"""Validate and normalize a manually captured or permissioned YC snapshot."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import AwareDatetime, Field, HttpUrl, ValidationError, model_validator

from investment_pipeline.shared.errors import ErrorCode, ErrorRecordV1
from investment_pipeline.shared.schemas import (
    CandidateRecordV1,
    CandidateSetV1,
    ContractModel,
    FounderV1,
    SourceReferenceV1,
    SourcingStatsV1,
    TractionSignalV1,
    TractionType,
)

_STAGE = "stage_01_sourcing"
_TRACTION_PRIORITY = {
    TractionType.REVENUE: 0,
    TractionType.PAID_CUSTOMERS: 1,
    TractionType.ACTIVE_USAGE: 2,
    TractionType.DEPLOYMENTS_OR_DESIGN_PARTNERS: 3,
}


class YCSnapshotRecordV1(ContractModel):
    """One public YC company record supplied outside the pipeline."""

    snapshot_version: Literal["1.0"] = "1.0"
    source_record_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    name: str = Field(min_length=1)
    website_url: HttpUrl | None = None
    yc_profile_url: HttpUrl
    tagline: str | None = None
    description: str | None = None
    categories: list[str] = []
    founders: list[FounderV1] = []
    team_size: int | None = Field(default=None, ge=1)
    founded_year: int | None = Field(default=None, ge=1900, le=2100)
    yc_batch: str | None = None
    current_batch: str = Field(min_length=1)
    status: str | None = None
    location: str | None = None
    traction_signals: list[TractionSignalV1] = []
    captured_at: AwareDatetime
    self_reported: bool = True

    @model_validator(mode="after")
    def validate_yc_profile(self) -> Self:
        if not _is_yc_profile_url(self.yc_profile_url):
            raise ValueError("yc_profile_url must be a YC company profile")
        if any(not _is_yc_profile_url(signal.source_url) for signal in self.traction_signals):
            raise ValueError("traction evidence must come from a YC company profile")
        return self


class SourcingSelectorV1(ContractModel):
    """Choose all records or exactly one deterministic selection mode."""

    topic: str | None = Field(default=None, min_length=1)
    yc_batch: str | None = Field(default=None, min_length=1)
    urls: list[HttpUrl] = []

    @model_validator(mode="after")
    def validate_one_mode(self) -> Self:
        if sum((self.topic is not None, self.yc_batch is not None, bool(self.urls))) > 1:
            raise ValueError("use only one of topic, yc_batch, or urls")
        if any(not _is_yc_profile_url(url) for url in self.urls):
            raise ValueError("urls must be YC company profiles")
        return self

    def summary(self) -> str:
        if self.topic is not None:
            return f'topic="{self.topic}"'
        if self.yc_batch is not None:
            return f'yc_batch="{self.yc_batch}"'
        if self.urls:
            return f"urls={len(self.urls)}"
        return "snapshot=all"


def run_sourcing(
    snapshot_path: Path,
    output_dir: Path,
    selector: SourcingSelectorV1 | None = None,
    max_candidates: int = 20,
) -> CandidateSetV1:
    """Run Stage 01 and persist its candidate and provenance artifacts."""
    if not 10 <= max_candidates <= 20:
        raise ValueError("max_candidates must be between 10 and 20")

    selector = selector or SourcingSelectorV1()
    records, errors = _load_snapshot(snapshot_path)
    matched = [record for record in records if _matches(record, selector)]
    unique_records, duplicate_errors = _deduplicate(matched)
    errors.extend(duplicate_errors)

    normalized: list[CandidateRecordV1] = []
    for record in unique_records:
        if candidate := _normalize(record, errors):
            normalized.append(candidate)

    eligible_candidates = [candidate for candidate in normalized if _is_eligible(candidate)]
    # ponytail: preserve snapshot order; add explicit ranking only if more than 20 is common.
    eligible = eligible_candidates[:max_candidates]
    incomplete = [candidate for candidate in normalized if not _is_eligible(candidate)]
    rejected = len(incomplete) + len(eligible_candidates[max_candidates:]) + len(errors)

    if len(eligible) < 10:
        errors.append(
            ErrorRecordV1(
                code=ErrorCode.INSUFFICIENT_CANDIDATES,
                message=f"Only {len(eligible)} eligible candidates; at least 10 are required",
                stage=_STAGE,
                details={"eligible": len(eligible), "required": 10},
            )
        )

    candidate_set = CandidateSetV1(
        created_at=datetime.now(UTC),
        input_summary=selector.summary(),
        stats=SourcingStatsV1(
            loaded=len(records),
            matched=len(matched),
            deduplicated=len(unique_records),
            eligible=len(eligible),
            rejected=rejected,
        ),
        candidates=eligible,
        incomplete_candidates=incomplete,
        errors=errors,
    )
    _write_artifacts(
        candidate_set,
        [_source_reference(record) for record in matched],
        output_dir,
    )
    return candidate_set


def _load_snapshot(path: Path) -> tuple[list[YCSnapshotRecordV1], list[ErrorRecordV1]]:
    records: list[YCSnapshotRecordV1] = []
    errors: list[ErrorRecordV1] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [
            ErrorRecordV1(
                code=ErrorCode.SOURCE_LOAD_FAILED,
                message=f"Could not read YC snapshot: {exc}",
                stage=_STAGE,
                details={"path": str(path)},
            )
        ]

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            records.append(YCSnapshotRecordV1.model_validate_json(line))
        except ValidationError as exc:
            issue = exc.errors(include_input=False)[0]
            location = ".".join(str(part) for part in issue["loc"])
            errors.append(
                ErrorRecordV1(
                    code=ErrorCode.INVALID_ARTIFACT,
                    message=(
                        f"Invalid snapshot record on line {line_number}: "
                        f"{location} {issue['msg']}"
                    ),
                    stage=_STAGE,
                    details={"line_number": line_number},
                )
            )
    return records, errors


def _matches(record: YCSnapshotRecordV1, selector: SourcingSelectorV1) -> bool:
    if selector.topic is not None:
        # ponytail: literal matching; add ranked tokens if real inputs show false negatives.
        topic = _normalize_text(selector.topic)
        searchable = _normalize_text(
            " ".join(
                value
                for value in (
                    record.name,
                    record.tagline,
                    record.description,
                    *record.categories,
                )
                if value
            )
        )
        return topic in searchable
    if selector.yc_batch is not None:
        return _normalize_text(record.yc_batch or "") == _normalize_text(selector.yc_batch)
    if selector.urls:
        wanted = {_normalized_url(url) for url in selector.urls}
        return _normalized_url(record.yc_profile_url) in wanted
    return True


def _deduplicate(
    records: list[YCSnapshotRecordV1],
) -> tuple[list[YCSnapshotRecordV1], list[ErrorRecordV1]]:
    unique: list[YCSnapshotRecordV1] = []
    errors: list[ErrorRecordV1] = []
    seen: set[tuple[str, str]] = set()
    for record in records:
        # ponytail: first record wins; merge fields only if snapshots overlap in practice.
        key = (
            ("domain", _canonical_domain(record.website_url))
            if record.website_url
            else ("name", _normalize_text(record.name))
        )
        if key in seen:
            errors.append(
                ErrorRecordV1(
                    code=ErrorCode.DUPLICATE_CANDIDATE,
                    message=f"Duplicate YC candidate ignored: {record.source_record_id}",
                    stage=_STAGE,
                    candidate_id=record.source_record_id,
                    details={"deduplication_key": f"{key[0]}:{key[1]}"},
                )
            )
            continue
        seen.add(key)
        unique.append(record)
    return unique, errors


def _normalize(
    record: YCSnapshotRecordV1,
    errors: list[ErrorRecordV1],
) -> CandidateRecordV1 | None:
    if record.website_url is None:
        errors.append(
            ErrorRecordV1(
                code=ErrorCode.CANDIDATE_NORMALIZATION_FAILED,
                message=f"Candidate has no website: {record.source_record_id}",
                stage=_STAGE,
                candidate_id=record.source_record_id,
            )
        )
        return None

    is_current_batch = (
        _normalize_text(record.yc_batch) == _normalize_text(record.current_batch)
        if record.yc_batch
        else record.founded_year == record.captured_at.year
    )
    return CandidateRecordV1(
        candidate_id=record.source_record_id,
        name=record.name,
        website_url=record.website_url,
        canonical_domain=_canonical_domain(record.website_url),
        yc_profile_url=record.yc_profile_url,
        tagline=record.tagline,
        description=record.description or record.tagline,
        categories=list(dict.fromkeys(record.categories)),
        founders=record.founders,
        team_size=record.team_size,
        founded_year=record.founded_year,
        yc_batch=record.yc_batch,
        status=record.status,
        location=record.location,
        traction=min(
            record.traction_signals,
            key=lambda signal: _TRACTION_PRIORITY[signal.traction_type],
            default=None,
        ),
        is_current_batch=is_current_batch,
        source=_source_reference(record),
    )


def _source_reference(record: YCSnapshotRecordV1) -> SourceReferenceV1:
    return SourceReferenceV1(
        source_record_id=record.source_record_id,
        source_url=record.yc_profile_url,
        captured_at=record.captured_at,
        self_reported=record.self_reported,
    )


def _write_artifacts(
    candidate_set: CandidateSetV1,
    source_refs: list[SourceReferenceV1],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "candidates.json").write_text(
        candidate_set.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "source_refs.jsonl").write_text(
        "".join(f"{source.model_dump_json()}\n" for source in source_refs),
        encoding="utf-8",
        newline="\n",
    )


def _is_eligible(candidate: CandidateRecordV1) -> bool:
    return candidate.is_current_batch or candidate.traction is not None


def _canonical_domain(url: HttpUrl) -> str:
    host = urlsplit(str(url)).hostname or ""
    return host.removeprefix("www.").casefold().rstrip(".")


def _normalized_url(url: HttpUrl) -> str:
    parsed = urlsplit(str(url))
    return f"{(parsed.hostname or '').casefold()}{parsed.path.rstrip('/')}"


def _is_yc_profile_url(url: HttpUrl) -> bool:
    return url.host in {"ycombinator.com", "www.ycombinator.com"} and (
        url.path or ""
    ).startswith("/companies/")


def _normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())
