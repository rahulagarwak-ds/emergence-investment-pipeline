"""Deterministic ranking, recommendation policy, and constrained memo rendering."""

import json
from collections.abc import Callable
from datetime import UTC, datetime
from functools import partial
from hashlib import sha256
from pathlib import Path

from pydantic import Field

from investment_pipeline.shared.errors import ErrorCode, ErrorRecordV1
from investment_pipeline.shared.openai_client import StructuredOpenAIClient
from investment_pipeline.shared.schemas import (
    THESIS_WEIGHTS,
    AnalysisRecordV1,
    AnalysisSetV1,
    CitedFindingV1,
    ContractModel,
    DimensionScoreV1,
    EvidenceItemV1,
    OpenAIResponseMetadataV1,
    Recommendation,
    RecommendationRecordV1,
    RecommendationSetV1,
)

# memo-v3: call in the header, pillar table (each pillar out of 100) above the rationale,
# verified citations only.
PROMPT_VERSION = "memo-v3"
MEMO_MAX_WORDS = 350
_PROMPT = Path(__file__).with_name("prompt_v2.md").read_text(encoding="utf-8")
PROMPT_HASH = sha256(_PROMPT.encode()).hexdigest()
_STAGE = "stage_03_recommendation"


class MemoDraftV1(ContractModel):
    """Model-owned memo language before deterministic Markdown rendering."""

    rationale: list[CitedFindingV1] = Field(min_length=1, max_length=3)
    key_risks: list[CitedFindingV1] = Field(min_length=1, max_length=3)
    decision_changes: list[str] = Field(min_length=2, max_length=3)


def run_recommendation(
    analysis_set: AnalysisSetV1,
    output_dir: Path,
    client: StructuredOpenAIClient,
    on_candidate: Callable[[int, int, str, str], None] | None = None,
) -> RecommendationSetV1:
    """Rank analyses, assign deterministic calls, and write constrained memos.

    ``on_candidate`` receives ``(rank, total, candidate_name, call | "render failed")``.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "memos").mkdir(exist_ok=True)
    analyses = sorted(
        analysis_set.analyses,
        key=lambda analysis: (-analysis.total_score, analysis.candidate_id),
    )
    meeting_slots = (len(analyses) + 9) // 10
    recommendations: list[RecommendationRecordV1] = []
    errors: list[ErrorRecordV1] = []
    rendering_enabled = True

    for rank, analysis in enumerate(analyses, start=1):
        recommendation = assign_recommendation(analysis, rank, meeting_slots)
        metadata: OpenAIResponseMetadataV1 | None = None
        memo_path: str | None = None

        if rendering_enabled:
            response = client.parse(
                instructions=_PROMPT,
                input_text=json.dumps(
                    {
                        "fixed_recommendation": recommendation.value,
                        "verified_evidence_ids": [
                            item.evidence_id for item in analysis.evidence if item.verified
                        ],
                        "analysis": analysis.model_dump(mode="json", exclude={"response"}),
                    },
                    indent=2,
                ),
                output_type=MemoDraftV1,
                stage=_STAGE,
                candidate_id=analysis.candidate_id,
                validate=partial(_validate_draft, analysis, recommendation),
            )
            if response.error is not None:
                errors.append(response.error)
                rendering_enabled = response.error.code is not ErrorCode.INVALID_CONFIG
            elif response.parsed is None or response.metadata is None:
                errors.append(
                    ErrorRecordV1(
                        code=ErrorCode.MEMO_RENDER_FAILED,
                        message="OpenAI response was missing memo content or metadata",
                        stage=_STAGE,
                        candidate_id=analysis.candidate_id,
                    )
                )
            else:
                try:
                    memo = _render_memo(analysis, recommendation, response.parsed)
                    rendered_path = f"memos/{analysis.candidate_id}.md"
                    (output_dir / rendered_path).write_text(memo, encoding="utf-8", newline="\n")
                    memo_path = rendered_path
                    metadata = response.metadata
                except OSError as exc:
                    errors.append(
                        ErrorRecordV1(
                            code=ErrorCode.MEMO_RENDER_FAILED,
                            message=f"Could not render memo: {type(exc).__name__}",
                            stage=_STAGE,
                            candidate_id=analysis.candidate_id,
                        )
                    )

        recommendations.append(
            RecommendationRecordV1(
                candidate_id=analysis.candidate_id,
                candidate_name=analysis.candidate_name,
                rank=rank,
                total_score=analysis.total_score,
                evidence_coverage=analysis.evidence_coverage,
                critical_risks=[risk.risk for risk in analysis.critical_risks],
                recommendation=recommendation,
                prompt_version=PROMPT_VERSION,
                prompt_hash=PROMPT_HASH,
                response=metadata,
                memo_path=memo_path,
            )
        )
        if on_candidate is not None:
            on_candidate(
                rank,
                len(analyses),
                analysis.candidate_name,
                recommendation.value if memo_path else "render failed",
            )

    result = RecommendationSetV1(
        created_at=datetime.now(UTC),
        recommendations=recommendations,
        errors=errors,
    )
    (output_dir / "index.md").write_text(_render_index(result), encoding="utf-8", newline="\n")
    (output_dir / "recommendations.json").write_text(
        result.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return result


def assign_recommendation(
    analysis: AnalysisRecordV1,
    rank: int,
    meeting_slots: int,
) -> Recommendation:
    """Apply the documented gates: top decile, score, evidence coverage, critical risks."""
    has_critical_risk = bool(analysis.critical_risks)
    if (
        rank <= meeting_slots
        and analysis.total_score >= 75
        and analysis.evidence_coverage >= 80
        and not has_critical_risk
    ):
        return Recommendation.TAKE_A_MEETING
    if analysis.total_score >= 55 and not has_critical_risk:
        return Recommendation.WATCH
    return Recommendation.PASS


def _validate_draft(
    analysis: AnalysisRecordV1,
    recommendation: Recommendation,
    draft: MemoDraftV1,
    _metadata: OpenAIResponseMetadataV1,
) -> None:
    evidence_ids = {item.evidence_id for item in analysis.evidence}
    verified_ids = {item.evidence_id for item in analysis.evidence if item.verified}
    referenced_ids = {
        evidence_id
        for point in (*draft.rationale, *draft.key_risks)
        for evidence_id in point.evidence_ids
    }
    if unknown_ids := referenced_ids - evidence_ids:
        raise ValueError(f"memo references unknown evidence ids: {sorted(unknown_ids)}")
    if unverified_ids := referenced_ids - verified_ids:
        raise ValueError(
            f"memo cites evidence whose link is not verified: {sorted(unverified_ids)} "
            f"(use only verified_evidence_ids)"
        )

    text = [
        *(point.text for point in (*draft.rationale, *draft.key_risks)),
        *draft.decision_changes,
    ]
    if any(
        "\n" in item
        or "http://" in item.casefold()
        or "https://" in item.casefold()
        or any(marker in item for marker in ("[", "]", "#", "*", "`"))
        for item in text
    ):
        raise ValueError("memo fields must be plain single-line text without URLs")
    if any(not question.endswith("?") for question in draft.decision_changes):
        raise ValueError("decision changes must be questions")
    if len(_render_memo(analysis, recommendation, draft).split()) > MEMO_MAX_WORDS:
        raise ValueError(f"memo exceeds {MEMO_MAX_WORDS} words")


def _render_memo(
    analysis: AnalysisRecordV1,
    recommendation: Recommendation,
    draft: MemoDraftV1,
) -> str:
    evidence = {item.evidence_id: item for item in analysis.evidence}
    lines = [
        f"# {_single_line(analysis.candidate_name)}",
        "",
        f"**Recommendation: {recommendation.value}**",
        "",
        f"**Thesis score:** {analysis.total_score}/100 · "
        f"**Evidence coverage:** {analysis.evidence_coverage}%",
        "",
        "| Pillar | Score | Evidence |",
        "| --- | ---: | --- |",
        *(_pillar_row(score, evidence) for score in analysis.dimension_scores),
        "",
        "## Rationale",
        *(_memo_point(point, evidence) for point in draft.rationale),
        "",
        "## Key risks",
        *(_memo_point(point, evidence) for point in draft.key_risks),
        "",
        "## What would change the decision",
        *(f"- {question}" for question in draft.decision_changes),
    ]
    return "\n".join(lines) + "\n"


def _pillar_row(score: DimensionScoreV1, evidence: dict[str, EvidenceItemV1]) -> str:
    """One pillar per line, shown out of 100 (display only; weights stay 25/25/20/15/15 in the
    data); null shows as unknown, and only verified links are clickable."""
    label = score.dimension.value.replace("_", " ").capitalize()
    weight = THESIS_WEIGHTS[score.dimension]
    points = "unknown" if score.score is None else str(round(score.score * 100 / weight))
    links = " ".join(
        f"[{evidence_id}](<{evidence[evidence_id].source_url}>)"
        if evidence[evidence_id].verified
        else f"{evidence_id} (unverified)"
        for evidence_id in score.evidence_ids
    )
    return f"| {label} | {points}/100 | {links or '—'} |"


def _memo_point(point: CitedFindingV1, evidence: dict[str, EvidenceItemV1]) -> str:
    citations = " ".join(
        _citation(evidence_id, evidence[evidence_id]) for evidence_id in point.evidence_ids
    )
    return f"- {point.text} {citations}"


def _citation(evidence_id: str, evidence: EvidenceItemV1) -> str:
    label = f"{evidence_id} · self-reported" if evidence.self_reported else evidence_id
    return f"[{label}](<{evidence.source_url}>)"


def _render_index(result: RecommendationSetV1) -> str:
    lines = [
        "# Ranked Recommendations",
        "",
        "| Rank | Company | Score | Coverage | Recommendation | Memo |",
        "| ---: | --- | ---: | ---: | --- | --- |",
    ]
    for record in result.recommendations:
        memo = f"[open]({record.memo_path})" if record.memo_path else "render failed"
        lines.append(
            f"| {record.rank} | {_table_text(record.candidate_name)} | "
            f"{record.total_score} | {record.evidence_coverage}% | "
            f"{record.recommendation.value} | {memo} |"
        )
    return "\n".join(lines) + "\n"


def _single_line(value: str) -> str:
    return " ".join(value.split())


def _table_text(value: str) -> str:
    return _single_line(value).replace("|", "\\|")
