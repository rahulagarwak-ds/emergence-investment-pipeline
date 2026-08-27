"""Stage 03 policy and constrained memo checks with OpenAI fully mocked."""

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from investment_pipeline.shared.config import PipelineConfig
from investment_pipeline.shared.errors import ErrorCode
from investment_pipeline.shared.openai_client import StructuredOpenAIClient
from investment_pipeline.shared.schemas import (
    THESIS_WEIGHTS,
    AnalysisRecordV1,
    AnalysisSetV1,
    CitedFindingV1,
    CriticalRisk,
    CriticalRiskFindingV1,
    DimensionScoreV1,
    EvidenceItemV1,
    OpenAIResponseMetadataV1,
    Recommendation,
    ThesisDimension,
    TokenUsageV1,
)
from investment_pipeline.stage_03_recommendation import run_recommendation
from investment_pipeline.stage_03_recommendation.recommendation import (
    MEMO_MAX_WORDS,
    MemoDraftV1,
    _recommendation,
)


class FakeResponses:
    def __init__(self) -> None:
        self.attempts: defaultdict[str, int] = defaultdict(int)

    def parse(self, **request: Any) -> Any:
        assert "tools" not in request
        assert "include" not in request
        assert request["store"] is False
        payload = json.loads(request["input"])
        analysis = payload["analysis"]
        candidate_id = analysis["candidate_id"]
        self.attempts[candidate_id] += 1
        evidence_id = "missing" if candidate_id == "company-02" else "e1"
        draft = MemoDraftV1(
            rationale=[
                CitedFindingV1(
                    text="The validated evidence supports the fixed recommendation.",
                    evidence_ids=[evidence_id],
                )
            ],
            key_risks=[
                CitedFindingV1(
                    text="The available evidence is self-reported.",
                    evidence_ids=[evidence_id],
                )
            ],
            decision_changes=[
                "Can adoption be independently verified?",
                "Does usage expand from one employee to a team?",
            ],
        )
        return SimpleNamespace(
            id=f"resp-{candidate_id}-{self.attempts[candidate_id]}",
            model="test-model",
            status="completed",
            usage=SimpleNamespace(input_tokens=10, output_tokens=5, total_tokens=15),
            output=[],
            output_parsed=draft,
        )


def test_policy_memos_failures_and_ranked_index(tmp_path: Path) -> None:
    analyses = [
        _analysis("company-01", 90),
        _analysis("company-02", 80),
        _analysis("company-03", 79, critical_risk=True),
        _analysis("company-04", 60),
        _analysis("company-05", 54),
        *(_analysis(f"company-{number:02}", 10) for number in range(6, 12)),
    ]
    responses = FakeResponses()
    client = StructuredOpenAIClient(
        PipelineConfig(openai_model="test-model", _env_file=None),
        client=SimpleNamespace(responses=responses),
    )

    result = run_recommendation(
        AnalysisSetV1(created_at=datetime.now(UTC), analyses=analyses),
        tmp_path,
        client,
    )

    by_id = {record.candidate_id: record for record in result.recommendations}
    assert by_id["company-01"].recommendation is Recommendation.TAKE_A_MEETING
    assert by_id["company-02"].recommendation is Recommendation.TAKE_A_MEETING
    assert by_id["company-03"].recommendation is Recommendation.PASS
    assert by_id["company-04"].recommendation is Recommendation.WATCH
    assert by_id["company-05"].recommendation is Recommendation.PASS
    assert by_id["company-02"].memo_path is None
    assert result.errors[0].code is ErrorCode.INVALID_MODEL_OUTPUT
    assert responses.attempts["company-02"] == 2
    assert len(list((tmp_path / "memos").glob("*.md"))) == 10

    memo = (tmp_path / "memos" / "company-01.md").read_text(encoding="utf-8")
    assert memo.splitlines()[-1] == "**Recommendation: Take a meeting**"
    assert "[e1 · self-reported](<https://evidence.test/company-01>)" in memo
    assert len(memo.split()) <= MEMO_MAX_WORDS

    index = (tmp_path / "index.md").read_text(encoding="utf-8")
    assert "| 1 | Company 01 | 90 | 100% | Take a meeting |" in index
    assert "| 2 | Company 02 | 80 | 100% | Take a meeting | render failed |" in index

    assert _recommendation(_analysis("risky", 90, critical_risk=True), 1, 1) is Recommendation.PASS
    assert _recommendation(_analysis("second", 85), 2, 1) is Recommendation.WATCH


def _analysis(
    candidate_id: str,
    total_score: int,
    *,
    critical_risk: bool = False,
) -> AnalysisRecordV1:
    remaining = total_score
    scores: list[DimensionScoreV1] = []
    for dimension in ThesisDimension:
        score = min(THESIS_WEIGHTS[dimension], remaining)
        remaining -= score
        scores.append(
            DimensionScoreV1(
                dimension=dimension,
                score=score,
                evidence_ids=["e1"],
            )
        )
    assert remaining == 0
    return AnalysisRecordV1(
        candidate_id=candidate_id,
        candidate_name=candidate_id.replace("-", " ").title(),
        prompt_version="analysis-v1",
        prompt_hash="0" * 64,
        response=OpenAIResponseMetadataV1(
            response_id=f"analysis-{candidate_id}",
            model="test-model",
            latency_ms=1,
            usage=TokenUsageV1(input_tokens=1, output_tokens=1, total_tokens=2),
            source_urls=[],
        ),
        team=[CitedFindingV1(text="Team evidence", evidence_ids=["e1"])],
        product=[CitedFindingV1(text="Product evidence", evidence_ids=["e1"])],
        market=[],
        risks=[],
        open_questions=[],
        unknowns=[],
        evidence=[
            EvidenceItemV1(
                evidence_id="e1",
                claim="Public evidence",
                source_url=f"https://evidence.test/{candidate_id}",
                observed_at=None,
                self_reported=True,
            )
        ],
        dimension_scores=scores,
        total_score=total_score,
        evidence_coverage=100,
        critical_risks=[
            CriticalRiskFindingV1(
                risk=CriticalRisk.SECURITY_OR_COMPLIANCE_BLOCKER,
                evidence_ids=["e1"],
            )
        ]
        if critical_risk
        else [],
    )
