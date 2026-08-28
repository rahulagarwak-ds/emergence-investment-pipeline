"""Orchestration checks: run storage, replay, failure preservation, and live progress."""

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from conftest import FIXTURE, RunPipeline

from investment_pipeline import stage_01_sourcing
from investment_pipeline.cli import _parser, main
from investment_pipeline.shared import run_store
from investment_pipeline.shared.config import PipelineConfig
from investment_pipeline.shared.errors import ErrorCode
from investment_pipeline.shared.openai_client import StructuredOpenAIClient
from investment_pipeline.shared.run_store import create_run_dir
from investment_pipeline.shared.schemas import RunInputV1, RunManifestV1, StageStatus


def test_fresh_run_persists_manifest_logs_and_artifacts(
    run: RunPipeline, capsys: pytest.CaptureFixture[str]
) -> None:
    result = run()

    assert result.exit_code == 0
    manifest, run_dir = result.manifest, result.run_dir
    assert manifest.status is StageStatus.COMPLETED
    assert [stage.status for stage in manifest.stages.values()] == [StageStatus.COMPLETED] * 3
    assert manifest.input.snapshot_sha256 == sha256(FIXTURE.read_bytes()).hexdigest()
    assert manifest.input.snapshot_captured_at is not None
    assert manifest.versions["model"] == "test-model"
    assert manifest.versions["analysis_prompt"].startswith("analysis-v2@")
    assert manifest.versions["memo_prompt"].startswith("memo-v3@")
    assert manifest.stages["01_sourcing"].summary["eligible"] == 10
    assert manifest.stages["02_analysis"].summary == {"valid": 9, "failed": 1}
    assert manifest.stages["02_analysis"].usage is not None
    assert manifest.stages["02_analysis"].usage.total_tokens == 9 * 15
    assert len(manifest.stages["02_analysis"].response_ids) == 9
    assert manifest.stages["02_analysis"].errors[0].code is ErrorCode.INVALID_MODEL_OUTPUT
    assert manifest.stages["03_recommendation"].summary == {
        "memos": 8,
        "render_failed": 1,
        "meeting": 1,
        "watch": 4,
        "pass": 4,
    }
    assert len(manifest.source_urls) == 10
    _assert_paths_are_portable(manifest)

    artifact_paths = {
        artifact.path for stage in manifest.stages.values() for artifact in stage.artifacts
    }
    assert {
        "01_sourcing/candidates.json",
        "01_sourcing/source_refs.jsonl",
        "02_analysis/analyses.jsonl",
        "03_recommendation/index.md",
        "03_recommendation/recommendations.json",
        "03_recommendation/memos/example-01.md",
    } <= artifact_paths
    for stage in manifest.stages.values():
        for artifact in stage.artifacts:
            content = (run_dir / artifact.path).read_bytes()
            assert sha256(content).hexdigest() == artifact.sha256
            assert b"\r" not in content, "artifacts must hash identically on every OS"
    assert b"\r" not in (run_dir / "manifest.json").read_bytes()
    assert b"\r" not in (run_dir / "logs.jsonl").read_bytes()

    events = [event["event"] for event in _events(run_dir)]
    assert events[0] == "run_started"
    assert events[-1] == "run_finished"
    assert events.count("candidate_analyzed") == 10
    assert events.count("memo_rendered") == 9

    out = capsys.readouterr().out
    assert f"Run {run_dir.name}" in out
    assert "10 eligible · 1 incomplete · 4 rejected · saved candidates.json" in out
    assert "1/10 Example 01 · complete" in out
    assert "9/10 Example 09 · failed" in out
    assert "10/10 complete · 9 valid · 1 failed" in out
    assert "8 memos · 1 meeting · 4 watch · 4 pass" in out
    assert out.splitlines()[-1].startswith("Done")
    assert "Traceback" not in out
    assert "{" not in out


def test_replay_skips_completed_upstream_stages(run: RunPipeline) -> None:
    first = run()
    candidates = first.run_dir / "01_sourcing" / "candidates.json"

    second = run("--from-artifact", str(candidates))
    assert second.exit_code == 0
    assert second.run_dir != first.run_dir
    manifest = second.manifest
    assert manifest.status is StageStatus.COMPLETED
    assert manifest.stages["01_sourcing"].status is StageStatus.SKIPPED
    assert manifest.stages["02_analysis"].status is StageStatus.COMPLETED
    assert manifest.input.parent_artifact is not None
    assert manifest.input.parent_artifact.path == "candidates.json"
    assert manifest.input.parent_artifact.sha256 == sha256(candidates.read_bytes()).hexdigest()
    assert manifest.input.snapshot_path is None
    assert (second.run_dir / "01_sourcing" / "candidates.json").read_bytes() == (
        candidates.read_bytes()
    )
    assert (second.run_dir / "01_sourcing" / "source_refs.jsonl").is_file()
    assert second.responses.calls == {"analysis": 11, "memo": 10}
    _assert_paths_are_portable(manifest)

    third = run("--from-artifact", str(second.run_dir / "02_analysis" / "analyses.jsonl"))
    assert third.exit_code == 0
    assert third.manifest.stages["01_sourcing"].status is StageStatus.SKIPPED
    assert third.manifest.stages["02_analysis"].status is StageStatus.SKIPPED
    assert third.manifest.stages["03_recommendation"].status is StageStatus.COMPLETED
    assert third.manifest.stages["02_analysis"].summary == {"valid": 9, "failed": 1}
    assert third.responses.calls == {"memo": 10}
    assert len(list(first.run_dir.parent.iterdir())) == 3


def test_insufficient_candidates_fail_before_any_model_call(
    run: RunPipeline, capsys: pytest.CaptureFixture[str]
) -> None:
    result = run("--yc-batch", "Winter 2025")

    assert result.exit_code == 1
    manifest = result.manifest
    assert manifest.status is StageStatus.FAILED
    assert manifest.stages["01_sourcing"].status is StageStatus.FAILED
    assert manifest.stages["02_analysis"].status is StageStatus.PENDING
    assert manifest.stages["03_recommendation"].status is StageStatus.PENDING
    assert manifest.stages["01_sourcing"].errors[-1].code is ErrorCode.INSUFFICIENT_CANDIDATES
    assert (result.run_dir / "01_sourcing" / "candidates.json").is_file()
    assert not result.responses.calls
    out = capsys.readouterr().out
    assert "1 of 10 required candidates qualify" in out
    assert out.splitlines()[-1].startswith("Failed")


def test_missing_model_configuration_stops_with_actionable_message(
    run: RunPipeline, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    unconfigured = PipelineConfig(_env_file=None, output_dir=tmp_path / "outputs")

    result = run(client=StructuredOpenAIClient(unconfigured), settings=unconfigured)

    assert result.exit_code == 1
    manifest = result.manifest
    assert manifest.status is StageStatus.FAILED
    assert manifest.stages["01_sourcing"].status is StageStatus.COMPLETED
    assert manifest.stages["02_analysis"].status is StageStatus.FAILED
    assert manifest.stages["03_recommendation"].status is StageStatus.PENDING
    assert manifest.versions["model"] == "unset"
    assert "OPENAI_MODEL is required · set it in .env" in capsys.readouterr().out


def test_replayed_analyses_with_unconfigured_model_fail_in_stage_03(
    run: RunPipeline, tmp_path: Path
) -> None:
    first = run()
    unconfigured = PipelineConfig(_env_file=None, output_dir=tmp_path / "outputs")

    result = run(
        "--from-artifact",
        str(first.run_dir / "02_analysis" / "analyses.jsonl"),
        client=StructuredOpenAIClient(unconfigured),
        settings=unconfigured,
    )

    assert result.exit_code == 1
    assert result.manifest.stages["02_analysis"].status is StageStatus.SKIPPED
    assert result.manifest.stages["03_recommendation"].status is StageStatus.FAILED
    assert result.manifest.stages["03_recommendation"].errors[0].code is ErrorCode.INVALID_CONFIG
    assert (result.run_dir / "03_recommendation" / "index.md").is_file()


def test_invalid_replay_inputs_are_recorded_in_failed_runs(
    run: RunPipeline, tmp_path: Path
) -> None:
    missing = run("--from-artifact", str(tmp_path / "missing" / "candidates.json"))
    assert missing.exit_code == 1
    assert missing.manifest.status is StageStatus.FAILED
    assert missing.manifest.errors[0].code is ErrorCode.INVALID_INPUT
    assert all(stage.status is StageStatus.PENDING for stage in missing.manifest.stages.values())

    corrupt = tmp_path / "analyses.jsonl"
    corrupt.write_text('{"record_type": "analysis", "candidate_id": "x"}\n', encoding="utf-8")
    result = run("--from-artifact", str(corrupt))
    assert result.exit_code == 1
    assert result.manifest.errors[0].code is ErrorCode.INVALID_ARTIFACT
    assert result.manifest.input.parent_artifact is not None


def test_unexpected_errors_are_preserved_without_a_traceback_on_screen(
    run: RunPipeline, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def explode(*args: object, **kwargs: object) -> None:
        raise RuntimeError("disk vanished")

    monkeypatch.setattr(stage_01_sourcing, "run_sourcing", explode)

    result = run()

    assert result.exit_code == 1
    assert result.manifest.status is StageStatus.FAILED
    crash = next(event for event in _events(result.run_dir) if event["event"] == "run_crashed")
    assert crash["error"] == "RuntimeError"
    assert crash["message"] == "disk vanished"
    assert "_source" in {frame.split(":")[0] for frame in crash["frames"]}
    assert not any("/" in frame or "\\" in frame for frame in crash["frames"])
    out = capsys.readouterr().out
    assert "Traceback" not in out
    assert "RuntimeError · details in" in out


def test_run_directories_are_never_reused(tmp_path: Path) -> None:
    first, second = create_run_dir(tmp_path), create_run_dir(tmp_path)
    assert first != second
    assert first.is_dir() and second.is_dir()


def test_manifest_replace_retries_transient_windows_locks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime.now(UTC)
    manifest = RunManifestV1(
        run_id="run",
        status=StageStatus.RUNNING,
        created_at=now,
        updated_at=now,
        input=RunInputV1(selector="snapshot=all"),
        versions={},
        stages={},
    )
    original_replace = Path.replace
    denials = {"remaining": 2}

    def flaky_replace(self: Path, target: Path) -> Path:
        if denials["remaining"]:
            denials["remaining"] -= 1
            raise PermissionError(5, "Access is denied")
        return original_replace(self, target)

    monkeypatch.setattr(run_store, "sleep", lambda _seconds: None)
    monkeypatch.setattr(Path, "replace", flaky_replace)
    run_store.write_manifest(tmp_path, manifest)
    assert (tmp_path / "manifest.json").is_file()
    assert denials["remaining"] == 0

    denials["remaining"] = 99
    with pytest.raises(PermissionError):
        run_store.write_manifest(tmp_path, manifest)


def test_parser_accepts_one_selection_mode() -> None:
    parse = _parser().parse_args
    assert parse(["run", "--topic", "ai agents"]).topic == "ai agents"
    assert parse(["run", "--url", "https://a.test", "--url", "https://b.test"]).urls == [
        "https://a.test",
        "https://b.test",
    ]
    with pytest.raises(SystemExit):
        parse(["run", "--topic", "x", "--yc-batch", "y"])


def test_main_rejects_invalid_environment_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MAX_CANDIDATES", "50")

    with pytest.raises(SystemExit) as exit_info:
        main(["run"])

    assert exit_info.value.code == 2
    assert "invalid setting" in capsys.readouterr().out


def _events(run_dir: Path) -> list[dict[str, Any]]:
    lines = (run_dir / "logs.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]


def _assert_paths_are_portable(manifest: RunManifestV1) -> None:
    paths = [
        manifest.input.snapshot_path,
        manifest.input.parent_artifact.path if manifest.input.parent_artifact else None,
        *(artifact.path for stage in manifest.stages.values() for artifact in stage.artifacts),
    ]
    for path in filter(None, paths):
        assert not Path(path).is_absolute()
        assert ":" not in path
        assert "\\" not in path
