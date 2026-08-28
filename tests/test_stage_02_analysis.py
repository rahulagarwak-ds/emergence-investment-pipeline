"""Stage 02 checks with the OpenAI boundary fully mocked."""

import json
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

from investment_pipeline.shared.config import PipelineConfig
from investment_pipeline.shared.errors import ErrorCode
from investment_pipeline.shared.openai_client import StructuredOpenAIClient
from investment_pipeline.shared.schemas import (
    CitedFindingV1,
    DimensionScoreV1,
    ThesisDimension,
)
from investment_pipeline.stage_01_sourcing import SourcingSelectorV1, run_sourcing
from investment_pipeline.stage_02_analysis import run_analysis
from investment_pipeline.stage_02_analysis.analysis import AnalysisDraftV1, EvidenceDraftV1

_FIXTURE = Path(__file__).parent / "fixtures" / "yc_snapshot.jsonl"


class FakeResponses:
    def __init__(self) -> None:
        self.attempts: defaultdict[str, int] = defaultdict(int)
        self.instructions: list[str] = []

    def parse(self, **request: Any) -> Any:
        assert request["model"] == "test-model"
        assert request["tools"] == [{"type": "web_search"}]
        assert request["include"] == ["web_search_call.action.sources"]
        assert request["store"] is False
        candidate = json.loads(request["input"])
        candidate_id = candidate["candidate_id"]
        self.attempts[candidate_id] += 1
        self.instructions.append(request["instructions"])

        unsupported = candidate_id == "example-02" or (
            candidate_id == "example-01" and self.attempts[candidate_id] == 1
        )
        external = candidate_id == "example-04"
        own_website = candidate_id == "example-05"
        source_url = (
            "https://unsupported.test/evidence"
            if unsupported
            else "https://public.test/evidence"
            if external
            else "https://docs.example-05.test/pricing?utm_source=x"
            if own_website
            else "https://example-06.test/gone"  # answers 404: rejected even after repair
            if candidate_id == "example-06"
            else "https://example-07.test/blocked"  # answers 403: kept, but unverified
            if candidate_id == "example-07"
            else "https://example-08.test/ratelimited"  # answers 429: kept, but unverified
            if candidate_id == "example-08"
            else candidate["source"]["source_url"]
        )
        missing_founder_score = candidate_id == "example-03"
        evidence_ids = ["e1"]
        scores = [
            DimensionScoreV1(
                dimension=dimension,
                score=None
                if missing_founder_score
                and dimension is ThesisDimension.FOUNDER_EXECUTION_FIT
                else 1,
                evidence_ids=[]
                if missing_founder_score and dimension is ThesisDimension.FOUNDER_EXECUTION_FIT
                else evidence_ids,
            )
            for dimension in ThesisDimension
        ]
        draft = AnalysisDraftV1(
            team=[CitedFindingV1(text="Self-reported team evidence", evidence_ids=evidence_ids)],
            product=[
                CitedFindingV1(
                    text="Self-reported product evidence",
                    evidence_ids=evidence_ids,
                )
            ],
            market=[],
            risks=[],
            open_questions=["What is independently verified?"],
            unknowns=["Independent traction verification"],
            evidence=[
                EvidenceDraftV1(
                    evidence_id="e1",
                    claim="YC profile claim",
                    source_url=source_url,
                    observed_at=None,
                    self_reported=not external,
                )
            ],
            dimension_scores=scores,
            critical_risks=[],
        )
        return SimpleNamespace(
            id=f"resp-{candidate_id}-{self.attempts[candidate_id]}",
            model="test-model",
            status="completed",
            usage=SimpleNamespace(input_tokens=10, output_tokens=5, total_tokens=15),
            output=[
                SimpleNamespace(
                    type="web_search_call",
                    action=SimpleNamespace(
                        sources=[SimpleNamespace(url="https://public.test/evidence")]
                    ),
                )
            ]
            if external
            else [],
            output_parsed=draft,
        )


def test_analysis_repairs_once_preserves_failure_and_calculates_scores(tmp_path: Path) -> None:
    candidate_set = run_sourcing(_FIXTURE, tmp_path / "01_sourcing")
    responses = FakeResponses()
    client = StructuredOpenAIClient(
        PipelineConfig(openai_model="test-model", _env_file=None),
        client=SimpleNamespace(responses=responses),
    )

    checked: list[str] = []

    def check_url(url: str) -> int | None:
        checked.append(url)
        return {"/gone": 404, "/blocked": 403, "/ratelimited": 429}.get(url[url.rfind("/") :], 200)

    result = run_analysis(candidate_set, tmp_path / "02_analysis", client, check_url=check_url)

    assert len(result.analyses) == 8
    assert [error.candidate_id for error in result.errors] == ["example-02", "example-06"]
    assert result.errors[0].code is ErrorCode.INVALID_MODEL_OUTPUT
    assert result.errors[0].details["total_tokens"] == 15
    assert "link returned 404" in str(result.errors[1].details["reason"])
    assert responses.attempts["example-01"] == 2
    assert responses.attempts["example-02"] == 2
    assert responses.attempts["example-06"] == 2
    assert "REPAIR:" in responses.instructions[1]
    assert checked.count("https://example-06.test/gone") == 1  # cached across the repair

    complete = next(item for item in result.analyses if item.candidate_id == "example-01")
    assert complete.total_score == 5
    assert complete.evidence_coverage == 100
    assert complete.response.usage.total_tokens == 15
    assert complete.evidence[0].http_status == 200
    assert complete.evidence[0].verified_at is not None
    assert complete.evidence[0].verified is True
    blocked = next(item for item in result.analyses if item.candidate_id == "example-07")
    assert blocked.evidence[0].http_status == 403
    assert blocked.evidence[0].verified is False
    limited = next(item for item in result.analyses if item.candidate_id == "example-08")
    assert limited.evidence[0].http_status == 429
    assert limited.evidence[0].verified is False

    incomplete = next(item for item in result.analyses if item.candidate_id == "example-03")
    assert incomplete.total_score == 4
    assert incomplete.evidence_coverage == 80
    external = next(item for item in result.analyses if item.candidate_id == "example-04")
    assert str(external.response.source_urls[0]) == "https://public.test/evidence"
    own_site = next(item for item in result.analyses if item.candidate_id == "example-05")
    assert str(own_site.evidence[0].source_url) == "https://docs.example-05.test/pricing?utm_source=x"
    assert own_site.evidence[0].self_reported is True
    assert "rejected because: unsupported evidence URL" in responses.instructions[1]

    analyses_path = tmp_path / "02_analysis" / "analyses.jsonl"
    lines = [json.loads(line) for line in analyses_path.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 10
    assert {line["record_type"] for line in lines} == {"analysis", "error"}
    assert all(request_instruction for request_instruction in responses.instructions)


def test_model_facing_schemas_avoid_unsupported_json_schema_formats() -> None:
    """OpenAI strict structured outputs reject ``format: uri``; keep URLs as strings in drafts."""
    from investment_pipeline.stage_03_recommendation.recommendation import MemoDraftV1

    for draft in (AnalysisDraftV1, MemoDraftV1):
        assert '"uri"' not in json.dumps(draft.model_json_schema()), draft.__name__
    with pytest.raises(ValidationError):
        EvidenceDraftV1(
            evidence_id="https://example.test/page",
            claim="ids must be short tokens, not URLs",
            source_url="https://example.test/page",
            observed_at=None,
            self_reported=True,
        )


def test_analysis_stops_on_insufficient_stage_01_artifact(tmp_path: Path) -> None:
    candidate_set = run_sourcing(
        _FIXTURE,
        tmp_path / "01_sourcing",
        SourcingSelectorV1(yc_batch="Winter 2025"),
    )
    responses = FakeResponses()
    client = StructuredOpenAIClient(
        PipelineConfig(openai_model="test-model", _env_file=None),
        client=SimpleNamespace(responses=responses),
    )

    result = run_analysis(candidate_set, tmp_path / "02_analysis", client)

    assert result.analyses == []
    assert result.errors[0].code is ErrorCode.INVALID_ARTIFACT
    assert responses.attempts == {}
