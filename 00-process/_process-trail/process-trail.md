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
    - Representative run `20260827T213043Z` (topic B2B, 10 candidates): 10 of 10 analyses accepted, 10 cited memos, 0 meeting / 5 watch / 5 pass; deterministic evals report zero findings and the semantic judge scores faithfulness 5.0, clarity 5.0, risk quality 4.4, specificity 4.7 but thesis adherence 2.8, which names the next memo-quality target. Replays from the run's `candidates.json` and `analyses.jsonl` completed as linked runs; the re-analysis reordered the ranking, so run-to-run score variance is the next scoring target
    - Two partner-topic runs died mid-Stage 03 with `FileNotFoundError` on their own `logs.jsonl`. Cause was the checkpointing method used during the session, not the pipeline: `git stash push -u` removes untracked files and had pulled the un-ignored run directories out from under the running processes. Stashes now exclude `outputs/`; the run store additionally retries transient file errors and the crash handler no longer depends on the log file
    - Windows `core.autocrlf` rewrote LF artifacts to CRLF on checkout, breaking every manifest hash locally; a `.gitattributes` with `eol=lf` keeps artifacts byte-stable on every platform. The memo grader also exposed models using a URL as an evidence id, which made citation labels unreadable; the model-facing evidence id is now constrained to a short token
    - Chunk 7 completed: seven runs kept under `outputs/` and un-ignored individually (B2B representative run, both replays, the honest insufficient-candidates failure, and healthcare, AI agents, developer tools topic runs); evals reports written for every completed run; README documents the runs and traces Rapidfolio from YC profile to memo. AI agents and developer tools each rejected one analysis for a stated reason and each kept nine memos, one of them a Take a meeting
    - Chunk 8 audit: pytest, Ruff, and mypy clean; artifact hashes verified for all kept runs; no secrets, employer, or machine paths in anything to be committed; Ponytail repo audit listed five optional cuts (consolidating the three test fakes, replacing pydantic-settings with stdlib env parsing, two small CLI de-duplications, deriving the judge rating names) totalling about 72 lines and one dependency, none applied so the handoff stays stable
    - Consistency review after the live session: architecture layout lines now match the flat `tests/` and run-grading `evals/` that were built, `AGENTS.md` lists the `inputs/` boundary, and the implementation prompt gained a Prompt 2 recording the requirements the live runs added; the seven committed runs share analysis prompt `1f2ee6fa` while the current prompt adds only the short-evidence-id instruction
    - Memo format v2 (memo-v2): the call moves to the header under the company name, followed by score and coverage and a five-row pillar table (score/maximum, unknown for null, evidence links) above the rationale; rendering stays deterministic Python; tests and the memo grader read the header while old-format committed runs still grade unchanged
    - Verified citations (analysis-v2 / memo-v2): the analysis prompt asks for the most specific page per claim; every evidence URL is requested once per candidate (HEAD, then GET) and its status and check time are stored on the evidence item; a 4xx/5xx or unreachable link is rejected with the exact reason for the repair retry and fails the candidate honestly if it persists, while 403 stays unverified; memos may cite only verified evidence and the pillar table shows unverified ids without a link; a `citations` grader checks memo links against verified evidence and flags root pages cited where deeper verified pages exist; runs from before verification are skipped by that grader
    - First memo-v2 run `20260828T062642Z` (topic B2B): 9 of 10 analyses accepted, 130 evidence links requested, 128 verified, 2 blocked (403) kept out of the memos; semantic judge thesis adherence rose from 2.8 to 3.7-4.0 across two judge passes, with faithfulness 4.9-5.0 and clarity 4.9-5.0 (the judge itself varies run to run). The one rejection was a 429 rate-limited news page, so 429 now joins 403 as unverified-but-present instead of failing the candidate
    - The citations grader's root-page heuristic (flag a homepage link when a deeper verified page exists) produced 52 false positives on that run because many claims genuinely live on the homepage; the heuristic was removed and the grader keeps only the hard check that every memo link is verified evidence, leaving page specificity to the semantic judge
    - memo-v3: pillar scores display out of 100 each for a consistent read; raw weighted scores are unchanged in the analysis artifact; grader and tests follow
