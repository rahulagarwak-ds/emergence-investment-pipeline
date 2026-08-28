"""Opt-in live smoke of the OpenAI boundary; set LIVE_SMOKE=1 with a configured .env to run."""

import os
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from investment_pipeline.shared.config import PipelineConfig
from investment_pipeline.shared.openai_client import StructuredOpenAIClient
from investment_pipeline.stage_01_sourcing import run_sourcing
from investment_pipeline.stage_02_analysis import analysis
from investment_pipeline.stage_02_analysis.analysis import AnalysisDraftV1

pytestmark = pytest.mark.skipif(
    os.environ.get("LIVE_SMOKE") != "1", reason="set LIVE_SMOKE=1 to call the live OpenAI API"
)
_FIXTURE = Path(__file__).parent / "fixtures" / "yc_snapshot.jsonl"


def test_live_structured_analysis_round_trip(tmp_path: Path) -> None:
    """One real Responses call: structured output parses and no evidence is invented."""
    config = PipelineConfig()
    assert config.openai_api_key is not None and config.openai_model, "configure .env first"
    candidate = run_sourcing(_FIXTURE, tmp_path).candidates[0]
    prompt = Path(analysis.__file__).with_name("prompt_v1.md").read_text(encoding="utf-8")

    response = StructuredOpenAIClient(config).parse(
        instructions=prompt,
        input_text=candidate.model_dump_json(indent=2),
        output_type=AnalysisDraftV1,
        stage="live_smoke",
        candidate_id=candidate.candidate_id,
        web_search=True,
    )

    assert response.error is None, response.error
    assert response.parsed is not None and response.metadata is not None
    assert response.metadata.usage.total_tokens > 0
    sources = {str(url).rstrip("/") for url in response.metadata.source_urls}
    for item in response.parsed.evidence:
        host = (urlsplit(item.source_url).hostname or "").casefold()
        company_page = host.endswith(candidate.canonical_domain) or host.endswith("ycombinator.com")
        assert company_page or item.source_url.rstrip("/") in sources, item
