"""Run directories, manifests, and structured logs shared by the CLI orchestration."""

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from time import sleep

from pydantic import JsonValue

from investment_pipeline.shared.schemas import ArtifactRefV1, RunManifestV1


def create_run_dir(output_dir: Path) -> Path:
    """Create a never-reused run directory named by UTC time, suffixed on collision."""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    attempt = 1
    while True:
        run_dir = output_dir / (stamp if attempt == 1 else f"{stamp}-{attempt}")
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            attempt += 1
        else:
            return run_dir


def display_path(path: Path) -> str:
    """Repo-relative POSIX path; a path outside the working directory keeps only its name."""
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.name


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def artifact_ref(run_dir: Path, path: Path) -> ArtifactRefV1:
    return ArtifactRefV1(path=path.relative_to(run_dir).as_posix(), sha256=file_sha256(path))


def write_manifest(run_dir: Path, manifest: RunManifestV1) -> None:
    """Replace manifest.json atomically so a crash never leaves a half-written manifest."""
    manifest.updated_at = datetime.now(UTC)
    staged = run_dir / "manifest.json.tmp"
    staged.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
    for attempt in range(5):
        try:
            staged.replace(run_dir / "manifest.json")
            return
        except PermissionError:
            # ponytail: Windows scanners lock fresh files for a moment; retry briefly, then fail.
            if attempt == 4:
                raise
            sleep(0.1 * (attempt + 1))


def append_log(run_dir: Path, event: str, **fields: JsonValue) -> None:
    record = {"at": datetime.now(UTC).isoformat(), "event": event, **fields}
    with (run_dir / "logs.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, default=str) + "\n")
