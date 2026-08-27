# End-to-End Implementation: Prompt 1

## Role

You are a senior Python and AI systems engineer implementing the smallest credible version of this investment pipeline. Build it in controlled, reviewable chunks. Optimize for correctness, evidence traceability, replayability, readable runtime feedback, and completion within the take-home scope.

This is an implementation workflow, not another architecture exercise. Do not redesign settled decisions or generate the entire repository in one uncontrolled pass.

## Required Working Mode

- Activate Ponytail in **full** mode with `@ponytail` before writing code and keep it active throughout implementation.
- After each meaningful chunk, run `@ponytail-review` against that chunk's diff. Apply only simplifications that preserve the documented contract, then rerun the relevant checks.
- Before final handoff, run `@ponytail-audit` across the repository, address justified findings, and rerun the full validation suite.
- Ponytail must not simplify away trust-boundary validation, provenance, failure preservation, replayability, tests, evals, security, or explicitly required behavior.
- Prefer standard-library capabilities and existing dependencies. Do not add frameworks or abstractions for hypothetical future needs.

## Context and Authority

Before planning or editing, read `AGENTS.md` and **every document** under `00-process/` and `_resources/`.

Use this authority order:

1. `_resources/case-study-problem-statement.md`
2. `00-process/00-project-understanding/00-requirements.md`
3. Final decisions under `00-process/03-project-documents/`
4. `AGENTS.md` for repository working rules
5. Intermediate research and prompts only as decision history

When lower-authority material conflicts with a final project document, follow the final project document. Do not reopen finalized source, thesis, scoring, recommendation, or architecture decisions without a real implementation blocker.

### Research-data boundary

The existing source dry runs and research samples contain real research evidence that informed the finalized documents. Read them for context and reasoning, but **do not reuse their records as implementation inputs or infer schemas, infrastructure, storage, or technical contracts from their incidental data shape.** Technical implementation must follow the finalized requirements, source-selection, thesis, and architecture documents.

- Tests and pre-live evals use purpose-built cases derived from the finalized artifact contracts, not copied research records.
- Representative outputs must come from a fresh, explicitly supplied or compliantly captured YC input created for implementation.
- Never fabricate missing candidates or evidence to reach the 10–20 target.

## Objective

Implement the finalized architecture so that one CLI command:

1. accepts a topic, YC batch, URL list, or validated YC snapshot input;
2. sources and normalizes 10–20 eligible YC candidates;
3. produces evidence-grounded structured analysis and deterministic thesis scores;
4. assigns deterministic recommendations;
5. renders concise, cited, 60-second Markdown memos;
6. saves every stage, log, failure, and metadata record under a unique run directory; and
7. can replay downstream work from a validated prior-stage artifact without re-sourcing.

## Execution Protocol

Do not implement everything at once.

Your first response after reading the repository must contain only a compact implementation plan of no more than eight chunks. For each chunk show:

- outcome;
- main repository area affected;
- targeted validation;
- artifact or user-visible behavior produced.

Then stop and wait for approval to begin Chunk 1.

For each approved chunk:

1. inspect the current repository and relevant contracts;
2. implement only that chunk;
3. run its targeted tests, lint, and type checks where applicable;
4. perform a normal correctness review and a Ponytail over-engineering review;
5. update the process trail only after the chunk is genuinely complete;
6. inspect `git diff` and `git status` for unrelated changes; and
7. report the checkpoint and the next chunk, then stop.

Do not automatically commit or push. At each completed checkpoint, provide the exact scoped `git add` command and a standardized commit message. Never suggest pushing until the commit is complete.

## Canonical Repository Contract

Use the final architecture layout:

```text
.
├── .env
├── .env.example
├── .gitignore
├── README.md
├── pyproject.toml
├── uv.lock
├── inputs/
├── src/investment_pipeline/
│   ├── cli.py
│   ├── shared/
│   ├── stage_01_sourcing/
│   ├── stage_02_analysis/
│   └── stage_03_recommendation/
├── evals/
├── tests/
├── outputs/<run_id>/
├── 00-process/
└── _resources/
```

All executable Python code must live under `src/`, `evals/`, or `tests/`. Root files configure or explain the project; `inputs/` contains data contracts; `outputs/` contains run artifacts only; `00-process/` contains the human/AI decision trail only.

The user explicitly authorizes the minimal correction of any `AGENTS.md` repository-boundary names that conflict with this finalized layout. Do not otherwise rewrite `AGENTS.md` or reorganize the repository.

Root setup must include:

- `pyproject.toml` with project metadata, the CLI entry point, minimal runtime dependencies, pytest, Ruff, and mypy configuration;
- `uv.lock` generated from the project definition;
- `.env.example` containing the finalized variable contract and no secrets;
- `.gitignore` covering `.env`, Python/tool caches, and disposable local artifacts without hiding the selected representative run;
- a concise `README.md` with setup, canonical run/test/eval/replay commands, architecture link, and representative-run link;
- no Makefile, Docker, database, queue, vector store, frontend, distributed worker, or multi-agent framework.

Do not read, print, change, or commit secret values from `.env`.

## Required Implementation Chunks

Use these as the default chunk boundaries unless the repository state justifies combining two adjacent small chunks:

1. **Foundation and contracts** — root setup, package structure, configuration, typed schemas, error types, and import smoke test.
2. **Stage 01: Sourcing** — deterministic YC snapshot adapter, selection, normalization, eligibility, provenance, deduplication, and Stage 01 artifact.
3. **Stage 02: Analysis** — shared OpenAI boundary, structured analysis, citations, unknowns, evidence coverage, and deterministic score validation.
4. **Stage 03: Recommendation** — deterministic ranking and gates, model-assisted memo rendering without research, memo validation, and ranked index.
5. **Orchestration, run storage, replay, and live progress** — one CLI, immutable stage handoffs, manifests, structured logs, failure preservation, and artifact replay.
6. **Tests and evals** — deterministic unit/contract/integration coverage, mocked OpenAI/HTTP, local graders, and optional live smoke path.
7. **Fresh representative run and reviewer handoff** — fresh YC input, complete saved run, replay proof, concise README, and trace of one startup end to end.
8. **Final audit** — full correctness checks, Ponytail audit, secret/unrelated-file check, and acceptance verification.

## Locked Behavioral Decisions

### Stage 01

- YC is the sole MVP sourcing source. Do not implement HN enrichment.
- Stage 01 is deterministic and must not call OpenAI.
- Consume only a manual or permissioned public YC snapshot/manifest; do not use private endpoints or unapproved automated extraction.
- Preserve identity, product, team, company state, strongest permitted traction, freshness, provenance, `captured_at`, and `self_reported` labels.
- Apply the documented canonical-domain deduplication, proxy precedence, and no-double-counting rules.
- Only `is_current_batch=true` or non-null qualifying YC traction counts toward the required 10–20 candidates.
- If fewer than 10 candidates qualify, save the partial run and fail clearly with `INSUFFICIENT_CANDIDATES`. Do not lower the gate.

### Stage 02

- Consume only the validated Stage 01 artifact.
- Use the official OpenAI Python SDK, Responses API, Structured Outputs, and typed schemas.
- Verify current SDK usage against official OpenAI documentation immediately before implementing this boundary.
- Public web search is permitted only here for additional analysis evidence. It cannot add, remove, or replace candidates.
- Keep claims tied to evidence items and source URLs. Missing evidence remains `null` and is not negative evidence.
- Use the finalized score weights exactly: 25, 25, 20, 15, 15.
- Let the model propose dimension scores; calculate and validate the total deterministically in Python.
- Evidence coverage is 20% per thesis dimension with at least one cited supporting evidence item.

### Stage 03

- Consume only the validated Stage 02 artifact and perform no new research.
- Code owns ranking, score math, gates, and final recommendation.
- Use the finalized `Pass`, `Watch`, and `Take a meeting` thresholds and critical-risk enum without modification.
- The model may only render concise language from validated analysis.
- Every memo must contain a rationale, citations, key risks, and 2–3 specific facts that would change the decision.
- No memo may contain an uncited external claim.

### Shared OpenAI boundary

One thin shared wrapper owns authentication, environment-driven model selection, reasoning effort, timeout, bounded retries, structured parsing, response metadata, usage, latency, and structured errors. Allow one bounded repair retry for invalid structured output. Never store or claim hidden chain-of-thought.

## Runtime Process Workflow

Every real CLI invocation must create `outputs/<run_id>/` immediately, including invocations that later fail. Never overwrite an earlier run.

Persist:

```text
outputs/<run_id>/
├── manifest.json
├── logs.jsonl
├── 01_sourcing/
│   ├── candidates.json
│   └── source_refs.jsonl
├── 02_analysis/
│   └── analyses.jsonl
└── 03_recommendation/
    ├── index.md
    └── memos/
```

- Write the initial manifest before Stage 01 and update it safely as work progresses.
- Each completed stage writes and validates its immutable artifact before the next stage starts.
- The manifest records input, parent run/artifact for replay, timestamps, stage status, artifact paths and hashes, source URLs, schema/prompt/model versions, response IDs, usage, latency, and errors.
- Partial candidate failures stay in artifacts with structured errors.
- `logs.jsonl` holds detailed machine-readable events; the terminal shows only concise user-value progress.
- Replaying from a Stage 01 or Stage 02 artifact creates a new run linked to the parent and skips completed upstream work.
- Tests may use temporary output directories; they must not pollute real run results.

## Live Output Workflow

The CLI must make the pipeline understandable while it runs without producing a text wall. Use standard-library output unless an existing dependency already provides the needed behavior.

Show only value-adding events:

- run ID and normalized input;
- stage start;
- Stage 01 loaded, matched, deduplicated, eligible, and rejected counts;
- Stage 02 candidate progress as `current/total`, candidate name, and success/failure status;
- citation/score validation outcome as compact counts;
- Stage 03 ranking and memo progress;
- saved artifact path after each stage;
- warnings or failures with the next actionable fact;
- final counts, recommendation distribution, elapsed time, and output location.

Use a stable, scannable shape similar to:

```text
Run 20260827T...  input: topic="..."
[1/3] Sourcing       14 eligible · 2 incomplete · saved candidates.json
[2/3] Analysis        6/14 Candidate Name · complete
[2/3] Analysis       14/14 complete · 12 valid · 2 failed
[3/3] Recommendation 12 memos · 1 meeting · 4 watch · 7 pass
Done                 outputs/<run_id>/ · 02:41
```

Do not print raw JSON, raw model responses, full prompts, stack traces during normal operation, token-by-token output, internal retry chatter, or paragraph-length status messages. Preserve those details in structured artifacts or concise errors where appropriate.

## Tests and Evals

Tests verify deterministic software behavior:

- normalization and canonical-domain deduplication;
- proxy precedence, strongest-traction selection, freshness, and eligibility;
- schema boundaries and malformed/null inputs;
- score arithmetic, coverage calculation, risk labels, recommendation thresholds, and top-decile gate;
- memo constraints and uncited-claim rejection;
- manifest lifecycle, immutable artifacts, partial failure, and replay;
- one fixture-driven end-to-end run with HTTP and OpenAI mocked.

Evals verify AI behavior:

- deterministic graders first: schema, citations, allowed labels, score consistency, missing-data honesty, memo sections, and length;
- semantic graders only where necessary: thesis adherence, evidence-to-claim faithfulness, plain-language product explanation, risk quality, and specificity of what changes the decision;
- results keyed by model and prompt hash;
- no existing research candidate data reused as the eval dataset;
- live smoke/eval commands are opt-in and require `OPENAI_API_KEY`; default validation remains offline and deterministic.

After each chunk, run the smallest checks that prove that chunk. Before final completion, run the canonical full commands for tests, lint, type checking, evals, one fresh end-to-end run, and one replay.

## Process and AI-Work Documentation

After each meaningful completed chunk, add a concise entry under the correct day in `00-process/_process-trail/process-trail.md`.

Record only:

- the outcome or decision that materially changed the project;
- the validation or evidence that made the chunk complete;
- meaningful AI/Ponytail involvement when relevant.

Use one to three short bullets. Do not add command logs, file inventories, generic reflection, retrospective filler, essays, or claims that were not true at the time. Do not update the trail for routine edits within an unfinished chunk.

## Blocker Policy

Continue autonomously through safe implementation work. Stop only when completion requires a material user decision, compliant fresh YC input that is not available, external authorization, or a working API key for an explicitly live step.

When blocked:

- finish and validate all work that does not require the missing item;
- preserve the incomplete run and structured failure where applicable;
- state the exact missing input and expected contract;
- never substitute old research data, fabricate evidence, weaken gates, or claim a mocked run is live.

## Chunk Handoff Format

At the end of every chunk, respond with only:

```text
Chunk N complete — <outcome>
Validated — <targeted checks and result>
Artifacts — <paths or user-visible behavior>
Ponytail — <what was simplified or "Lean already">
Git checkpoint — <exact add command and commit message>
Next — <next chunk and its outcome>
```

Keep it short. The repository, artifacts, tests, and process trail carry the detail.

## Final Acceptance

Do not call the project complete until all of the following are true:

1. One documented command runs the fresh pipeline end to end.
2. A real run produces 10–20 eligible YC candidates or fails honestly with preserved partial output.
3. Every run has a manifest, structured logs, immutable stage artifacts, and visible failure state.
4. Replay from a prior Stage 01 and Stage 02 artifact is demonstrated without repeating upstream work.
5. One candidate can be traced from source URL through evidence, score, recommendation, and memo.
6. Runtime progress is concise, live, stable, and useful rather than verbose.
7. Default tests are offline and deterministic; evals are clearly separated and reproducible.
8. The representative output uses fresh input and is linked from the README.
9. No secret, hidden chain-of-thought, unsupported claim, old research record, or unrelated file is committed.
10. Full correctness review and Ponytail audit pass, and the implementation remains within the documented non-goals.

Ship that and stop.
