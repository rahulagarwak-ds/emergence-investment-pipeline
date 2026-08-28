"""Thin OpenAI Responses boundary for typed pipeline calls."""

from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic
from typing import Any

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ValidationError

from investment_pipeline.shared.config import PipelineConfig
from investment_pipeline.shared.errors import ErrorCode, ErrorRecordV1
from investment_pipeline.shared.schemas import OpenAIResponseMetadataV1, TokenUsageV1


@dataclass(frozen=True)
class ParsedOpenAIResponse[T: BaseModel]:
    parsed: T | None = None
    metadata: OpenAIResponseMetadataV1 | None = None
    error: ErrorRecordV1 | None = None


class StructuredOpenAIClient:
    """Own configuration, retries, parsing, usage, latency, and structured errors."""

    def __init__(self, config: PipelineConfig, client: Any | None = None) -> None:
        self._model = config.openai_model
        self._reasoning_effort = config.openai_reasoning_effort
        self._configuration_error: str | None = None

        if not self._model:
            self._configuration_error = "OPENAI_MODEL is required"
            self._client = None
        elif client is not None:
            self._client = client
        elif config.openai_api_key is None:
            self._configuration_error = "OPENAI_API_KEY is required"
            self._client = None
        else:
            self._client = OpenAI(
                api_key=config.openai_api_key.get_secret_value(),
                timeout=config.request_timeout_seconds,
                max_retries=1,
            )

    def parse[T: BaseModel](
        self,
        *,
        instructions: str,
        input_text: str,
        output_type: type[T],
        stage: str,
        candidate_id: str,
        validate: Callable[[T, OpenAIResponseMetadataV1], object] | None = None,
        web_search: bool = False,
    ) -> ParsedOpenAIResponse[T]:
        """Parse one typed response, retrying invalid output once with a repair instruction."""
        if self._configuration_error or self._client is None or self._model is None:
            return ParsedOpenAIResponse(
                error=ErrorRecordV1(
                    code=ErrorCode.INVALID_CONFIG,
                    message=self._configuration_error or "OpenAI client is unavailable",
                    stage=stage,
                    candidate_id=candidate_id,
                )
            )

        started = monotonic()
        last_metadata: OpenAIResponseMetadataV1 | None = None
        last_reason = "no parsed output"
        for attempt in range(2):
            request: dict[str, Any] = {
                "model": self._model,
                "instructions": instructions
                if attempt == 0
                else (
                    f"{instructions}\n\nREPAIR: your previous output was rejected because: "
                    f"{last_reason}. Return a fully valid object that satisfies every instruction."
                ),
                "input": input_text,
                "text_format": output_type,
                "store": False,
            }
            if self._reasoning_effort is not None:
                request["reasoning"] = {"effort": self._reasoning_effort}
            if web_search:
                request.update(
                    tools=[{"type": "web_search"}],
                    include=["web_search_call.action.sources"],
                )

            try:
                response = self._client.responses.parse(**request)
                last_metadata = _metadata(response, monotonic() - started)
                parsed = response.output_parsed
                if not isinstance(parsed, output_type):
                    raise ValueError("response did not contain parsed output")
                if validate is not None:
                    validate(parsed, last_metadata)
                return ParsedOpenAIResponse(parsed=parsed, metadata=last_metadata)
            except OpenAIError as exc:
                return ParsedOpenAIResponse(
                    error=ErrorRecordV1(
                        code=ErrorCode.MODEL_REQUEST_FAILED,
                        message=f"OpenAI request failed: {type(exc).__name__}",
                        stage=stage,
                        candidate_id=candidate_id,
                        retryable=True,
                        details={"error": str(exc)[:500]},
                    )
                )
            except (ValidationError, ValueError) as exc:
                last_reason = str(exc)[:500]
                if attempt == 0:
                    continue

        details: dict[str, str | int] = {"attempts": 2, "reason": last_reason}
        if last_metadata is not None:
            details.update(
                response_id=last_metadata.response_id,
                model=last_metadata.model,
                latency_ms=last_metadata.latency_ms,
                input_tokens=last_metadata.usage.input_tokens,
                output_tokens=last_metadata.usage.output_tokens,
                total_tokens=last_metadata.usage.total_tokens,
            )
        return ParsedOpenAIResponse(
            error=ErrorRecordV1(
                code=ErrorCode.INVALID_MODEL_OUTPUT,
                message="OpenAI returned invalid structured output after one repair attempt",
                stage=stage,
                candidate_id=candidate_id,
                details=details,
            )
        )


def _metadata(response: Any, elapsed_seconds: float) -> OpenAIResponseMetadataV1:
    if response.status != "completed":
        raise ValueError(f"response status is {response.status}")
    usage = response.usage
    if usage is None:
        raise ValueError("response usage is missing")
    return OpenAIResponseMetadataV1(
        response_id=response.id,
        model=response.model,
        latency_ms=round(elapsed_seconds * 1000),
        usage=TokenUsageV1(
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
        ),
        source_urls=_source_urls(response),
    )


def _source_urls(response: Any) -> list[str]:
    urls: list[str] = []
    for item in response.output:
        if getattr(item, "type", None) != "web_search_call":
            continue
        action = getattr(item, "action", None)
        for source in getattr(action, "sources", None) or []:
            if url := getattr(source, "url", None):
                urls.append(url)
    return list(dict.fromkeys(urls))
