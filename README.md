# AI-Augmented Investment Pipeline

A small, replayable Python pipeline for sourcing YC companies, analyzing them against the
[B2B adoption thesis](00-process/03-project-documents/01-thesis.md), and producing cited
investment memos. The finalized design is in the [architecture document](00-process/03-project-documents/02-architecture.md).

## Setup

```bash
cp .env.example .env
uv sync --dev
```

Set `OPENAI_API_KEY` and `OPENAI_MODEL` in `.env`; see `.env.example` for every variable.

## Run

```bash
uv run investment-pipeline run --topic "AI agents for SMBs"
uv run investment-pipeline run --yc-batch "Summer 2026"
uv run investment-pipeline run --url https://www.ycombinator.com/companies/<slug>
uv run investment-pipeline run --from-artifact outputs/<run_id>/01_sourcing/candidates.json
```

Stage 01 reads `inputs/yc_snapshot.jsonl` (override with `--snapshot`); see
[inputs/README.md](inputs/README.md) for the snapshot contract. Every invocation writes a new
`outputs/<run_id>/` containing `manifest.json`, `logs.jsonl`, and one directory per stage; runs
are never overwritten. `--from-artifact` replays downstream stages from a prior run's
`01_sourcing/candidates.json` or `02_analysis/analyses.jsonl` as a new run linked to its parent.
The representative run is added in a later chunk.

## Checks

```bash
uv run pytest
uv run ruff check .
uv run mypy src tests
```
