"""Capture a YC batch snapshot from the yc-oss open dataset.

yc-oss republishes YC's public Algolia company index daily as static JSON; it is not a scrape of
ycombinator.com and only covers publicly launched companies. The dataset carries no founder bios,
founding years, or traction claims, so those fields stay empty here and unknown downstream.
"""

import json
from collections.abc import Callable
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal
from urllib.request import urlopen

from pydantic import AwareDatetime, Field, HttpUrl, ValidationError

from investment_pipeline.shared.schemas import ContractModel
from investment_pipeline.stage_01_sourcing.sourcing import YCSnapshotRecordV1

DATASET_URL = "https://yc-oss.github.io/api"
_SEASONS = ("Winter", "Spring", "Summer", "Fall")


class SnapshotProvenanceV1(ContractModel):
    """Where a snapshot came from and what the capture dropped."""

    schema_version: Literal["1.0"] = "1.0"
    dataset: Literal["yc-oss/api"] = "yc-oss/api"
    meta_url: HttpUrl
    batch_url: HttpUrl
    dataset_last_updated: str = Field(min_length=1)
    current_batch: str = Field(min_length=1)
    captured_at: AwareDatetime
    upstream_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    records: int = Field(ge=0)
    skipped: list[str] = []


def capture_yc_snapshot(
    batch: str | None,
    output_path: Path,
    fetch: Callable[[str], bytes] | None = None,
    captured_at: datetime | None = None,
) -> SnapshotProvenanceV1:
    """Write one YCSnapshotRecordV1 per launched company in ``batch`` plus a provenance sidecar.

    ``batch`` defaults to the batch in session at capture time, which is also what
    ``is_current_batch`` compares against downstream.
    """
    fetch = fetch or _download
    captured_at = captured_at or datetime.now(UTC)
    current_batch = batch_in_session(captured_at)
    batch = batch or current_batch
    meta_url = f"{DATASET_URL}/meta.json"
    meta = json.loads(fetch(meta_url))
    batch_url = f"{DATASET_URL}/batches/{batch.casefold().replace(' ', '-')}.json"
    upstream = fetch(batch_url)

    lines: list[str] = []
    skipped: list[str] = []
    for company in json.loads(upstream):
        try:
            record = _record(company, current_batch, captured_at)
        except (ValidationError, KeyError, TypeError):
            skipped.append(str(company.get("slug") or company.get("id") or "unknown"))
            continue
        lines.append(record.model_dump_json())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8", newline="\n")
    provenance = SnapshotProvenanceV1(
        meta_url=meta_url,
        batch_url=batch_url,
        dataset_last_updated=str(meta.get("last_updated") or "unknown"),
        current_batch=current_batch,
        captured_at=captured_at,
        upstream_sha256=sha256(upstream).hexdigest(),
        records=len(lines),
        skipped=skipped,
    )
    output_path.with_suffix(".provenance.json").write_text(
        provenance.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return provenance


def _record(
    company: dict[str, Any], current_batch: str, captured_at: datetime
) -> YCSnapshotRecordV1:
    categories = [*(company.get("industries") or []), *(company.get("tags") or [])]
    return YCSnapshotRecordV1(
        source_record_id=company["slug"],
        name=company["name"],
        website_url=company.get("website") or None,
        yc_profile_url=company["url"],
        tagline=company.get("one_liner") or None,
        description=company.get("long_description") or None,
        categories=list(dict.fromkeys(categories)),
        team_size=company.get("team_size") or None,
        yc_batch=company.get("batch") or None,
        current_batch=current_batch,
        status=company.get("status") or None,
        location=company.get("all_locations") or None,
        captured_at=captured_at,
    )


def batch_in_session(moment: datetime) -> str:
    """The batch in session on ``moment``; calendar quarters map to Winter, Spring, Summer, Fall.

    Future batches appear in the directory as soon as their first companies launch, so "newest
    batch present" would not mean "current"; the calendar does.
    """
    return f"{_SEASONS[(moment.month - 1) // 3]} {moment.year}"


def _download(url: str) -> bytes:
    with urlopen(url, timeout=60) as response:
        return bytes(response.read())
