# YC snapshot input

Stage 01 reads UTF-8 JSONL with one `YCSnapshotRecordV1` object per line (contract in
`src/investment_pipeline/stage_01_sourcing/sourcing.py`). The pipeline never scrapes YC.

## Capture

```bash
uv run investment-pipeline snapshot                       # the batch in session today
uv run investment-pipeline snapshot --batch "Summer 2026" # a named batch
```

writes `inputs/yc_snapshot.jsonl` and `inputs/yc_snapshot.provenance.json` from the
[yc-oss open dataset](https://github.com/yc-oss/api): YC's public Algolia company index,
republished daily as static JSON and limited to publicly launched companies. The provenance
sidecar records the dataset URLs, its `last_updated` stamp, the upstream SHA-256, the capture
time, the current batch, and every record that failed the contract.

`current_batch` is the batch in session on the capture date (Winter Jan-Mar, Spring Apr-Jun,
Summer Jul-Sep, Fall Oct-Dec). Future batches appear in the directory as soon as their first
companies launch, so "newest batch present" is not "current"; `is_current_batch` downstream
compares against the calendar batch.

## What the dataset does not carry

Founder names and bios, founding year, and traction claims are absent, so those fields are empty
in the snapshot and stay unknown downstream: founder execution fit is scored only when Stage 02
finds cited public evidence, and candidate eligibility rests on current-batch membership.

`tests/fixtures/yc_snapshot.jsonl` is a synthetic contract fixture, never a real input.
