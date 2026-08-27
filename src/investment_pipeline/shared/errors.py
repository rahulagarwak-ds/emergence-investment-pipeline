"""Structured failures preserved in pipeline artifacts."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, JsonValue


class ErrorCode(StrEnum):
    """Stable machine-readable pipeline failure codes."""

    INVALID_CONFIG = "INVALID_CONFIG"
    INVALID_INPUT = "INVALID_INPUT"
    INVALID_ARTIFACT = "INVALID_ARTIFACT"
    INSUFFICIENT_CANDIDATES = "INSUFFICIENT_CANDIDATES"
    SOURCE_LOAD_FAILED = "SOURCE_LOAD_FAILED"
    CANDIDATE_NORMALIZATION_FAILED = "CANDIDATE_NORMALIZATION_FAILED"
    DUPLICATE_CANDIDATE = "DUPLICATE_CANDIDATE"
    MODEL_REQUEST_FAILED = "MODEL_REQUEST_FAILED"
    INVALID_MODEL_OUTPUT = "INVALID_MODEL_OUTPUT"
    MEMO_RENDER_FAILED = "MEMO_RENDER_FAILED"


class ErrorRecordV1(BaseModel):
    """Serializable error attached to a run or candidate."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    record_type: Literal["error"] = "error"
    code: ErrorCode
    message: str
    stage: str | None = None
    candidate_id: str | None = None
    retryable: bool = False
    details: dict[str, JsonValue] = {}
