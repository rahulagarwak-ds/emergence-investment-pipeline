"""Orchestration checks: run storage, replay, failure preservation, and live progress."""

import json
from argparse import Namespace
from collections import Counter
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from investment_pipeline.cli import _parser, run_pipeline
from investment_pipeline.shared.config import PipelineConfig
from investment_pipeline.shared.errors import ErrorCode
from investment_pipeline.shared.openai_client import StructuredOpenAIClient
from investment_pipeline.shared.run_store import create_run_dir
from investment_pipeline.shared.schemas import (
    CitedFindingV1,
    DimensionScoreV1,
    EvidenceItemV1,
    RunManifestV1,
    StageStatus,
    ThesisDimension,
)
from investment_pipeline.stage_02_analysis.analysis import AnalysisDraftV1
from investment_pipeline.stage_03_recommendation.recommendation import MemoDraftV1

_FIXTURE = Path(__file__).parent / "fixtures" / "yc_snapshot.jsonl"
_SCORES = {
    "example-01": (25, 25, 20, 15, 5),
    "example-02": (25, 25, 10, 0, 0),
    "example-03": (25, 25, 10, 0, 0),
    "example-04": (25, 25, 10, 0, 0),
    "example-05": (25, 25, 10, 0, 0),
}


class FakeResponses:
    """Answer Stage 02 and Stage 03 requests; example-09 analysis and example-08 memo fail."""

    def __init__(self) -> None:
        self.calls: Counter[str] = Counter()

    def parse(self, **request: Any) -> Any:
        assert request["store"] is False
        payload = json.loads(request["input"])
        draft: AnalysisDraftV1 | MemoDraftV1
        if request["text_format"] is AnalysisDraftV1:
            self.calls["analysis"] += 1
            draft = _analysis_draft(payload)
        else:
            self.calls["memo"] += 1
            draft = _memo_draft(payload["analysis"]["candidate_id"])
        return SimpleNamespace(
            id=f"resp-{self.calls.total()}",
            model="test-model",
            status="completed",
            usage=SimpleNamespace(input_tokens=10, output_tokens=5, total_tokens=15),
            output=[],
            output_parsed=draft,
        )


def test_fresh_run_persists_manifest_logs_and_artifacts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config, responses = _config(tmp_path), FakeResponses()

    exit_code = run_pipeline(_args("--snapshot", str(_FIXTURE)), config, _client(config, responses))

    assert exit_code == 0
    run_dir = _latest_run(config.output_dir)
    manifest = _manifest(run_dir)
    assert manifest.status is StageStatus.COMPLETED
    assert [stage.status for stage in manifest.stages.values()] == [StageStatus.COMPLETED] * 3
    assert manifest.input.snapshot_sha256 == sha256(_FIXTURE.read_bytes()).hexdigest()
    assert manifest.input.snapshot_captured_at is not None
    assert manifest.versions["model"] == "test-model"
    assert manifest.versions["analysis_prompt"].startswith("analysis-v1@")
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
            assert sha256((run_dir / artifact.path).read_bytes()).hexdigest() == artifact.sha256

    events = [
        json.loads(line)["event"]
        for line in (run_dir / "logs.jsonl").read_text(encoding="utf-8").splitlines()
    ]
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


def test_replay_skips_completed_upstream_stages(tmp_path: Path) -> None:
    config = _config(tmp_path)
    assert run_pipeline(_args("--snapshot", str(_FIXTURE)), config, _client(config)) == 0
    first_run = _latest_run(config.output_dir)
    candidates = first_run / "01_sourcing" / "candidates.json"

    responses = FakeResponses()
    exit_code = run_pipeline(
        _args("--from-artifact", str(candidates)), config, _client(config, responses)
    )
    assert exit_code == 0
    second_run = _latest_run(config.output_dir)
    manifest = _manifest(second_run)
    assert second_run != first_run
    assert manifest.status is StageStatus.COMPLETED
    assert manifest.stages["01_sourcing"].status is StageStatus.SKIPPED
    assert manifest.stages["02_analysis"].status is StageStatus.COMPLETED
    assert manifest.input.parent_artifact is not None
    assert manifest.input.parent_artifact.path == "candidates.json"
    assert manifest.input.parent_artifact.sha256 == sha256(candidates.read_bytes()).hexdigest()
    assert manifest.input.snapshot_path is None
    assert (second_run / "01_sourcing" / "candidates.json").read_bytes() == candidates.read_bytes()
    assert (second_run / "01_sourcing" / "source_refs.jsonl").is_file()
    assert responses.calls == {"analysis": 11, "memo": 10}
    _assert_paths_are_portable(manifest)

    responses = FakeResponses()
    analyses = second_run / "02_analysis" / "analyses.jsonl"
    exit_code = run_pipeline(
        _args("--from-artifact", str(analyses)), config, _client(config, responses)
    )
    assert exit_code == 0
    third = _manifest(_latest_run(config.output_dir))
    assert third.stages["01_sourcing"].status is StageStatus.SKIPPED
    assert third.stages["02_analysis"].status is StageStatus.SKIPPED
    assert third.stages["03_recommendation"].status is StageStatus.COMPLETED
    assert third.stages["02_analysis"].summary == {"valid": 9, "failed": 1}
    assert responses.calls == {"memo": 10}
    assert len(list(config.output_dir.iterdir())) == 3


def test_insufficient_candidates_fail_before_any_model_call(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config, responses = _config(tmp_path), FakeResponses()

    exit_code = run_pipeline(
        _args("--snapshot", str(_FIXTURE), "--yc-batch", "Winter 2025"),
        config,
        _client(config, responses),
    )

    assert exit_code == 1
    run_dir = _latest_run(config.output_dir)
    manifest = _manifest(run_dir)
    assert manifest.status is StageStatus.FAILED
    assert manifest.stages["01_sourcing"].status is StageStatus.FAILED
    assert manifest.stages["02_analysis"].status is StageStatus.PENDING
    assert manifest.stages["03_recommendation"].status is StageStatus.PENDING
    assert manifest.stages["01_sourcing"].errors[-1].code is ErrorCode.INSUFFICIENT_CANDIDATES
    assert (run_dir / "01_sourcing" / "candidates.json").is_file()
    assert not responses.calls
    out = capsys.readouterr().out
    assert "1 of 10 required candidates qualify" in out
    assert out.splitlines()[-1].startswith("Failed")


def test_missing_model_configuration_stops_with_actionable_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = PipelineConfig(_env_file=None, output_dir=tmp_path / "outputs")

    exit_code = run_pipeline(
        _args("--snapshot", str(_FIXTURE)), config, StructuredOpenAIClient(config)
    )

    assert exit_code == 1
    manifest = _manifest(_latest_run(config.output_dir))
    assert manifest.status is StageStatus.FAILED
    assert manifest.stages["01_sourcing"].status is StageStatus.COMPLETED
    assert manifest.stages["02_analysis"].status is StageStatus.FAILED
    assert manifest.stages["03_recommendation"].status is StageStatus.PENDING
    assert manifest.versions["model"] == "unset"
    assert "OPENAI_MODEL is required · set it in .env" in capsys.readouterr().out


def test_invalid_replay_input_is_recorded_in_a_failed_run(tmp_path: Path) -> None:
    config = _config(tmp_path)

    exit_code = run_pipeline(
        _args("--from-artifact", str(tmp_path / "missing" / "candidates.json")),
        config,
        _client(config),
    )

    assert exit_code == 1
    manifest = _manifest(_latest_run(config.output_dir))
    assert manifest.status is StageStatus.FAILED
    assert manifest.errors[0].code is ErrorCode.INVALID_INPUT
    assert all(stage.status is StageStatus.PENDING for stage in manifest.stages.values())


def test_run_directories_are_never_reused(tmp_path: Path) -> None:
    first, second = create_run_dir(tmp_path), create_run_dir(tmp_path)
    assert first != second
    assert first.is_dir() and second.is_dir()


def test_parser_accepts_one_selection_mode() -> None:
    assert _args("--topic", "ai agents").topic == "ai agents"
    assert _args("--url", "https://a.test", "--url", "https://b.test").urls == [
        "https://a.test",
        "https://b.test",
    ]
    with pytest.raises(SystemExit):
        _args("--topic", "x", "--yc-batch", "y")


def _analysis_draft(candidate: dict[str, Any]) -> AnalysisDraftV1:
    candidate_id = candidate["candidate_id"]
    points = _SCORES.get(candidate_id, (10, 10, 5, 0, 0))
    source_url = (
        "https://unsupported.test/evidence"
        if candidate_id == "example-09"
        else candidate["source"]["source_url"]
    )
    return AnalysisDraftV1(
        team=[CitedFindingV1(text="Self-reported team evidence", evidence_ids=["e1"])],
        product=[CitedFindingV1(text="Self-reported product evidence", evidence_ids=["e1"])],
        market=[],
        risks=[],
        open_questions=["What is independently verified?"],
        unknowns=["Independent traction verification"],
        evidence=[
            EvidenceItemV1(
                evidence_id="e1",
                claim="YC profile claim",
                source_url=source_url,
                observed_at=None,
                self_reported=True,
            )
        ],
        dimension_scores=[
            DimensionScoreV1(dimension=dimension, score=score, evidence_ids=["e1"])
            for dimension, score in zip(ThesisDimension, points, strict=True)
        ],
        critical_risks=[],
    )


def _memo_draft(candidate_id: str) -> MemoDraftV1:
    evidence_id = "missing" if candidate_id == "example-08" else "e1"
    return MemoDraftV1(
        rationale=[CitedFindingV1(text="Evidence supports the call.", evidence_ids=[evidence_id])],
        key_risks=[CitedFindingV1(text="Evidence is self-reported.", evidence_ids=[evidence_id])],
        decision_changes=["Can adoption be verified?", "Does usage expand to a team?"],
    )


def _args(*extra: str) -> Namespace:
    return _parser().parse_args(["run", *extra])


def _config(tmp_path: Path) -> PipelineConfig:
    return PipelineConfig(
        _env_file=None, openai_model="test-model", output_dir=tmp_path / "outputs"
    )


def _client(
    config: PipelineConfig, responses: FakeResponses | None = None
) -> StructuredOpenAIClient:
    return StructuredOpenAIClient(
        config, client=SimpleNamespace(responses=responses or FakeResponses())
    )


def _latest_run(output_dir: Path) -> Path:
    return max(output_dir.iterdir())


def _manifest(run_dir: Path) -> RunManifestV1:
    return RunManifestV1.model_validate_json(
        (run_dir / "manifest.json").read_text(encoding="utf-8")
    )


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
