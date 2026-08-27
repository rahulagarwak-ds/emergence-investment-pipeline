"""Snapshot capture from a purpose-built yc-oss-shaped payload; no network."""

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest

from investment_pipeline import stage_01_sourcing
from investment_pipeline.cli import main
from investment_pipeline.shared.errors import ErrorCode
from investment_pipeline.stage_01_sourcing import YCSnapshotRecordV1, run_sourcing
from investment_pipeline.stage_01_sourcing.yc_snapshot import (
    SnapshotProvenanceV1,
    batch_in_session,
    capture_yc_snapshot,
)

_BATCH = (Path(__file__).parent / "fixtures" / "yc_oss_batch.json").read_bytes()
_META = json.dumps({"last_updated": "2026-08-27T05:52:19.855Z", "batches": {}}).encode()
_CAPTURED_AT = datetime(2026, 8, 27, 20, 0, tzinfo=UTC)


def _fetch(url: str) -> bytes:
    assert url.startswith("https://yc-oss.github.io/api/")
    return _META if url.endswith("meta.json") else _BATCH


def test_capture_writes_contract_records_and_provenance(tmp_path: Path) -> None:
    output = tmp_path / "inputs" / "yc_snapshot.jsonl"

    provenance = capture_yc_snapshot(None, output, fetch=_fetch, captured_at=_CAPTURED_AT)

    records = [
        YCSnapshotRecordV1.model_validate_json(line)
        for line in output.read_text(encoding="utf-8").splitlines()
    ]
    assert [record.source_record_id for record in records] == [
        "example-01",
        "example-02",
        "example-03",
    ]
    first, no_site, sparse = records
    assert first.categories == ["B2B", "AI", "Sales"]
    assert first.yc_batch == first.current_batch == "Summer 2026"
    assert first.founders == [] and first.traction_signals == [] and first.founded_year is None
    assert no_site.website_url is None
    assert sparse.team_size is None and sparse.description is None and sparse.categories == ["B2B"]
    assert all(record.captured_at == _CAPTURED_AT for record in records)

    assert provenance.records == 3
    assert provenance.skipped == ["not-yc"]
    assert provenance.current_batch == "Summer 2026"
    assert provenance.captured_at == _CAPTURED_AT
    assert provenance.upstream_sha256 == sha256(_BATCH).hexdigest()
    assert str(provenance.batch_url) == "https://yc-oss.github.io/api/batches/summer-2026.json"
    sidecar = SnapshotProvenanceV1.model_validate_json(
        output.with_suffix(".provenance.json").read_text(encoding="utf-8")
    )
    assert sidecar == provenance

    sourced = run_sourcing(output, tmp_path / "01_sourcing")
    assert [candidate.candidate_id for candidate in sourced.candidates] == [
        "example-01",
        "example-03",
    ]
    assert {error.code for error in sourced.errors} == {
        ErrorCode.CANDIDATE_NORMALIZATION_FAILED,
        ErrorCode.INSUFFICIENT_CANDIDATES,
    }


def test_explicit_batch_is_fetched_but_current_batch_follows_the_calendar(
    tmp_path: Path,
) -> None:
    seen: list[str] = []

    def fetch(url: str) -> bytes:
        seen.append(url)
        return _fetch(url)

    provenance = capture_yc_snapshot(
        "Winter 2025", tmp_path / "snapshot.jsonl", fetch=fetch, captured_at=_CAPTURED_AT
    )

    assert seen[-1] == "https://yc-oss.github.io/api/batches/winter-2025.json"
    assert provenance.current_batch == "Summer 2026"


def test_batch_in_session_follows_the_quarter_calendar() -> None:
    assert batch_in_session(datetime(2026, 1, 15, tzinfo=UTC)) == "Winter 2026"
    assert batch_in_session(datetime(2026, 6, 30, tzinfo=UTC)) == "Spring 2026"
    assert batch_in_session(datetime(2026, 8, 27, tzinfo=UTC)) == "Summer 2026"
    assert batch_in_session(datetime(2026, 12, 1, tzinfo=UTC)) == "Fall 2026"


def test_snapshot_command_reports_counts_and_exits_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "yc_snapshot.jsonl"

    def offline_capture(batch: str | None, path: Path) -> SnapshotProvenanceV1:
        return capture_yc_snapshot(batch, path, fetch=_fetch, captured_at=_CAPTURED_AT)

    monkeypatch.setattr(stage_01_sourcing, "capture_yc_snapshot", offline_capture)

    with pytest.raises(SystemExit) as exit_info:
        main(["snapshot", "--output", str(output)])

    assert exit_info.value.code == 0
    assert output.is_file()
    out = capsys.readouterr().out
    assert "Summer 2026 · 3 records · 1 skipped · dataset updated 2026-08-27" in out
