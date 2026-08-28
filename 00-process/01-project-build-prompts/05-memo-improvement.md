# Memo Improvement: Prompt 1

## Role

You are the same senior Python and AI systems engineer who implemented the pipeline. Improve the
one-page memo so a partner reads it top-down, sees how the score was built, and can click through
to the exact evidence. Work in the same chunked, reviewable workflow with Ponytail active.

## Context

Read `AGENTS.md`, the thesis, the architecture document, `src/investment_pipeline/stage_03_recommendation/`,
`evals/graders.py`, and two committed memos (`outputs/20260827T213043Z/03_recommendation/memos/rapidfolio.md`
and `.../datoric.md`) before planning.

Observed problems in the committed memos:

- The call (`Pass` / `Watch` / `Take a meeting`) is the last line. A partner wants the decision first.
- Only the total score is shown. The five pillar scores exist in `analyses.jsonl` but the reader
  cannot see how the total was composed or where evidence was missing.
- Citations often land on a generic page (the YC profile, the company homepage) instead of the
  specific page the claim came from, and nothing checks that a cited link is live.

## Required changes

### 1. Call first

- The memo opens with the company name and the recommendation on the first lines, followed by the
  total score and evidence coverage.
- Keep the recommendation line exact and machine-checkable so tests and the memo grader still parse
  it; move their "last line" checks to the header.

### 2. Pillar scores above the rationale

- Render a compact table of the five thesis dimensions directly above `## Rationale`: dimension,
  score, maximum (25/25/20/15/15), and a link to the evidence ids that support it.
- A `null` score renders as `unknown`, never as `0`; the table must make missing evidence visible.
- Rendering stays deterministic Python from `AnalysisRecordV1`; the model does not write the table.

### 3. Exact, verified citations

- Stage 02 prompt: every evidence item must cite the most specific page where the claim appears (the
  pricing page, the docs page, the founder's YC profile section, the news article), not the site
  root, unless the claim itself is about the root page.
- Verification step in Stage 02, deterministic and stdlib-only: request every evidence URL and
  record the HTTP status and check time on the evidence item. A URL that is unreachable or returns
  4xx/5xx is rejected with the exact reason; the repair retry asks the model to replace or drop that
  evidence. If the repaired output still cites a broken URL, the candidate analysis fails honestly.
- Stage 03 may cite only evidence marked verified. No memo may contain an unverified or broken link.
- The evals grader gains a `citations` check: every link in every memo resolves to a verified
  evidence item and the memo cites the most specific verified URL available for that evidence.

## Constraints

- Do not change score weights, recommendation gates, or the top-decile rule.
- Keep the 350-word limit and the 60-second read; the pillar table counts toward it.
- Version the changed prompts (`analysis-v2`, `memo-v2`) and the memo format so manifests
  distinguish old runs from new ones. Committed runs stay as they are.
- Update tests, graders, README trace, and the process trail with each chunk. No commits or pushes.

## Design notes to accept or strike

- Pillar table: agreed it helps, with one condition: keep it to five rows and one line each, so the
  rationale is still visible without scrolling. Percentages are not needed; `18/25` reads faster.
- Link verification checks reachability, not content. Sites behind bot protection can return 403 to
  a plain request while working in a browser; treat 403 as "unverified, keep out of the memo" and
  record it, rather than failing the whole analysis on it. Content verification (does the page say
  what the claim says) is a semantic-judge question, not a deterministic one.
- URL fragments (`#pricing`) cannot be verified beyond the page; allow them only when the page
  itself verifies.
- Verification adds one request per evidence item (roughly 10 to 20 per candidate). Run them with a
  short timeout and in one pass after parsing, before the repair decision.

## Acceptance

1. Every new memo: call in the header, pillar table above the rationale, all links verified.
2. `investment-evals` reports zero `citations` findings on a fresh run.
3. Old committed runs still load and grade under the old format.
4. pytest, Ruff, mypy pass; the process trail records the memo format decision.
