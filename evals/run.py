"""Grade one completed run: deterministic graders always, the semantic judge on request."""

import json
import sys
from argparse import ArgumentParser
from collections.abc import Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from statistics import mean

from pydantic import Field, JsonValue

from evals.graders import GRADERS, GradedRun, load_run
from investment_pipeline.shared.config import PipelineConfig
from investment_pipeline.shared.errors import ErrorCode
from investment_pipeline.shared.openai_client import StructuredOpenAIClient
from investment_pipeline.shared.schemas import ContractModel

REPORTS = Path(__file__).with_name("reports")
JUDGE_PROMPT_VERSION = "judge-v1"
_JUDGE_PROMPT = Path(__file__).with_name("judge_prompt_v1.md").read_text(encoding="utf-8")
JUDGE_PROMPT_HASH = sha256(_JUDGE_PROMPT.encode()).hexdigest()
_RATINGS = ("thesis_adherence", "faithfulness", "clarity", "risk_quality", "specificity")


class MemoJudgementV1(ContractModel):
    """Five 1-5 ratings from the judge model plus one short note."""

    thesis_adherence: int = Field(ge=1, le=5)
    faithfulness: int = Field(ge=1, le=5)
    clarity: int = Field(ge=1, le=5)
    risk_quality: int = Field(ge=1, le=5)
    specificity: int = Field(ge=1, le=5)
    notes: str = Field(min_length=1)


def main(argv: Sequence[str] | None = None) -> None:
    parser = ArgumentParser(prog="investment-evals", description="Grade one pipeline run")
    parser.add_argument("run_dir", type=Path, help="outputs/<run_id> directory to grade")
    parser.add_argument(
        "--semantic",
        action="store_true",
        help="also ask the configured OpenAI model to rate each memo (costs tokens)",
    )
    args = parser.parse_args(argv)

    try:
        run = load_run(args.run_dir)
    except (OSError, ValueError) as exc:
        print(f"schema        run artifacts failed to load: {type(exc).__name__}")
        sys.exit(1)

    findings = [finding for grader in GRADERS for finding in grader(run)]
    report: dict[str, JsonValue] = {
        "run_id": run.manifest.run_id,
        "model": run.manifest.versions.get("model"),
        "analysis_prompt": run.manifest.versions.get("analysis_prompt"),
        "memo_prompt": run.manifest.versions.get("memo_prompt"),
        "graded_at": datetime.now(UTC).isoformat(),
        "deterministic": {
            "findings": [asdict(finding) for finding in findings],
            "passed": not findings,
        },
        "semantic": judge(run, StructuredOpenAIClient(PipelineConfig())) if args.semantic else None,
    }
    REPORTS.mkdir(exist_ok=True)
    report_path = REPORTS / f"{run.manifest.run_id}.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")

    for grader in GRADERS:
        name = grader.__name__.removeprefix("grade_")
        count = sum(finding.grader == name for finding in findings)
        print(f"{name:<14}{count} finding{'' if count == 1 else 's'}")
    for finding in findings:
        print(f"  - {finding.candidate_id}: {finding.message}")
    semantic = report["semantic"]
    if isinstance(semantic, dict):
        print(f"semantic      {semantic.get('averages') or semantic.get('skipped')}")
    print(f"report        {report_path.as_posix()}")
    sys.exit(1 if findings else 0)


def judge(run: GradedRun, client: StructuredOpenAIClient) -> dict[str, JsonValue]:
    """Rate each rendered memo with the judge model; return ratings, errors, and averages."""
    analyses = {analysis.candidate_id: analysis for analysis in run.analyses.analyses}
    judgements: dict[str, MemoJudgementV1] = {}
    errors: dict[str, JsonValue] = {}
    for candidate_id, memo in run.memos.items():
        response = client.parse(
            instructions=_JUDGE_PROMPT,
            input_text=json.dumps(
                {
                    "memo": memo,
                    "analysis": analyses[candidate_id].model_dump(
                        mode="json", exclude={"response"}
                    ),
                },
                indent=2,
            ),
            output_type=MemoJudgementV1,
            stage="evals",
            candidate_id=candidate_id,
        )
        if response.error is not None and response.error.code is ErrorCode.INVALID_CONFIG:
            return {"skipped": response.error.message}
        if response.error is not None:
            errors[candidate_id] = response.error.message
        elif response.parsed is not None:
            judgements[candidate_id] = response.parsed
    ratings: dict[str, JsonValue] = {
        candidate_id: judgement.model_dump() for candidate_id, judgement in judgements.items()
    }
    averages: dict[str, JsonValue] = {
        name: round(mean(getattr(judgement, name) for judgement in judgements.values()), 2)
        for name in _RATINGS
        if judgements
    }
    return {
        "judge_prompt": f"{JUDGE_PROMPT_VERSION}@{JUDGE_PROMPT_HASH}",
        "ratings": ratings,
        "errors": errors,
        "averages": averages,
    }
