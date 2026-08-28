"""Evidence-grounded Stage 02 analysis."""

import json
from collections.abc import Callable
from datetime import UTC, datetime
from functools import partial
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from pydantic import AwareDatetime, Field, HttpUrl

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

PROMPT_VERSION = "analysis-v2"
_PROMPT = Path(__file__).with_name("prompt_v2.md").read_text(encoding="utf-8")
PROMPT_HASH = sha256(_PROMPT.encode()).hexdigest()
_STAGE = "stage_02_analysis"
_USER_AGENT = "investment-pipeline/0.1 (evidence link check)"
UrlCheck = Callable[[str], int | None]


class EvidenceDraftV1(ContractModel):
    """Evidence as the model returns it; ``source_url`` stays a string because OpenAI's strict
    schema subset rejects ``format: uri``. Python converts it into ``EvidenceItemV1``."""

    # Short tokens only: the id becomes the memo's citation label, so a URL here is unreadable.
    evidence_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,31}$")
    claim: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    observed_at: AwareDatetime | None
    self_reported: bool


class AnalysisDraftV1(ContractModel):
    """Model-owned fields before deterministic totals and metadata are added."""

    team: list[CitedFindingV1]
    product: list[CitedFindingV1]
    market: list[CitedFindingV1]
    risks: list[CitedFindingV1]
    open_questions: list[str]
    unknowns: list[str]
    evidence: list[EvidenceDraftV1]
    dimension_scores: list[DimensionScoreV1]
    critical_risks: list[CriticalRiskFindingV1]


def run_analysis(
    candidate_set: CandidateSetV1,
    output_dir: Path,
    client: StructuredOpenAIClient,
    on_candidate: Callable[[int, int, str, str], None] | None = None,
    check_url: UrlCheck | None = None,
) -> AnalysisSetV1:
    """Analyze exactly the eligible Stage 01 candidates and persist JSONL results.

    ``on_candidate`` receives ``(index, total, candidate_name, "complete" | "failed")``.
    ``check_url`` returns the HTTP status of an evidence URL (default: a real request).
    """
    check_url = check_url or http_status
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
        statuses: dict[str, int | None] = {}  # one request per URL per candidate, across repairs
        response = client.parse(
            instructions=_PROMPT,
            input_text=candidate.model_dump_json(indent=2),
            output_type=AnalysisDraftV1,
            stage=_STAGE,
            candidate_id=candidate.candidate_id,
            validate=partial(_validate_analysis, candidate, check_url, statuses),
            web_search=True,
        )
        succeeded = response.parsed is not None and response.metadata is not None
        if response.parsed is not None and response.metadata is not None:
            analyses.append(
                _build_analysis(candidate, response.parsed, response.metadata, check_url, statuses)
            )
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
    check_url: UrlCheck,
    statuses: dict[str, int | None],
) -> AnalysisRecordV1:
    # Company-authored pages (YC profile, any page on the company's domain) are allowed but must
    # stay self-reported; everything else must be a URL the web search actually returned.
    yc_profile = _normalized_url(candidate.source.source_url)
    web_sources = {_normalized_url(url) for url in metadata.source_urls}
    checked_at = datetime.now(UTC)
    evidence_items: list[EvidenceItemV1] = []
    for item in draft.evidence:
        evidence = EvidenceItemV1.model_validate(item.model_dump())
        source_url = _normalized_url(evidence.source_url)
        company_authored = source_url == yc_profile or _on_domain(
            evidence.source_url, candidate.canonical_domain
        )
        if not company_authored and source_url not in web_sources:
            raise ValueError(
                f"unsupported evidence URL: {evidence.source_url} (cite only the YC profile, "
                "pages on the company's own domain, or URLs returned by web search)"
            )
        if company_authored and not evidence.self_reported:
            raise ValueError(
                f"company-authored evidence must be marked self-reported: {evidence.source_url}"
            )
        # Every cited link is requested once. Broken links (404, 5xx, unreachable) are rejected;
        # pages that exist but refuse us (403 forbidden, 429 rate limited) stay unverified.
        url = str(evidence.source_url)
        if url not in statuses:
            statuses[url] = check_url(url)
        status = statuses[url]
        if status is None or (status >= 400 and status not in (403, 429)):
            raise ValueError(
                f"evidence {evidence.evidence_id} link returned {status or 'no response'}: {url} "
                "(cite a page that loads, or drop this evidence)"
            )
        evidence_items.append(
            evidence.model_copy(update={"http_status": status, "verified_at": checked_at})
        )

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
        evidence=evidence_items,
        dimension_scores=draft.dimension_scores,
        total_score=total_score,
        evidence_coverage=evidence_coverage,
        critical_risks=draft.critical_risks,
    )


def _validate_analysis(
    candidate: CandidateRecordV1,
    check_url: UrlCheck,
    statuses: dict[str, int | None],
    draft: AnalysisDraftV1,
    metadata: OpenAIResponseMetadataV1,
) -> None:
    _build_analysis(candidate, draft, metadata, check_url, statuses)


def http_status(url: str, timeout: float = 10.0) -> int | None:
    """HTTP status of ``url`` (HEAD, then GET when HEAD is refused); None when unreachable."""
    for method in ("HEAD", "GET"):
        request = Request(url, method=method, headers={"User-Agent": _USER_AGENT})
        try:
            with urlopen(request, timeout=timeout) as response:
                return int(response.status)
        except HTTPError as exc:
            if method == "HEAD" and exc.code in (403, 405, 501):
                continue
            return int(exc.code)
        except (URLError, TimeoutError, ValueError, OSError):
            if method == "HEAD":
                continue
            return None
    return None


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
    """Compare URLs without case, trailing slash, query string, or fragment."""
    parsed = urlsplit(str(url))
    return urlunsplit(
        (parsed.scheme.casefold(), parsed.netloc.casefold(), parsed.path.rstrip("/"), "", "")
    )


def _on_domain(url: HttpUrl, canonical_domain: str) -> bool:
    host = (urlsplit(str(url)).hostname or "").casefold()
    return host == canonical_domain or host.endswith(f".{canonical_domain}")
