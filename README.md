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
| [`20260827T214909Z`](outputs/20260827T214909Z/) | `run --topic healthcare` | 10 memos: 0 meeting, 4 watch, 6 pass |
| [`20260827T222312Z`](outputs/20260827T222312Z/) | `run --topic "AI agents"` | 9 memos (1 analysis rejected for an unsupported URL): 0 meeting, 4 watch, 5 pass |
| [`20260827T222314Z`](outputs/20260827T222314Z/) | `run --topic "developer tools"` | 9 memos (1 analysis rejected for dangling evidence ids): 1 meeting, 6 watch, 2 pass |
| [`20260828T062642Z`](outputs/20260828T062642Z/) | `run --topic B2B` (memo-v2, verified links) | 9 memos (1 analysis rejected: a rate-limited link, since reclassified as unverified): 0 meeting, 6 watch, 3 pass · 128 of 130 links verified · [evals report](evals/reports/20260828T062642Z.json) |

Every run has an [evals report](evals/reports/). The B2B run passes all deterministic graders; the
two later topic runs carry `memos` findings for one company each whose citation labels are raw URLs,
a prompt gap fixed after those runs started (evidence ids are now constrained to short tokens).
Rejected analyses stay in `02_analysis/analyses.jsonl` as error records with the validation reason.

### Trace one startup end to end

Rapidfolio, rank 1 of the memo-v2 B2B run (69/100, Watch):

1. Source record: `inputs/yc_snapshot.jsonl` line `"source_record_id":"rapidfolio"`, captured from the YC profile <https://www.ycombinator.com/companies/rapidfolio> (provenance in `inputs/yc_snapshot.provenance.json`).
2. Candidate: `outputs/20260828T062642Z/01_sourcing/candidates.json`, `candidate_id: rapidfolio`, eligible via `is_current_batch`.
3. Analysis: the `rapidfolio` line of `outputs/20260828T062642Z/02_analysis/analyses.jsonl` — every finding cites `evidence_ids`; every evidence item carries its `source_url`, `self_reported` label, and the `http_status` / `verified_at` recorded when the link was requested; `dimension_scores` sum to `total_score: 69`, `evidence_coverage: 100`.
4. Call: `outputs/20260828T062642Z/03_recommendation/recommendations.json`, rank 1 → `Watch` (score ≥ 55, coverage 100, no critical risk, but below the 75 needed for a meeting).
5. Memo: [`outputs/20260828T062642Z/03_recommendation/memos/rapidfolio.md`](outputs/20260828T062642Z/03_recommendation/memos/rapidfolio.md) — call first, pillar table, then rationale; every link resolves to a verified evidence item from step 3. The same company under the earlier format: [`20260827T213043Z`](outputs/20260827T213043Z/03_recommendation/memos/rapidfolio.md) (72/100 — run-to-run score variance is visible here).

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
missing-data honesty, memo structure and length, and citations (every memo link is evidence whose
URL verified during Stage 02). The optional semantic judge rates thesis adherence, faithfulness,
clarity, risk quality, and specificity per memo.

## Memo format (memo-v3)

Top-down for a 60-second read: the call under the company name, then score and evidence coverage,
then a five-row pillar table (each pillar shown out of 100 for readability — the weighted raw
scores stay in `analyses.jsonl` — `unknown` when evidence was missing, links to the evidence),
then rationale, key risks, and the two or three questions that would change the decision. Every link in a memo was requested during Stage 02 (`http_status` and `verified_at` are
stored on the evidence item); evidence whose link did not verify is kept in the analysis but never
cited in the memo. Runs before `20260828` use the earlier format with the call as the last line.
