# AI-Augmented Investment Pipeline

A small, replayable Python pipeline for sourcing YC companies, analyzing them against the
[B2B adoption thesis](00-process/03-project-documents/01-thesis.md), and producing cited
investment memos. The finalized design is in the [architecture document](00-process/03-project-documents/02-architecture.md).

## Setup

```bash
cp .env.example .env
uv sync --dev
```

Chunk 1 establishes the package, configuration, and versioned artifact contracts. The runnable
pipeline and representative output are added in later implementation chunks.

```bash
uv run investment-pipeline --help
uv run pytest
uv run ruff check .
uv run mypy src tests
```
