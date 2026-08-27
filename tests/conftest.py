"""Shared fixtures that drive the full pipeline with OpenAI mocked."""

import json
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any, NamedTuple

import pytest

from investment_pipeline.cli import _parser, run_pipeline
from investment_pipeline.shared.config import PipelineConfig
from investment_pipeline.shared.openai_client import StructuredOpenAIClient
from investment_pipeline.shared.schemas import (
    CitedFindingV1,
    DimensionScoreV1,
    EvidenceItemV1,
    RunManifestV1,
    ThesisDimension,
)
from investment_pipeline.stage_02_analysis.analysis import AnalysisDraftV1
from investment_pipeline.stage_03_recommendation.recommendation import MemoDraftV1

FIXTURE = Path(__file__).parent / "fixtures" / "yc_snapshot.jsonl"
_SCORES = {
    "example-01": (25, 25, 20, 15, 5),
    "example-02": (25, 25, 10, 0, 0),
    "example-03": (25, 25, 10, 0, 0),
    "example-04": (25, 25, 10, 0, 0),
    "example-05": (25, 25, 10, 0, 0),
}


class FakeResponses:
    """Answer Stage 02 and Stage 03 requests deterministically from the request payload.

    example-09's analysis cites an unsupported URL and fails after the repair attempt; example-08's
    memo cites an unknown evidence id and fails to render; founder scores stay null whenever the
    candidate record lists no founders.
    """

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


class RunResult(NamedTuple):
    exit_code: int
    run_dir: Path
    manifest: RunManifestV1
    responses: FakeResponses


RunPipeline = Callable[..., RunResult]


@pytest.fixture
def config(tmp_path: Path) -> PipelineConfig:
    return PipelineConfig(
        _env_file=None, openai_model="test-model", output_dir=tmp_path / "outputs"
    )


@pytest.fixture
def run(config: PipelineConfig) -> RunPipeline:
    """Run the CLI against the fixture snapshot with a fresh fake per call."""

    def _run(
        *cli_args: str,
        client: StructuredOpenAIClient | None = None,
        settings: PipelineConfig = config,
    ) -> RunResult:
        if not {"--snapshot", "--from-artifact"} & set(cli_args):
            cli_args = ("--snapshot", str(FIXTURE), *cli_args)
        responses = FakeResponses()
        client = client or StructuredOpenAIClient(
            settings, client=SimpleNamespace(responses=responses)
        )
        exit_code = run_pipeline(_parser().parse_args(["run", *cli_args]), settings, client)
        run_dir = max(settings.output_dir.iterdir())
        manifest = RunManifestV1.model_validate_json(
            (run_dir / "manifest.json").read_text(encoding="utf-8")
        )
        return RunResult(exit_code, run_dir, manifest, responses)

    return _run


def _analysis_draft(candidate: dict[str, Any]) -> AnalysisDraftV1:
    candidate_id = candidate["candidate_id"]
    points = _SCORES.get(candidate_id, (10, 10, 5, 0, 0))
    source_url = (
        "https://unsupported.test/evidence"
        if candidate_id == "example-09"
        else candidate["source"]["source_url"]
    )
    scores = []
    for dimension, score in zip(ThesisDimension, points, strict=True):
        unknown = dimension is ThesisDimension.FOUNDER_EXECUTION_FIT and not candidate["founders"]
        scores.append(
            DimensionScoreV1(
                dimension=dimension,
                score=None if unknown else score,
                evidence_ids=[] if unknown else ["e1"],
            )
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
        dimension_scores=scores,
        critical_risks=[],
    )


def _memo_draft(candidate_id: str) -> MemoDraftV1:
    evidence_id = "missing" if candidate_id == "example-08" else "e1"
    return MemoDraftV1(
        rationale=[CitedFindingV1(text="Evidence supports the call.", evidence_ids=[evidence_id])],
        key_risks=[CitedFindingV1(text="Evidence is self-reported.", evidence_ids=[evidence_id])],
        decision_changes=["Can adoption be verified?", "Does usage expand to a team?"],
    )
