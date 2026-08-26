# AGENTS.md

## Project Context

This repository contains an AI-augmented investment pipeline for a seed-stage VC workflow.

The pipeline has three primary stages:

1. Sourcing
2. Analysis
3. Recommendation

The system should remain simple, replayable, traceable, and easy for another engineer to understand.

## Working Principles

- Read existing code and documentation before making changes.
- Follow the existing repository structure and conventions.
- Prefer simple implementations over additional abstractions.
- Make the smallest change required to complete the task.
- Do not modify unrelated files.
- Do not introduce infrastructure unless clearly required.
- Keep sourcing, analysis, and recommendation concerns separated.
- Preserve intermediate artifacts where they improve traceability.

## Before Making Changes

1. Understand the requested task.
2. Inspect relevant existing files.
3. Check related decisions and requirements under `00-process/`.
4. Identify dependencies and downstream impact.
5. Ask for clarification when a material product or investment decision cannot be inferred from existing documentation.

Do not silently make major scoping, thesis, scoring, or investment decisions.

## Code

- Prefer readable, explicit code.
- Keep functions focused.
- Avoid unnecessary classes, frameworks, and abstractions.
- Reuse existing utilities before creating new ones.
- Use clear names that describe business intent.
- Keep configuration separate from implementation where appropriate.
- Handle missing or malformed external data explicitly.
- Do not hide failures that could affect investment analysis.

## Data and Evidence

- Use public data only.
- Preserve source URLs and provenance for material claims.
- Never invent missing information.
- Represent unavailable information as unknown/null where appropriate.
- Distinguish sourced facts from model-generated inference.
- Distinguish self-reported company claims from independently observable signals.
- Do not convert missing evidence into negative evidence unless explicitly defined by the scoring framework.
- Avoid double-counting correlated signals.

## LLM Usage

- Treat LLM output as generated analysis, not ground truth.
- Use structured outputs where practical.
- Keep runtime prompts versioned in the repository.
- Ground analysis in collected evidence.
- Do not allow unsupported factual claims into final memos.
- Prefer deterministic code for calculations, validation, ranking, and rules where an LLM is unnecessary.

## Scoring and Recommendations

- Follow the documented thesis and scoring framework.
- Do not change scoring weights or recommendation rules without explicit instruction.
- Scores must be reproducible from the defined framework.
- Keep thesis fit separate from absolute company quality.
- Preserve uncertainty when evidence is incomplete.
- Recommendations must be supported by the analysis rather than generated independently.

## Testing and Evaluation

- Add or update tests when behavior changes.
- Keep deterministic software tests separate from AI/output evaluations.
- Test important edge cases, especially missing and malformed source data.
- Evaluate grounding, scoring consistency, and output quality where relevant.
- Do not optimize an implementation only for the committed example outputs.

## Repository Boundaries

- `00-process/` contains project understanding, prompts, decisions, and process evidence.
- `01-src/` contains pipeline implementation and runtime prompts.
- `02-evals/` contains AI and output-quality evaluations.
- `03-tests/` contains deterministic software tests.
- `04-run-results/` contains committed pipeline outputs.
- `_resources/` contains supplied reference material.

Do not reorganize these top-level boundaries without explicit instruction.

## Scope Guardrails

Do not introduce unless explicitly requested:

- frontend applications
- databases
- vector databases
- job queues
- distributed infrastructure
- authentication systems
- deployment infrastructure
- additional sourcing platforms

The project is a focused take-home pipeline, not a production platform.

## Security

- Never commit API keys, tokens, credentials, or secrets.
- Use environment variables for secrets.
- Do not modify `.env` values unless explicitly requested.
- Keep `.env` excluded from version control.
- Avoid logging secrets or sensitive configuration.

## Completion

Before considering a task complete:

1. Run relevant tests or validations.
2. Check that existing behavior has not been unintentionally changed.
3. Verify generated artifacts where applicable.
4. Check source/provenance preservation for data changes.
5. Review `git diff` for unrelated modifications.
6. Clearly state what was changed, what was validated, and any remaining uncertainty.

## AI Work Transparency

AI assistance is expected in this repository.

Do not manufacture retrospective process documentation. When a task produces a meaningful design decision, debugging discovery, evaluation result, or implementation trade-off, surface it clearly so it can be recorded in the appropriate process artifact.

Do not present AI-generated judgment as a human decision.