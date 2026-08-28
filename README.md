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
uv run investment-pipeline snapshot                    # capture the current YC batch into inputs/
uv run investment-pipeline run --topic B2B
uv run investment-pipeline run --yc-batch "Summer 2026"
uv run investment-pipeline run --url https://www.ycombinator.com/companies/<slug>
uv run investment-pipeline run --from-artifact outputs/<run_id>/01_sourcing/candidates.json
```

Stage 01 reads `inputs/yc_snapshot.jsonl` (override with `--snapshot`); see
[inputs/README.md](inputs/README.md) for the snapshot contract. Every invocation writes a new
`outputs/<run_id>/` containing `manifest.json`, `logs.jsonl`, and one directory per stage; runs
are never overwritten. `--from-artifact` replays downstream stages from a prior run's
`01_sourcing/candidates.json` or `02_analysis/analyses.jsonl` as a new run linked to its parent.

## Representative runs

Committed runs from the Summer 2026 snapshot (`MAX_CANDIDATES=10`, `gpt-5`, low reasoning effort):

| Run | Command | Result |
|---|---|---|
| [`20260827T213043Z`](outputs/20260827T213043Z/) | `run --topic B2B` | 10 analyses, 10 memos: 0 meeting, 5 watch, 5 pass · [ranked index](outputs/20260827T213043Z/03_recommendation/index.md) · [evals report](evals/reports/20260827T213043Z.json) |
| [`20260827T214810Z`](outputs/20260827T214810Z/) | `run --from-artifact …/213043Z/02_analysis/analyses.jsonl` | Stage 02 replayed, memos re-rendered only |
| [`20260827T214813Z`](outputs/20260827T214813Z/) | `run --from-artifact …/213043Z/01_sourcing/candidates.json` | Stage 01 replayed, analysis and memos regenerated |
| [`20260827T214901Z`](outputs/20260827T214901Z/) | `run --topic "AI agents for SMBs"` | honest failure: 0 literal matches, `INSUFFICIENT_CANDIDATES`, partial run preserved |
| [`20260827T214905Z`](outputs/20260827T214905Z/) | `run --topic "AI agents"` | partner-style topic run |
| [`20260827T214907Z`](outputs/20260827T214907Z/) | `run --topic "developer tools"` | partner-style topic run |
| [`20260827T214909Z`](outputs/20260827T214909Z/) | `run --topic healthcare` | partner-style topic run |

### Trace one startup end to end

Rapidfolio, rank 1 of the B2B run (72/100, Watch):

1. Source record: `inputs/yc_snapshot.jsonl` line `"source_record_id":"rapidfolio"`, captured from the YC profile <https://www.ycombinator.com/companies/rapidfolio> (provenance in `inputs/yc_snapshot.provenance.json`).
2. Candidate: `outputs/20260827T213043Z/01_sourcing/candidates.json`, `candidate_id: rapidfolio`, eligible via `is_current_batch`.
3. Analysis: the `rapidfolio` line of `outputs/20260827T213043Z/02_analysis/analyses.jsonl` — every finding cites `evidence_ids`; every evidence item carries its `source_url` and `self_reported` label; `dimension_scores` sum to `total_score: 72`, `evidence_coverage: 100`.
4. Call: `outputs/20260827T213043Z/03_recommendation/recommendations.json`, rank 1 → `Watch` (score ≥ 55, coverage 100, no critical risk, but below the 75 needed for a meeting).
5. Memo: [`outputs/20260827T213043Z/03_recommendation/memos/rapidfolio.md`](outputs/20260827T213043Z/03_recommendation/memos/rapidfolio.md) — each bullet links its evidence back to step 3.

## Checks and evals

```bash
uv run pytest                                        # offline, deterministic
uv run ruff check .
uv run mypy src tests evals
uv run investment-evals outputs/<run_id>             # deterministic graders; report in evals/reports/
uv run investment-evals outputs/<run_id> --semantic  # adds the model judge; needs OPENAI_API_KEY and OPENAI_MODEL
LIVE_SMOKE=1 uv run pytest tests/test_live_smoke.py  # one live structured-output call; skipped otherwise
```

Tests verify deterministic software behavior with OpenAI mocked. Evals grade a finished run's
artifacts: grounding of every evidence URL, rank and call consistency with the policy,
missing-data honesty, and memo structure, citations, and length. The optional semantic judge
rates thesis adherence, faithfulness, clarity, risk quality, and specificity per memo.
