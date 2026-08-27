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

from investment_pipeline.shared.errors import ErrorRecordV1

SCHEMA_VERSION: Literal["1.0"] = "1.0"


class ContractModel(BaseModel):
    """Strict base for persisted contracts."""

    model_config = ConfigDict(extra="forbid")


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
    candidate_id: str = Field(min_length=1)
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


class CandidateSetV1(ContractModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    created_at: AwareDatetime
    input_summary: str = Field(min_length=1)
    candidates: list[CandidateRecordV1]
    errors: list[ErrorRecordV1] = []


class EvidenceItemV1(ContractModel):
    evidence_id: str = Field(min_length=1)
    claim: str = Field(min_length=1)
    source_url: HttpUrl
    observed_at: AwareDatetime | None = None
    self_reported: bool


class CitedFindingV1(ContractModel):
    text: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)


class DimensionScoreV1(ContractModel):
    dimension: ThesisDimension
    score: int = Field(ge=0)
    evidence_ids: list[str] = []

    @model_validator(mode="after")
    def validate_score(self) -> Self:
        if self.score > THESIS_WEIGHTS[self.dimension]:
            raise ValueError(f"score exceeds {self.dimension} weight")
        if self.score and not self.evidence_ids:
            raise ValueError("a non-zero score requires cited evidence")
        return self


class CriticalRiskFindingV1(ContractModel):
    risk: CriticalRisk
    evidence_ids: list[str] = Field(min_length=1)


class AnalysisRecordV1(ContractModel):
    candidate_id: str = Field(min_length=1)
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
        if self.total_score != sum(score.score for score in self.dimension_scores):
            raise ValueError("total_score must equal the dimension score sum")
        return self


class AnalysisSetV1(ContractModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    created_at: AwareDatetime
    analyses: list[AnalysisRecordV1]
    errors: list[ErrorRecordV1] = []
