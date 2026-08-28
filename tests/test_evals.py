"""Eval graders and report over a mocked run."""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from conftest import RunPipeline

import evals.run as evals_run
from evals.graders import GRADERS, Finding, load_run
from evals.run import MemoJudgementV1
from investment_pipeline.shared.config import PipelineConfig
from investment_pipeline.shared.openai_client import StructuredOpenAIClient
from investment_pipeline.shared.schemas import Recommendation

_RENDER_FAILURE = Finding("memos", "example-08", "memo missing: render failed")


def test_clean_run_only_reports_the_recorded_render_failure(run: RunPipeline) -> None:
    result = run()
    assert _grade(result.run_dir) == [_RENDER_FAILURE]


def test_graders_flag_tampered_outputs(run: RunPipeline) -> None:
    result = run()
    memo = result.run_dir / "03_recommendation" / "memos" / "example-01.md"
    lines = memo.read_text(encoding="utf-8").splitlines()
    lines[2] = "**Recommendation: Pass**"
    lines.insert(lines.index("## Rationale") + 1, "- An uncited claim slipped in.")
    memo.write_text("\n".join(lines) + "\n", encoding="utf-8")

    recommendations = result.run_dir / "03_recommendation" / "recommendations.json"
    payload = json.loads(recommendations.read_text(encoding="utf-8"))
    payload["recommendations"][1]["recommendation"] = Recommendation.TAKE_A_MEETING.value
    recommendations.write_text(json.dumps(payload), encoding="utf-8")

    analyses = result.run_dir / "02_analysis" / "analyses.jsonl"
    records = analyses.read_text(encoding="utf-8").splitlines()
    first = json.loads(records[0])
    first["evidence"][0]["source_url"] = "https://elsewhere.test/claim"
    records[0] = json.dumps(first)
    analyses.write_text("\n".join(records) + "\n", encoding="utf-8")

    findings = _grade(result.run_dir)

    by_grader = {(finding.grader, finding.candidate_id) for finding in findings}
    assert ("grounding", first["candidate_id"]) in by_grader
    assert ("policy", "example-02") in by_grader
    assert ("memos", "example-02") in by_grader
    example_01 = [
        f.message for f in findings if (f.grader, f.candidate_id) == ("memos", "example-01")
    ]
    assert example_01 == [
        "recommendation line does not state the recorded recommendation",
        "uncited bullet under '## Rationale'",
    ]
    assert _RENDER_FAILURE in findings


def test_citations_grader_flags_unverified_links_and_skips_legacy_runs(run: RunPipeline) -> None:
    result = run()
    assert [f for f in _grade(result.run_dir) if f.grader == "citations"] == []

    analyses = result.run_dir / "02_analysis" / "analyses.jsonl"
    records = [json.loads(line) for line in analyses.read_text(encoding="utf-8").splitlines()]
    for record in records:
        if record.get("candidate_id") == "example-03" and record["record_type"] == "analysis":
            record["evidence"][0]["http_status"] = 403
    analyses.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    flagged = [f for f in _grade(result.run_dir) if f.grader == "citations"]
    assert flagged and all(f.candidate_id == "example-03" for f in flagged)
    assert "not verified evidence" in flagged[0].message

    for record in records:
        for item in record.get("evidence", []):
            item.pop("http_status", None)
            item.pop("verified_at", None)
    analyses.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    assert [f for f in _grade(result.run_dir) if f.grader == "citations"] == []


def test_report_is_keyed_by_model_and_prompt_hashes(
    run: RunPipeline,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run()
    monkeypatch.setattr(evals_run, "REPORTS", tmp_path / "reports")

    with pytest.raises(SystemExit) as exit_info:
        evals_run.main([str(result.run_dir)])

    assert exit_info.value.code == 1
    report = json.loads(
        (tmp_path / "reports" / f"{result.run_dir.name}.json").read_text(encoding="utf-8")
    )
    assert report["run_id"] == result.run_dir.name
    assert report["model"] == "test-model"
    assert report["analysis_prompt"] == result.manifest.versions["analysis_prompt"]
    assert report["memo_prompt"] == result.manifest.versions["memo_prompt"]
    assert report["deterministic"] == {
        "findings": [
            {
                "grader": "memos",
                "candidate_id": "example-08",
                "message": "memo missing: render failed",
            }
        ],
        "passed": False,
    }
    assert report["semantic"] is None
    out = capsys.readouterr().out
    assert "grounding     0 findings" in out
    assert "memos         1 finding" in out
    assert "citations     0 findings" in out
    assert "example-08: memo missing: render failed" in out


def test_semantic_judge_is_skipped_without_model_configuration(
    run: RunPipeline, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = run()
    monkeypatch.setattr(evals_run, "REPORTS", tmp_path / "reports")
    monkeypatch.chdir(tmp_path)
    for name in ("OPENAI_API_KEY", "OPENAI_MODEL"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(SystemExit):
        evals_run.main([str(result.run_dir), "--semantic"])

    report = json.loads(
        (tmp_path / "reports" / f"{result.run_dir.name}.json").read_text(encoding="utf-8")
    )
    assert report["semantic"] == {"skipped": "OPENAI_MODEL is required in .env"}


def test_semantic_judge_averages_ratings_and_keeps_per_memo_errors(run: RunPipeline) -> None:
    result = run()

    class JudgeResponses:
        def parse(self, **request: Any) -> Any:
            assert request["text_format"] is MemoJudgementV1
            assert "tools" not in request
            candidate_id = json.loads(request["input"])["analysis"]["candidate_id"]
            if candidate_id == "example-02":
                raise ValueError("judge returned prose")
            return SimpleNamespace(
                id=f"judge-{candidate_id}",
                model="test-model",
                status="completed",
                usage=SimpleNamespace(input_tokens=1, output_tokens=1, total_tokens=2),
                output=[],
                output_parsed=MemoJudgementV1(
                    thesis_adherence=4,
                    faithfulness=5,
                    clarity=3,
                    risk_quality=4,
                    specificity=2,
                    notes="Risks lean on self-reported claims.",
                ),
            )

    client = StructuredOpenAIClient(
        PipelineConfig(_env_file=None, openai_model="test-model"),
        client=SimpleNamespace(responses=JudgeResponses()),
    )

    semantic = evals_run.judge(load_run(result.run_dir), client)

    assert semantic["judge_prompt"] == f"judge-v1@{evals_run.JUDGE_PROMPT_HASH}"
    ratings = semantic["ratings"]
    assert isinstance(ratings, dict) and len(ratings) == 7
    assert semantic["errors"] == {
        "example-02": "OpenAI returned invalid structured output after one repair attempt"
    }
    assert semantic["averages"] == {
        "thesis_adherence": 4,
        "faithfulness": 5,
        "clarity": 3,
        "risk_quality": 4,
        "specificity": 2,
    }


def _grade(run_dir: Path) -> list[Finding]:
    graded = load_run(run_dir)
    return [finding for grader in GRADERS for finding in grader(graded)]
