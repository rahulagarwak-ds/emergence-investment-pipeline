"""Structured failures preserved in pipeline artifacts."""

import re
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


def api_message(text: str, limit: int = 160) -> str:
    """Unwrap an SDK error body to its message and collapse whitespace."""
    if match := re.search(r"'message': '([^']+)'", text):
        text = match.group(1)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def failure_reason(error: ErrorRecordV1, limit: int = 90) -> str:
    """One short line for live progress: the validation reason or the API's own message."""
    detail = str(error.details.get("reason") or error.details.get("error") or error.message)
    return api_message(detail, limit)

