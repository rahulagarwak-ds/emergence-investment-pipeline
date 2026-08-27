"""Stage 01 deterministic sourcing checks using purpose-built records."""

from pathlib import Path

from investment_pipeline.shared.errors import ErrorCode
from investment_pipeline.shared.schemas import CandidateSetV1, TractionType
from investment_pipeline.stage_01_sourcing import SourcingSelectorV1, run_sourcing

_FIXTURE = Path(__file__).parent / "fixtures" / "yc_snapshot.jsonl"


def test_snapshot_normalization_deduplication_eligibility_and_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "01_sourcing"
    result = run_sourcing(_FIXTURE, output_dir)

    assert result.stats.model_dump() == {
        "loaded": 13,
        "matched": 13,
        "deduplicated": 12,
        "eligible": 10,
        "rejected": 4,
    }
    assert result.candidates[0].canonical_domain == "example-01.test"
    assert result.candidates[0].description == "Workflow assistant one"
    assert result.candidates[-1].traction is not None
    assert result.candidates[-1].traction.traction_type is TractionType.REVENUE
    assert [candidate.candidate_id for candidate in result.incomplete_candidates] == [
        "legacy-incomplete"
    ]
    assert {error.code for error in result.errors} == {
        ErrorCode.DUPLICATE_CANDIDATE,
        ErrorCode.INVALID_ARTIFACT,
        ErrorCode.CANDIDATE_NORMALIZATION_FAILED,
    }

    saved = CandidateSetV1.model_validate_json(
        (output_dir / "candidates.json").read_text(encoding="utf-8")
    )
    assert saved == result
    assert len((output_dir / "source_refs.jsonl").read_text(encoding="utf-8").splitlines()) == 13


def test_selectors_and_insufficient_candidate_failure_are_preserved(tmp_path: Path) -> None:
    result = run_sourcing(
        _FIXTURE,
        tmp_path / "batch",
        SourcingSelectorV1(yc_batch="Winter 2025"),
    )
    assert [candidate.candidate_id for candidate in result.candidates] == ["legacy-traction"]
    assert [candidate.candidate_id for candidate in result.incomplete_candidates] == [
        "legacy-incomplete"
    ]
    assert result.errors[-1].code is ErrorCode.INSUFFICIENT_CANDIDATES

    by_url = run_sourcing(
        _FIXTURE,
        tmp_path / "url",
        SourcingSelectorV1(
            urls=["https://www.ycombinator.com/companies/example-02?ignored=true"]
        ),
    )
    assert [candidate.candidate_id for candidate in by_url.candidates] == ["example-02"]

    by_topic = run_sourcing(
        _FIXTURE,
        tmp_path / "topic",
        SourcingSelectorV1(topic="workflow assistant one"),
    )
    assert [candidate.candidate_id for candidate in by_topic.candidates] == ["example-01"]
