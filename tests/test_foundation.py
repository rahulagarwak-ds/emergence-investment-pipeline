"""Foundation smoke checks."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from investment_pipeline.shared.config import PipelineConfig
from investment_pipeline.shared.schemas import (
    AnalysisRecordV1,
    CandidateRecordV1,
    CitedFindingV1,
    DimensionScoreV1,
    SourceReferenceV1,
    ThesisDimension,
)


def test_foundation_imports_and_rejects_malformed_contracts() -> None:
    config = PipelineConfig(_env_file=None)
    assert config.max_candidates == 20

    source = SourceReferenceV1(
        source_record_id="example",
        source_url="https://www.ycombinator.com/companies/example",
        captured_at=datetime.now(UTC),
        self_reported=True,
    )
    with pytest.raises(ValidationError):
        CandidateRecordV1.model_validate(
            {
                "candidate_id": "example",
                "name": "Example",
                "website_url": "not-a-url",
                "canonical_domain": "example.com",
                "yc_profile_url": str(source.source_url),
                "is_current_batch": True,
                "source": source.model_dump(),
                "unexpected": "rejected",
            }
        )

    scores = [DimensionScoreV1(dimension=dimension, score=0) for dimension in ThesisDimension]
    with pytest.raises(ValidationError):
        AnalysisRecordV1(
            candidate_id="example",
            team=[CitedFindingV1(text="Unsupported claim", evidence_ids=["missing"])],
            product=[],
            market=[],
            risks=[],
            open_questions=[],
            unknowns=[],
            evidence=[],
            dimension_scores=scores,
            total_score=0,
            evidence_coverage=0,
        )
