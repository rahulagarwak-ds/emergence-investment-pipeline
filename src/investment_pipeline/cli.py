"""Command-line entry point and stage orchestration."""

import sys
import traceback
from argparse import ArgumentParser, Namespace
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from shutil import copyfile
from time import monotonic

from pydantic import HttpUrl, ValidationError

from investment_pipeline import stage_01_sourcing, stage_02_analysis, stage_03_recommendation
from investment_pipeline.shared.config import PipelineConfig
from investment_pipeline.shared.errors import ErrorCode, ErrorRecordV1
from investment_pipeline.shared.openai_client import StructuredOpenAIClient
from investment_pipeline.shared.run_store import (
    append_log,
    artifact_ref,
    create_run_dir,
    display_path,
    file_sha256,
    write_manifest,
)
from investment_pipeline.shared.schemas import (
    SCHEMA_VERSION,
    AnalysisSetV1,
    ArtifactRefV1,
    CandidateSetV1,
    OpenAIResponseMetadataV1,
    Recommendation,
    RunInputV1,
    RunManifestV1,
    StageRunV1,
    StageStatus,
    TokenUsageV1,
)

_SOURCING, _ANALYSIS, _RECOMMENDATION = "01_sourcing", "02_analysis", "03_recommendation"
_LABELS = {
    _SOURCING: "[1/3] Sourcing",
    _ANALYSIS: "[2/3] Analysis",
    _RECOMMENDATION: "[3/3] Recommendation",
}
_REPLAY_STAGES = {"candidates.json": _SOURCING, "analyses.jsonl": _ANALYSIS}


def main(argv: Sequence[str] | None = None) -> None:
    """Parse arguments, load configuration, and run the pipeline."""
    args = _parser().parse_args(argv)
    try:
        config = PipelineConfig()
    except ValidationError as exc:
        _say(
            "Failed",
            f"{exc.error_count()} invalid setting(s) in .env · compare with .env.example",
        )
        sys.exit(2)
    sys.exit(run_pipeline(args, config, StructuredOpenAIClient(config)))


def _parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="investment-pipeline", description="AI-augmented investment pipeline"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="source, analyze, and recommend YC candidates")
    mode = run.add_mutually_exclusive_group()
    mode.add_argument(
        "--topic", help="topic matched against name, tagline, description, categories"
    )
    mode.add_argument("--yc-batch", help='YC batch, for example "Summer 2026"')
    mode.add_argument(
        "--url",
        action="append",
        dest="urls",
        default=[],
        metavar="YC_PROFILE_URL",
        help="YC company profile URL; repeat for several",
    )
    mode.add_argument(
        "--from-artifact",
        type=Path,
        metavar="PATH",
        help="replay from a prior run's 01_sourcing/candidates.json or 02_analysis/analyses.jsonl",
    )
    run.add_argument(
        "--snapshot",
        type=Path,
        default=Path("inputs/yc_snapshot.jsonl"),
        help="YC snapshot JSONL (default: inputs/yc_snapshot.jsonl)",
    )
    return parser


def run_pipeline(args: Namespace, config: PipelineConfig, client: StructuredOpenAIClient) -> int:
    """Run or replay the pipeline inside a new run directory and return the exit code."""
    started = monotonic()
    run_dir = create_run_dir(config.output_dir)
    now = datetime.now(UTC)
    manifest = RunManifestV1(
        run_id=run_dir.name,
        status=StageStatus.RUNNING,
        created_at=now,
        updated_at=now,
        input=RunInputV1(selector=_describe_input(args)),
        versions={
            "schema": SCHEMA_VERSION,
            "analysis_prompt": (
                f"{stage_02_analysis.PROMPT_VERSION}@{stage_02_analysis.PROMPT_HASH}"
            ),
            "memo_prompt": (
                f"{stage_03_recommendation.PROMPT_VERSION}@{stage_03_recommendation.PROMPT_HASH}"
            ),
            "model": config.openai_model or "unset",
            "reasoning_effort": config.openai_reasoning_effort or "default",
        },
        stages={name: StageRunV1() for name in _LABELS},
    )
    write_manifest(run_dir, manifest)
    append_log(run_dir, "run_started", selector=manifest.input.selector)
    _say(f"Run {manifest.run_id}", f"input: {manifest.input.selector}")

    try:
        succeeded = _run_stages(args, config, client, run_dir, manifest)
    except Exception as exc:
        append_log(
            run_dir, "run_crashed", error=type(exc).__name__, traceback=traceback.format_exc()
        )
        _say("Failed", f"{type(exc).__name__} · details in {display_path(run_dir)}/logs.jsonl")
        succeeded = False

    manifest.status = StageStatus.COMPLETED if succeeded else StageStatus.FAILED
    write_manifest(run_dir, manifest)
    append_log(run_dir, "run_finished", status=manifest.status.value)
    _say("Done" if succeeded else "Failed", f"{display_path(run_dir)}/ · {_elapsed(started)}")
    return 0 if succeeded else 1


def _run_stages(
    args: Namespace,
    config: PipelineConfig,
    client: StructuredOpenAIClient,
    run_dir: Path,
    manifest: RunManifestV1,
) -> bool:
    replay_stage = None
    if args.from_artifact is not None:
        replay_stage = _REPLAY_STAGES.get(args.from_artifact.name)
        if replay_stage is None or not args.from_artifact.is_file():
            return _reject(
                manifest,
                run_dir,
                ErrorCode.INVALID_INPUT,
                "replay needs an existing candidates.json or analyses.jsonl from a prior run",
            )
        manifest.input.parent_artifact = ArtifactRefV1(
            path=display_path(args.from_artifact),
            sha256=file_sha256(args.from_artifact),
        )

    if replay_stage == _ANALYSIS:
        analysis_set = _replay_analyses(args.from_artifact, run_dir, manifest)
    else:
        candidate_set = (
            _replay_candidates(args.from_artifact, run_dir, manifest)
            if replay_stage == _SOURCING
            else _source(args, config, run_dir, manifest)
        )
        if candidate_set is None:
            return False
        analysis_set = _analyze(candidate_set, client, run_dir, manifest)
    if analysis_set is None:
        return False
    return _recommend(analysis_set, client, run_dir, manifest)


def _source(
    args: Namespace,
    config: PipelineConfig,
    run_dir: Path,
    manifest: RunManifestV1,
) -> CandidateSetV1 | None:
    try:
        selector = stage_01_sourcing.SourcingSelectorV1(
            topic=args.topic,
            yc_batch=args.yc_batch,
            urls=args.urls,
        )
    except ValidationError as exc:
        _reject(manifest, run_dir, ErrorCode.INVALID_INPUT, exc.errors()[0]["msg"])
        return None
    _open(manifest.stages[_SOURCING], run_dir, _SOURCING)
    manifest.input.snapshot_path = display_path(args.snapshot)
    if args.snapshot.is_file():
        manifest.input.snapshot_sha256 = file_sha256(args.snapshot)
    candidate_set = stage_01_sourcing.run_sourcing(
        args.snapshot,
        run_dir / _SOURCING,
        selector,
        config.max_candidates,
    )
    return _finish_sourcing(candidate_set, StageStatus.COMPLETED, run_dir, manifest)


def _replay_candidates(
    source: Path,
    run_dir: Path,
    manifest: RunManifestV1,
) -> CandidateSetV1 | None:
    try:
        candidate_set = CandidateSetV1.model_validate_json(source.read_text(encoding="utf-8"))
    except ValidationError as exc:
        _reject(manifest, run_dir, ErrorCode.INVALID_ARTIFACT, _invalid_artifact(exc))
        return None
    _copy_artifact(source, run_dir / _SOURCING)
    if (sibling := source.with_name("source_refs.jsonl")).is_file():
        _copy_artifact(sibling, run_dir / _SOURCING)
    return _finish_sourcing(candidate_set, StageStatus.SKIPPED, run_dir, manifest)


def _finish_sourcing(
    candidate_set: CandidateSetV1,
    status: StageStatus,
    run_dir: Path,
    manifest: RunManifestV1,
) -> CandidateSetV1 | None:
    stage = manifest.stages[_SOURCING]
    stats = candidate_set.stats
    records = (*candidate_set.candidates, *candidate_set.incomplete_candidates)
    manifest.input.snapshot_captured_at = max(
        (record.source.captured_at for record in records), default=None
    )
    manifest.source_urls = _unique_urls(c.yc_profile_url for c in candidate_set.candidates)
    stage.summary = stats.model_dump()
    stage.errors = candidate_set.errors
    insufficient = any(
        error.code is ErrorCode.INSUFFICIENT_CANDIDATES for error in candidate_set.errors
    )
    _close(stage, StageStatus.FAILED if insufficient else status, run_dir, _SOURCING, manifest)
    verb = "replayed" if status is StageStatus.SKIPPED else "saved"
    _say(
        _LABELS[_SOURCING],
        f"{stats.eligible} eligible · {len(candidate_set.incomplete_candidates)} incomplete · "
        f"{stats.rejected} rejected · {verb} candidates.json",
    )
    if insufficient:
        _say(
            "Failed",
            f"{stats.eligible} of 10 required candidates qualify · "
            "widen the selector or refresh the snapshot",
        )
        return None
    return candidate_set


def _analyze(
    candidate_set: CandidateSetV1,
    client: StructuredOpenAIClient,
    run_dir: Path,
    manifest: RunManifestV1,
) -> AnalysisSetV1 | None:
    stage, label = manifest.stages[_ANALYSIS], _LABELS[_ANALYSIS]
    _open(stage, run_dir, _ANALYSIS)

    def report(index: int, total: int, name: str, status: str) -> None:
        _say(label, f"{index}/{total} {name} · {status}")
        append_log(
            run_dir, "candidate_analyzed", index=index, total=total, candidate=name, status=status
        )

    analysis_set = stage_02_analysis.run_analysis(
        candidate_set, run_dir / _ANALYSIS, client, report
    )
    responses = [analysis.response for analysis in analysis_set.analyses]
    _record_responses(stage, responses)
    manifest.source_urls = _unique_urls(
        [*manifest.source_urls, *(url for response in responses for url in response.source_urls)]
    )
    stage.summary = {"valid": len(analysis_set.analyses), "failed": len(analysis_set.errors)}
    stage.errors = analysis_set.errors
    config_error = next(
        (error for error in analysis_set.errors if error.code is ErrorCode.INVALID_CONFIG), None
    )
    failed = config_error is not None or not analysis_set.analyses
    _close(
        stage, StageStatus.FAILED if failed else StageStatus.COMPLETED, run_dir, _ANALYSIS, manifest
    )
    processed = len(analysis_set.analyses) + len(analysis_set.errors)
    _say(
        label,
        f"{processed}/{len(candidate_set.candidates)} complete · "
        f"{len(analysis_set.analyses)} valid · {len(analysis_set.errors)} failed",
    )
    if config_error is not None:
        _say("Failed", f"{config_error.message} · set it in .env")
        return None
    if not analysis_set.analyses:
        _say(
            "Failed", f"no valid analyses · see {display_path(run_dir)}/{_ANALYSIS}/analyses.jsonl"
        )
        return None
    return analysis_set


def _replay_analyses(
    source: Path,
    run_dir: Path,
    manifest: RunManifestV1,
) -> AnalysisSetV1 | None:
    try:
        analysis_set = stage_02_analysis.load_analyses(source)
    except ValidationError as exc:
        _reject(manifest, run_dir, ErrorCode.INVALID_ARTIFACT, _invalid_artifact(exc))
        return None
    _copy_artifact(source, run_dir / _ANALYSIS)
    _close(manifest.stages[_SOURCING], StageStatus.SKIPPED, run_dir, _SOURCING, manifest)
    stage = manifest.stages[_ANALYSIS]
    _record_responses(stage, [analysis.response for analysis in analysis_set.analyses])
    stage.summary = {"valid": len(analysis_set.analyses), "failed": len(analysis_set.errors)}
    stage.errors = analysis_set.errors
    _close(stage, StageStatus.SKIPPED, run_dir, _ANALYSIS, manifest)
    _say(
        _LABELS[_ANALYSIS],
        f"replayed {len(analysis_set.analyses)} valid · {len(analysis_set.errors)} failed",
    )
    if not analysis_set.analyses:
        _say("Failed", "replayed artifact has no valid analyses")
        return None
    return analysis_set


def _recommend(
    analysis_set: AnalysisSetV1,
    client: StructuredOpenAIClient,
    run_dir: Path,
    manifest: RunManifestV1,
) -> bool:
    stage, label = manifest.stages[_RECOMMENDATION], _LABELS[_RECOMMENDATION]
    _open(stage, run_dir, _RECOMMENDATION)

    def report(rank: int, total: int, name: str, status: str) -> None:
        _say(label, f"{rank}/{total} {name} · {status}")
        append_log(run_dir, "memo_rendered", rank=rank, total=total, candidate=name, status=status)

    result = stage_03_recommendation.run_recommendation(
        analysis_set, run_dir / _RECOMMENDATION, client, report
    )
    _record_responses(
        stage, [record.response for record in result.recommendations if record.response is not None]
    )
    calls = [record.recommendation for record in result.recommendations]
    memos = sum(record.memo_path is not None for record in result.recommendations)
    meeting = calls.count(Recommendation.TAKE_A_MEETING)
    watch = calls.count(Recommendation.WATCH)
    passed = calls.count(Recommendation.PASS)
    stage.summary = {
        "memos": memos,
        "render_failed": len(result.recommendations) - memos,
        "meeting": meeting,
        "watch": watch,
        "pass": passed,
    }
    stage.errors = result.errors
    config_error = next(
        (error for error in result.errors if error.code is ErrorCode.INVALID_CONFIG), None
    )
    status = StageStatus.FAILED if config_error is not None else StageStatus.COMPLETED
    _close(stage, status, run_dir, _RECOMMENDATION, manifest)
    _say(label, f"{memos} memos · {meeting} meeting · {watch} watch · {passed} pass")
    if config_error is not None:
        _say("Failed", f"{config_error.message} · set it in .env")
        return False
    return True


def _open(stage: StageRunV1, run_dir: Path, name: str) -> None:
    stage.status = StageStatus.RUNNING
    stage.started_at = datetime.now(UTC)
    append_log(run_dir, "stage_started", stage=name)


def _close(
    stage: StageRunV1,
    status: StageStatus,
    run_dir: Path,
    name: str,
    manifest: RunManifestV1,
) -> None:
    stage.status = status
    stage.finished_at = datetime.now(UTC)
    stage_dir = run_dir / name
    stage.artifacts = [
        artifact_ref(run_dir, path) for path in sorted(stage_dir.rglob("*")) if path.is_file()
    ]
    append_log(
        run_dir,
        "stage_finished",
        stage=name,
        status=status.value,
        summary=stage.summary,
        errors=len(stage.errors),
    )
    write_manifest(run_dir, manifest)


def _reject(manifest: RunManifestV1, run_dir: Path, code: ErrorCode, message: str) -> bool:
    manifest.errors.append(ErrorRecordV1(code=code, message=message, stage="cli"))
    append_log(run_dir, "input_rejected", code=code.value, message=message)
    _say("Failed", message)
    return False


def _record_responses(stage: StageRunV1, responses: list[OpenAIResponseMetadataV1]) -> None:
    stage.response_ids = [response.response_id for response in responses]
    stage.usage = TokenUsageV1(
        input_tokens=sum(response.usage.input_tokens for response in responses),
        output_tokens=sum(response.usage.output_tokens for response in responses),
        total_tokens=sum(response.usage.total_tokens for response in responses),
    )
    stage.latency_ms = sum(response.latency_ms for response in responses)


def _copy_artifact(source: Path, stage_dir: Path) -> None:
    stage_dir.mkdir(parents=True, exist_ok=True)
    copyfile(source, stage_dir / source.name)


def _describe_input(args: Namespace) -> str:
    if args.from_artifact is not None:
        return f"replay={display_path(args.from_artifact)}"
    try:
        return stage_01_sourcing.SourcingSelectorV1(
            topic=args.topic, yc_batch=args.yc_batch, urls=args.urls
        ).summary()
    except ValidationError:
        return "invalid selector"


def _invalid_artifact(exc: ValidationError) -> str:
    return f"replay artifact is invalid: {exc.errors()[0]['msg']}"


def _unique_urls(urls: Iterable[HttpUrl]) -> list[HttpUrl]:
    return list({str(url): url for url in urls}.values())


def _elapsed(started: float) -> str:
    seconds = round(monotonic() - started)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _say(label: str, message: str) -> None:
    print(f"{label:<21}{message}", flush=True)
