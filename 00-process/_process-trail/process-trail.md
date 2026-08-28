# Process Trail

Day 1 (No Output- 22nd & 23rd Aug 2026):

    - reading problem statement
    - understanding the problem statement
    - research different options and scoping the repo structure and code
    - documentation research on what documents are needed
    - manual vs AI assistance segmentation of efforts
    - research on the sources: AI-assisted (ChatGPT chat only) and manual walkthrough to understand the requirements
    - from the lens of partner: research done on what might a partner want
    - understanding of the thesis to be created


Day 2(25th-26th Aug 2026):
    - repo creation
    - process trail document start
    - requirements document created
    - source research prompts created
    - source research validation and alternative comparison created(via AI research agent)
    - source selection document created(via AI research agent)

Day 3(26th-27th Aug 2026):
    - thesis research and documentation(biggest manual research chunk)
        - summary from Google and ChatGPT
        - 00-process/03-project-documents/00-thesis.md created
        - architectural prompt created via AI
        - architecture document created via prompt
        - pony tail installed for upcoming coding sessions to minimize the tech debt followed by AI-assisted coding
        - added .env and .env.example empty files to prep for coding
        - added AGENTS.md for default instructions and context to current project for Codex


Day 4(27th Aug 2026):
    - source decision clarified with YC as the sole MVP source and HN retained only as comparison evidence
    - architecture aligned to YC-only sourcing and reduced for faster review
    - documentation proofreading and gap analysis completed via AI-assisted review
    - critical documentation gaps resolved
        - deterministic YC snapshot acquisition and candidate eligibility defined
        - evidence coverage and recommendation risk gates defined
        - thesis sources linked and title aligned with the argument
        - sourcing and Stage 02 web research boundaries clarified
    - AGENTS.md updated with the process-trail instruction for meaningful work
    - end-to-end implementation prompt created for chunked delivery, testing, replayable run artifacts, concise live progress, and Ponytail review
    - removed the separate key-decisions directory requirement; final decisions remain in project documents and decision history remains in the process trail
    - Chunk 1 foundation completed with the uv-managed Python package, environment contract, stage boundaries, and strict versioned Pydantic artifact/error schemas
    - import smoke, contract rejection, pytest, Ruff, mypy, lockfile, CLI-help, and secret checks passed; AI-assisted correctness and Ponytail reviews removed the unused exception wrapper
    - Chunk 2 completed the deterministic, YC-only snapshot stage with validation, literal selectors, canonical-domain deduplication, proxy precedence, eligibility gates, provenance, and preserved partial artifacts
    - AI-assisted implementation kept stable snapshot order at the 20-candidate cap instead of inventing a pre-analysis ranking; fixture tests, artifact reload, pytest, Ruff, mypy, lockfile, and secret checks passed

Day 5(28th Aug 2026):
    - Chunk 3 completed evidence-grounded Stage 02 with the official OpenAI Responses structured-output boundary, web-search source validation, one repair attempt, per-candidate failures, prompt/model metadata, nullable unknown scores, deterministic totals, and evidence coverage
    - Official SDK documentation and installed signatures were verified; mocked repair, failure, web-source, and invalid-upstream paths passed with pytest, Ruff, mypy, lockfile, artifact, diff, and secret checks, and the AI-assisted Ponytail review removed a redundant request option
    - Chunk 4 completed deterministic score ranking and recommendation gates, constrained no-research memo rendering, cited Markdown validation, partial render failures, and the ranked index
    - AI-assisted policy and boundary tests covered the 11-candidate top-decile ceiling, score and critical-risk gates, tool-free model calls, uncited evidence rejection, memo limits, and failure preservation; pytest, Ruff, mypy, lockfile, diff, and secret checks passed, and Ponytail removed a dead exception branch
    - Test suite first run on Windows exposed five artifact reads using the platform default encoding; the memo citation separator failed under cp1252 while src writers were already UTF-8. Tests now read as UTF-8; pytest, Ruff, and mypy passed
    - Chunk 5 completed the single `run` CLI: every invocation creates an immutable `outputs/<run_id>/` with manifest, structured logs, per-stage artifact hashes, deterministic stage handoffs, `--from-artifact` replay from Stage 01 or Stage 02 output, `recommendations.json` for call and response traceability, and concise live progress that fails fast with the next actionable fact
    - Manifests store only repo-relative or bare file names so machine-specific directories never enter committed runs; mocked end-to-end, both replay paths, insufficient-candidate, missing-model, invalid-replay, and run-id uniqueness tests passed with pytest, Ruff, and mypy, a real CLI smoke run on the fixture failed honestly on the unset model, and the Ponytail review found nothing to cut
    - Chunk 6 completed tests and evals: shared pipeline fixtures in `tests/conftest.py`, orchestration edge tests for crash preservation, corrupt replay input, Stage 03 configuration failure and environment validation, an `evals/` package whose `investment-evals` command runs deterministic graders (evidence grounding, rank and call policy, missing-data honesty, memo structure and citations) and writes reports keyed by model and prompt hash, an opt-in structured memo judge, and a `LIVE_SMOKE=1` gated live boundary test
    - The suite surfaced a Windows-only intermittent PermissionError on the atomic manifest rename; the rename now retries briefly, and crash logs record function:line frames instead of full tracebacks so machine paths never enter a run. pytest, Ruff, and mypy passed and the Ponytail review found nothing to cut
    - Snapshot acquisition decided: instead of hand-capturing YC profiles, Stage 01 input is captured from the yc-oss open dataset (a daily republication of YC's public Algolia index, launched companies only, no license file published) through a new `investment-pipeline snapshot` command with a provenance sidecar; founders, founding year, and traction are absent from that dataset and stay unknown downstream
    - First capture exposed a rule bug: the dataset already lists Fall 2026 (23) and Winter 2027 (1) early launches, so 'newest batch present' made Summer 2026 non-current and zero candidates eligible; current batch is now the batch in session on the capture date, Summer 2026 captured 236 records, and offline Stage 01 gives 20 eligible for the batch, B2B, or AI selectors and an honest insufficient-candidates failure for the literal topic 'AI agents for SMBs'
    - The captured snapshot carried CRLF line endings on Windows, which would have made every manifest artifact hash unverifiable after a checkout on another OS; all artifact writers now force LF, and the run test asserts artifacts contain no carriage returns
    - First live Stage 02 call failed before the model ran: OpenAI's strict structured-output schema rejects `format: uri`, which every `HttpUrl` field emits, so the model-facing evidence draft now carries URLs as strings and Python converts them into the strict contract; a schema-compatibility test guards the drafts, and `MODEL_REQUEST_FAILED` records now keep the API error text and `INVALID_MODEL_OUTPUT` records the validation reason
    - First real run on 10 B2B candidates produced 5 partner-grade cited memos and 5 rejected analyses; reproducing two failures showed the model citing other pages on the company's own domain (docs., /security) and third-party URLs with tracking parameters. Grounding now accepts any page on the candidate's canonical domain as self-reported company evidence, matches URLs without query strings, and the repair retry states the exact rejection instead of a generic instruction
    - Run settings for the representative output set to 10 candidates at low reasoning effort (about 100 seconds per analysis at medium made 20-candidate runs impractical); the reruns replace, not accumulate, so only the final run is kept
