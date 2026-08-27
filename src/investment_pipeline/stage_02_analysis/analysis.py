"""Evidence-grounded Stage 02 analysis."""

import json
from collections.abc import Callable
from datetime import UTC, datetime
from functools import partial
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from pydantic import HttpUrl

from investment_pipeline.shared.errors import ErrorCode, ErrorRecordV1
from investment_pipeline.shared.openai_client import StructuredOpenAIClient
from investment_pipeline.shared.schemas import (
    AnalysisRecordV1,
    AnalysisSetV1,
    CandidateRecordV1,
    CandidateSetV1,
    CitedFindingV1,
    ContractModel,
    CriticalRiskFindingV1,
    DimensionScoreV1,
    EvidenceItemV1,
    OpenAIResponseMetadataV1,
)

PROMPT_VERSION = "analysis-v1"
_PROMPT = Path(__file__).with_name("prompt_v1.md").read_text(encoding="utf-8")
PROMPT_HASH = sha256(_PROMPT.encode()).hexdigest()
_STAGE = "stage_02_analysis"


class AnalysisDraftV1(ContractModel):
    """Model-owned fields before deterministic totals and metadata are added."""

    team: list[CitedFindingV1]
    product: list[CitedFindingV1]
    market: list[CitedFindingV1]
    risks: list[CitedFindingV1]
    open_questions: list[str]
    unknowns: list[str]
    evidence: list[EvidenceItemV1]
    dimension_scores: list[DimensionScoreV1]
    critical_risks: list[CriticalRiskFindingV1]


def run_analysis(
    candidate_set: CandidateSetV1,
    output_dir: Path,
    client: StructuredOpenAIClient,
    on_candidate: Callable[[int, int, str, str], None] | None = None,
) -> AnalysisSetV1:
    """Analyze exactly the eligible Stage 01 candidates and persist JSONL results.

    ``on_candidate`` receives ``(index, total, candidate_name, "complete" | "failed")``.
    """
    if any(error.code is ErrorCode.INSUFFICIENT_CANDIDATES for error in candidate_set.errors):
        result = AnalysisSetV1(
            created_at=datetime.now(UTC),
            analyses=[],
            errors=[
                ErrorRecordV1(
                    code=ErrorCode.INVALID_ARTIFACT,
                    message="Stage 01 artifact has fewer than 10 eligible candidates",
                    stage=_STAGE,
                )
            ],
        )
        _write_artifact(result, output_dir)
        return result

    analyses: list[AnalysisRecordV1] = []
    errors: list[ErrorRecordV1] = []
    total = len(candidate_set.candidates)
    for index, candidate in enumerate(candidate_set.candidates, start=1):
        response = client.parse(
            instructions=_PROMPT,
            input_text=candidate.model_dump_json(indent=2),
            output_type=AnalysisDraftV1,
            stage=_STAGE,
            candidate_id=candidate.candidate_id,
            validate=partial(_validate_analysis, candidate),
            web_search=True,
        )
        succeeded = response.parsed is not None and response.metadata is not None
        if response.parsed is not None and response.metadata is not None:
            analyses.append(_build_analysis(candidate, response.parsed, response.metadata))
        else:
            errors.append(
                response.error
                or ErrorRecordV1(
                    code=ErrorCode.INVALID_MODEL_OUTPUT,
                    message="OpenAI response was missing parsed output or metadata",
                    stage=_STAGE,
                    candidate_id=candidate.candidate_id,
                )
            )
        if on_candidate is not None:
            on_candidate(index, total, candidate.name, "complete" if succeeded else "failed")
        if response.error is not None and response.error.code is ErrorCode.INVALID_CONFIG:
            break

    result = AnalysisSetV1(
        created_at=datetime.now(UTC),
        analyses=analyses,
        errors=errors,
    )
    _write_artifact(result, output_dir)
    return result


def _build_analysis(
    candidate: CandidateRecordV1,
    draft: AnalysisDraftV1,
    metadata: OpenAIResponseMetadataV1,
) -> AnalysisRecordV1:
    allowed_urls = {
        _normalized_url(candidate.source.source_url),
        *(_normalized_url(url) for url in metadata.source_urls),
    }
    candidate_source = _normalized_url(candidate.source.source_url)
    for evidence in draft.evidence:
        source_url = _normalized_url(evidence.source_url)
        if source_url not in allowed_urls:
            raise ValueError(f"unsupported evidence URL: {evidence.source_url}")
        if (
            source_url == candidate_source
            and evidence.self_reported != candidate.source.self_reported
        ):
            raise ValueError("YC evidence self-reported label does not match source provenance")

    total_score = sum(score.score or 0 for score in draft.dimension_scores)
    evidence_coverage = 20 * sum(bool(score.evidence_ids) for score in draft.dimension_scores)
    return AnalysisRecordV1(
        candidate_id=candidate.candidate_id,
        candidate_name=candidate.name,
        prompt_version=PROMPT_VERSION,
        prompt_hash=PROMPT_HASH,
        response=metadata,
        team=draft.team,
        product=draft.product,
        market=draft.market,
        risks=draft.risks,
        open_questions=draft.open_questions,
        unknowns=draft.unknowns,
        evidence=draft.evidence,
        dimension_scores=draft.dimension_scores,
        total_score=total_score,
        evidence_coverage=evidence_coverage,
        critical_risks=draft.critical_risks,
    )


def _validate_analysis(
    candidate: CandidateRecordV1,
    draft: AnalysisDraftV1,
    metadata: OpenAIResponseMetadataV1,
) -> None:
    _build_analysis(candidate, draft, metadata)


def load_analyses(path: Path) -> AnalysisSetV1:
    """Reload a Stage 02 artifact for replay; the set timestamp is the reload time."""
    analyses: list[AnalysisRecordV1] = []
    errors: list[ErrorRecordV1] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("record_type") == "error":
            errors.append(ErrorRecordV1.model_validate(record))
        else:
            analyses.append(AnalysisRecordV1.model_validate(record))
    return AnalysisSetV1(created_at=datetime.now(UTC), analyses=analyses, errors=errors)


def _write_artifact(result: AnalysisSetV1, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    lines = [*(analysis.model_dump_json() for analysis in result.analyses)]
    lines.extend(error.model_dump_json() for error in result.errors)
    (output_dir / "analyses.jsonl").write_text(
        "".join(f"{line}\n" for line in lines),
        encoding="utf-8",
        newline="\n",
    )


def _normalized_url(url: HttpUrl) -> str:
    parsed = urlsplit(str(url))
    return urlunsplit(
        (
            parsed.scheme.casefold(),
            parsed.netloc.casefold(),
            parsed.path.rstrip("/"),
            parsed.query,
            "",
        )
    )
