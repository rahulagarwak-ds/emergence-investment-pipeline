"""Versioned artifact contracts shared across stage boundaries."""

from enum import StrEnum
from typing import Literal, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    model_validator,
)

from investment_pipeline.shared.errors import ErrorCode, ErrorRecordV1

SCHEMA_VERSION: Literal["1.0"] = "1.0"
CANDIDATE_ID_PATTERN = r"^[a-z0-9][a-z0-9-]*$"


class ContractModel(BaseModel):
    """Strict base for persisted contracts."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TractionType(StrEnum):
    REVENUE = "revenue"
    PAID_CUSTOMERS = "paid_customers"
    ACTIVE_USAGE = "active_usage"
    DEPLOYMENTS_OR_DESIGN_PARTNERS = "deployments_or_design_partners"


class ThesisDimension(StrEnum):
    PRODUCT_ADOPTION = "product_adoption"
    WORKFLOW_HABIT_AND_IMPORTANCE = "workflow_habit_and_importance"
    EMPLOYEE_TO_TEAM_EXPANSION = "employee_to_team_expansion"
    ENTERPRISE_PROCUREMENT_PATH = "enterprise_procurement_path"
    FOUNDER_EXECUTION_FIT = "founder_execution_fit"


THESIS_WEIGHTS: dict[ThesisDimension, int] = {
    ThesisDimension.PRODUCT_ADOPTION: 25,
    ThesisDimension.WORKFLOW_HABIT_AND_IMPORTANCE: 25,
    ThesisDimension.EMPLOYEE_TO_TEAM_EXPANSION: 20,
    ThesisDimension.ENTERPRISE_PROCUREMENT_PATH: 15,
    ThesisDimension.FOUNDER_EXECUTION_FIT: 15,
}


class CriticalRisk(StrEnum):
    IDENTITY_UNVERIFIED = "identity_unverified"
    REQUIRES_UPFRONT_PROCUREMENT = "requires_upfront_procurement"
    NO_TEAM_EXPANSION_PATH = "no_team_expansion_path"
    NO_ENTERPRISE_PROCUREMENT_PATH = "no_enterprise_procurement_path"
    SECURITY_OR_COMPLIANCE_BLOCKER = "security_or_compliance_blocker"


class Recommendation(StrEnum):
    PASS = "Pass"
    WATCH = "Watch"
    TAKE_A_MEETING = "Take a meeting"


class FounderV1(ContractModel):
    name: str = Field(min_length=1)
    bio: str | None = None


class SourceReferenceV1(ContractModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    source_record_id: str = Field(min_length=1)
    source_url: HttpUrl
    captured_at: AwareDatetime
    self_reported: bool


class TractionSignalV1(ContractModel):
    traction_type: TractionType
    value: str = Field(min_length=1)
    period: str | None = None
    evidence: str = Field(min_length=1)
    source_url: HttpUrl
    self_reported: bool


class CandidateRecordV1(ContractModel):
    candidate_id: str = Field(pattern=CANDIDATE_ID_PATTERN)
    name: str = Field(min_length=1)
    website_url: HttpUrl
    canonical_domain: str = Field(min_length=1)
    yc_profile_url: HttpUrl
    tagline: str | None = None
    description: str | None = None
    categories: list[str] = []
    founders: list[FounderV1] = []
    team_size: int | None = Field(default=None, ge=1)
    founded_year: int | None = Field(default=None, ge=1900, le=2100)
    yc_batch: str | None = None
    status: str | None = None
    location: str | None = None
    traction: TractionSignalV1 | None = None
    is_current_batch: bool
    source: SourceReferenceV1


class SourcingStatsV1(ContractModel):
    loaded: int = Field(ge=0)
    matched: int = Field(ge=0)
    deduplicated: int = Field(ge=0)
    eligible: int = Field(ge=0, le=20)
    rejected: int = Field(ge=0)


class CandidateSetV1(ContractModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    created_at: AwareDatetime
    input_summary: str = Field(min_length=1)
    stats: SourcingStatsV1
    candidates: list[CandidateRecordV1] = Field(max_length=20)
    incomplete_candidates: list[CandidateRecordV1] = []
    errors: list[ErrorRecordV1] = []

    @model_validator(mode="after")
    def validate_candidate_ids(self) -> Self:
        candidate_ids = [
            candidate.candidate_id
            for candidate in (*self.candidates, *self.incomplete_candidates)
        ]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("candidate ids must be unique")
        if self.stats.eligible != len(self.candidates):
            raise ValueError("eligible count must match candidates")
        if any(
            not candidate.is_current_batch and candidate.traction is None
            for candidate in self.candidates
        ):
            raise ValueError("candidates must satisfy the freshness or traction gate")
        if any(
            candidate.is_current_batch or candidate.traction is not None
            for candidate in self.incomplete_candidates
        ):
            raise ValueError("incomplete candidates must fail the freshness and traction gate")
        has_insufficient_error = any(
            error.code is ErrorCode.INSUFFICIENT_CANDIDATES for error in self.errors
        )
        if (len(self.candidates) < 10) != has_insufficient_error:
            raise ValueError("insufficient candidate errors must match the 10-candidate gate")
        return self


class EvidenceItemV1(ContractModel):
    evidence_id: str = Field(min_length=1)
    claim: str = Field(min_length=1)
    source_url: HttpUrl
    observed_at: AwareDatetime | None
    self_reported: bool


class CitedFindingV1(ContractModel):
    text: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)


class DimensionScoreV1(ContractModel):
    dimension: ThesisDimension
    score: int | None = Field(ge=0)
    evidence_ids: list[str]

    @model_validator(mode="after")
    def validate_score(self) -> Self:
        if self.score is not None and self.score > THESIS_WEIGHTS[self.dimension]:
            raise ValueError(f"score exceeds {self.dimension} weight")
        if self.score is not None and not self.evidence_ids:
            raise ValueError("a score requires cited evidence; use null when evidence is missing")
        return self


class CriticalRiskFindingV1(ContractModel):
    risk: CriticalRisk
    evidence_ids: list[str] = Field(min_length=1)


class TokenUsageV1(ContractModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class OpenAIResponseMetadataV1(ContractModel):
    response_id: str = Field(min_length=1)
    model: str = Field(min_length=1)
    latency_ms: int = Field(ge=0)
    usage: TokenUsageV1
    source_urls: list[HttpUrl]


class AnalysisRecordV1(ContractModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    record_type: Literal["analysis"] = "analysis"
    candidate_id: str = Field(pattern=CANDIDATE_ID_PATTERN)
    candidate_name: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    prompt_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    response: OpenAIResponseMetadataV1
    team: list[CitedFindingV1]
    product: list[CitedFindingV1]
    market: list[CitedFindingV1]
    risks: list[CitedFindingV1]
    open_questions: list[str]
    unknowns: list[str]
    evidence: list[EvidenceItemV1]
    dimension_scores: list[DimensionScoreV1]
    total_score: int = Field(ge=0, le=100)
    evidence_coverage: int = Field(ge=0, le=100, multiple_of=20)
    critical_risks: list[CriticalRiskFindingV1] = []

    @model_validator(mode="after")
    def validate_evidence_and_scores(self) -> Self:
        evidence_id_list = [item.evidence_id for item in self.evidence]
        evidence_ids = set(evidence_id_list)
        if len(evidence_ids) != len(evidence_id_list):
            raise ValueError("evidence ids must be unique")
        referenced_ids = {
            evidence_id
            for findings in (self.team, self.product, self.market, self.risks)
            for finding in findings
            for evidence_id in finding.evidence_ids
        }
        referenced_ids.update(
            evidence_id
            for score in self.dimension_scores
            for evidence_id in score.evidence_ids
        )
        referenced_ids.update(
            evidence_id
            for risk in self.critical_risks
            for evidence_id in risk.evidence_ids
        )
        if missing_ids := referenced_ids - evidence_ids:
            raise ValueError(f"unknown evidence ids: {sorted(missing_ids)}")

        dimensions = [score.dimension for score in self.dimension_scores]
        if len(dimensions) != len(THESIS_WEIGHTS) or set(dimensions) != set(THESIS_WEIGHTS):
            raise ValueError("dimension_scores must contain each thesis dimension exactly once")
        expected_total = sum(score.score or 0 for score in self.dimension_scores)
        if self.total_score != expected_total:
            raise ValueError("total_score must sum dimension scores, with null contributing zero")
        expected_coverage = 20 * sum(bool(score.evidence_ids) for score in self.dimension_scores)
        if self.evidence_coverage != expected_coverage:
            raise ValueError("evidence_coverage must be 20 per cited thesis dimension")
        return self


class AnalysisSetV1(ContractModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    created_at: AwareDatetime
    analyses: list[AnalysisRecordV1]
    errors: list[ErrorRecordV1] = []

    @model_validator(mode="after")
    def validate_candidate_ids(self) -> Self:
        candidate_ids = [analysis.candidate_id for analysis in self.analyses]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("analysis candidate ids must be unique")
        return self


class RecommendationRecordV1(ContractModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    record_type: Literal["recommendation"] = "recommendation"
    candidate_id: str = Field(pattern=CANDIDATE_ID_PATTERN)
    candidate_name: str = Field(min_length=1)
    rank: int = Field(ge=1)
    total_score: int = Field(ge=0, le=100)
    evidence_coverage: int = Field(ge=0, le=100, multiple_of=20)
    critical_risks: list[CriticalRisk]
    recommendation: Recommendation
    prompt_version: str = Field(min_length=1)
    prompt_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    response: OpenAIResponseMetadataV1 | None = None
    memo_path: str | None = Field(default=None, pattern=r"^memos/[a-z0-9][a-z0-9-]*\.md$")

    @model_validator(mode="after")
    def validate_memo_metadata(self) -> Self:
        if (self.response is None) != (self.memo_path is None):
            raise ValueError(
                "response metadata and memo path must either both exist or both be null"
            )
        return self


class RecommendationSetV1(ContractModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    created_at: AwareDatetime
    recommendations: list[RecommendationRecordV1]
    errors: list[ErrorRecordV1] = []

    @model_validator(mode="after")
    def validate_ranks_and_candidates(self) -> Self:
        if [record.rank for record in self.recommendations] != list(
            range(1, len(self.recommendations) + 1)
        ):
            raise ValueError("recommendations must be in contiguous rank order")
        candidate_ids = [record.candidate_id for record in self.recommendations]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("recommendation candidate ids must be unique")
        return self
