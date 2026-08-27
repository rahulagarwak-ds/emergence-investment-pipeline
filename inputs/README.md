# YC snapshot input

Stage 01 accepts UTF-8 JSONL with one `YCSnapshotRecordV1` object per line. The snapshot must be
manually captured or obtained through a permissioned public-data process; the pipeline does not
scrape YC. See `tests/fixtures/yc_snapshot.jsonl` for the synthetic contract fixture.
