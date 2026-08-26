# Architecture: Prompt 1

## Role

You are a senior Python and AI systems architect. Design the smallest credible architecture for this take-home project. Optimize for clarity, replayability, evidence traceability, and implementation within the stated 6–8 hour scope.

## Context

Read **every document** under `00-process/` and `_resources/` before writing. Use this authority order:

1. `_resources/case-study-problem-statement.md`
2. `00-process/00-project-understanding/00-requirements.md`
3. Final decisions in `00-process/03-project-documents/`
4. Intermediate research, dry runs, prompts, and process trail as supporting context

Do not rewrite the requirements, source research, or thesis. Translate them into a buildable system design.

## Task

Create a minimal but functional architecture document that a reviewer can understand in **two minutes**. It must show exactly how one command becomes 10–20 sourced candidates, structured thesis analysis, and one-page recommendation memos.

This is an architecture document, not implementation. Make decisions; do not list multiple architecture options.

## Locked Decisions

- Language: **Python**.
- AI stack: official **OpenAI Python SDK**, using the **Responses API** and **Structured Outputs** with typed schemas.
- Verify current SDK, Responses API, structured-output, web-search, and eval guidance against official OpenAI documentation before finalizing.
- No frontend, database, vector database, queue, distributed workers, or multi-agent framework.
- One local CLI command must run the pipeline end to end.
- Data handoffs are versioned JSON/JSONL and Markdown files committed for a representative run.
- YC is the primary sourcing source. HN is optional enrichment and must never be a required join.
- Do not assume YC provides a documented directory API or design around private endpoints. Isolate acquisition behind a source adapter and state the compliant MVP acquisition assumption.
- Missing evidence remains `null`; it is not negative evidence.

## Mandatory Source Layout

Show these three sibling stage packages under one importable package inside `src/`:

```text
src/
└── investment_pipeline/
    ├── stage_01_sourcing/
    ├── stage_02_analysis/
    ├── stage_03_recommendation/
    ├── shared/
    └── cli.py
```

Use these exact Python-import-safe stage names. Enforce forward-only dependencies:

```text
CLI → Stage 01 → artifact → Stage 02 → artifact → Stage 03 → memos
                    ↘ shared schemas/config/provenance ↗
```

No stage may reach into another stage's internals. It may consume only the previous stage's validated artifact contract.

## Stage Responsibilities

### `stage_01_sourcing`

- Accept one of: topic query, YC batch, or URL list.
- Return 10–20 normalized candidates from YC; optionally attach exact-domain HN evidence.
- Normalize identity, product, team, company state, traction, freshness, and provenance fields defined by the final source-selection document.
- Apply canonical-domain deduplication, proxy rules, no-double-counting, `self_reported` labels, and `captured_at`.
- Persist raw/source references and `01_sourcing/candidates.json`.
- Fail visibly per candidate; do not discard the full run because one profile is incomplete.

### `stage_02_analysis`

- Consume only the Stage 01 contract.
- Use the OpenAI Responses API for evidence-grounded analysis of team, product, market, competitive landscape, why now, risks, and open questions.
- Use public web search only here when additional market evidence is required; retain returned source URLs beside claims.
- Produce typed structured output before rendering prose.
- Score the finalized thesis dimensions exactly:
  - Product Adoption: 25
  - Workflow Habit and Importance: 25
  - Employee-to-Team Expansion: 20
  - Enterprise Procurement Path: 15
  - Founder Execution Fit: 15
- Let the model propose dimension scores with evidence; calculate and validate the 0–100 total deterministically in Python.
- Persist `02_analysis/analyses.jsonl`, including evidence coverage, unknowns, model/prompt version, and citations.

### `stage_03_recommendation`

- Consume only the Stage 02 contract; perform no new research.
- Rank candidates and apply a deterministic recommendation policy for `Pass`, `Watch`, or `Take a meeting`.
- Permit `Take a meeting` only for the strongest 10–20% when score, evidence coverage, and risk gates pass.
- Use the model only to render concise partner-ready language; code owns score math, ranking, and final call.
- Produce one Markdown memo per startup, readable in 60 seconds, with rationale, citations, key risks, and 2–3 facts that would change the decision.
- Persist memos under `03_recommendation/memos/` plus a ranked `index.md`.

## Root and Runtime Contract

The architecture tree must make these root responsibilities obvious:

- `.env`: local secrets/configuration; root-level and gitignored.
- `.env.example`: committed variable contract with no secrets.
- `README.md`: two-minute entry point with setup, commands, and one end-to-end output link.
- `.gitignore`: excludes `.env`, caches, and uncommitted local runs without hiding representative outputs.
- `pyproject.toml`: project metadata, dependencies, CLI entry point, pytest, lint, and type-check configuration.
- Lockfile: reproducible dependency versions.
- `src/`: application code with the three required stages.
- `tests/`: deterministic code and contract tests.
- `evals/`: model-output datasets, graders, and reports; not a second application.
- `outputs/<run_id>/`: stage artifacts, memos, logs, and manifest.
- `00-process/`: visible human/AI decision trail.
- `_resources/`: supplied reference material.

Show one canonical run command, one test command, and one eval command. Prefer `uv` with `pyproject.toml`; do not introduce Make, Docker, or another wrapper unless essential.

The root `.env.example` must define, at minimum:

```text
OPENAI_API_KEY=
OPENAI_MODEL=
OPENAI_REASONING_EFFORT=
REQUEST_TIMEOUT_SECONDS=
MAX_CANDIDATES=
OUTPUT_DIR=
ENABLE_HN_ENRICHMENT=
```

Do not hardcode a model name in code or architecture.

## OpenAI Boundary

Require one shared, thin OpenAI client wrapper that owns authentication, timeout, bounded retries, model configuration, response parsing, usage capture, and structured failures.

- Stage 01 is deterministic and does not call OpenAI.
- Stage 02 may call Responses API plus web search and must return typed analysis objects with citations.
- Stage 03 may call Responses API without tools to render memos from validated analysis.
- Prompts are versioned files or constants beside the consuming stage.
- Persist model, prompt version/hash, response ID, token usage, latency, and error status in the run manifest.
- Never persist or claim hidden chain-of-thought.

## Tests and Evals

Keep the distinction explicit:

### Tests verify code

- Unit tests: normalization, domain deduplication, proxy precedence, freshness, score arithmetic, recommendation thresholds, top-10–20% gate, and memo constraints.
- Contract tests: Stage 01 → 02 and Stage 02 → 03 schemas.
- Integration test: one fixture-driven end-to-end run with HTTP and OpenAI mocked.
- Optional live smoke test: opt-in, excluded from default CI, requires `OPENAI_API_KEY`.

### Evals verify AI behavior

- Commit a small representative dataset based on the completed YC/HN dry runs.
- Deterministic graders first: required fields, valid citations, allowed labels, score consistency, missing-data honesty, memo sections, and length.
- Semantic graders only where needed: thesis adherence, evidence-to-claim faithfulness, plain-language product explanation, risk quality, and specificity of “what changes our mind.”
- Store eval results by model and prompt version so changes can be compared.
- Keep the MVP eval harness local; mention OpenAI Evals API only as an optional later integration, not a dependency.

## Replayability and Failure Policy

Require `outputs/<run_id>/manifest.json` to record input, timestamps, stage status, artifact paths, source URLs, prompt/model versions, usage, and errors.

- Each completed stage writes an immutable artifact before the next begins.
- A run can be inspected or replayed from a prior stage artifact without re-sourcing.
- Partial candidate failures remain in output with structured errors.
- Invalid model output gets one bounded repair retry, then a structured failure.
- No memo may contain an uncited external claim.

## Required Architecture Document Structure

Write the architecture document in this exact order:

1. **Decision Summary** — maximum six bullets.
2. **System at a Glance** — one small Mermaid flow diagram from CLI input to committed memos.
3. **Repository Structure** — one annotated tree, limited to essential files/directories.
4. **Stage Contracts** — one table with stage, input, responsibility, output, and failure behavior.
5. **OpenAI SDK Boundary** — calls, structured outputs, web-search placement, and metadata captured.
6. **Data and Run Artifacts** — key schemas and `outputs/<run_id>/` layout.
7. **Tests and Evals** — compact test pyramid and eval matrix.
8. **Configuration and Commands** — root files, environment variables, and three canonical commands.
9. **Tradeoffs and Non-goals** — only decisions that demonstrate scope judgment.

## Style

- Target **900 words maximum**, excluding the tree and diagram.
- Top-down; conclusion first.
- One diagram, one tree, and no more than three compact tables.
- No generic architecture principles, repeated requirements, code walkthrough, or future-roadmap padding.
- Define every boundary in terms of input, output, and ownership.
- Surface the YC acquisition constraint and sparse traction/freshness limitation honestly.
- Make the three numbered stage folders and root `.env`/`pyproject.toml` understandable at a glance.

## Acceptance Check

The document is complete only if a reviewer can answer within two minutes:

1. What single command runs the system?
2. What do Stages 01, 02, and 03 each own?
3. What exact artifact crosses each boundary?
4. Where and why is OpenAI called?
5. How are citations, missing data, and failures preserved?
6. What is covered by tests versus evals?
7. How can one startup be traced from source to final recommendation?
8. Why is this design sufficient without a database, frontend, queue, or vector store?

## Output

Write only:

`00-process/03-project-documents/01-architecture.md`
