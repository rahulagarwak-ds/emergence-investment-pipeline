# Source selection

Research date: 2026-08-26  
Selected source: **Y Combinator Startup Directory**

## Why YC

- Passes the stated constraint: profiles of publicly launched YC companies are viewable without payment, and YC presents the directory as a resource for investors.
- Highest startup precision and best combined coverage of product, founders, batch, status, location, and team size.
- Current-batch filtering can supply 10–20 recent seed-stage candidates from one consistent source.
- Product and founder text is materially more useful for thesis analysis than launch popularity alone.

## Final source decision

**The Y Combinator Startup Directory is the sole selected sourcing source for the MVP.** Hacker News was evaluated only as a cross-reference during source research; it is not a selected source, optional enrichment, or a required pipeline dependency. Downstream architecture and implementation must source candidate records from YC only.

## Platform comparison

Each cell is **Quality/Coverage** on a 1–10 scale. Composite = `10 × Σ(weight × quality/10 × coverage/10)`. Correlated fields count once.

| Rank | Platform | Candidate identity 20% | Product 20% | Team 20% | Company state 15% | Freshness / traction 15% | Public / free access 10% | Composite |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | **YC** | 10/10 | 9/10 | 9/10 | 9/10 | 7/10 | 10/10 | **9.0** |
| 2 | Product Hunt | 7/8 | 8/10 | 4/6 | 3/5 | 9/10 | 9/10 | **5.7** |
| 3 | Crunchbase | 8/5 | 8/7 | 7/6 | 8/6 | 6/5 | 6/5 | **4.2** |
| 4 | Hacker News | 4/8 | 5/7 | 2/2 | 1/1 | 9/10 | 10/10 | **3.8** |
| 5 | Twitter/X | 4/4 | 4/4 | 4/4 | 2/3 | 8/6 | 4/4 | **1.9** |

### Sample audit

| Platform | Sample | Observed coverage |
|---|---|---|
| YC | Mireye, Ultrasonium, Baud, Tenor, 83 Sciences — Summer 2026 | Name, site, product, founders, batch, team size, status, location: 5/5. Strong quantified operating traction: 1/5. |
| Product Hunt | akta.pro, Diet Claude, Agnost AI, Jotform AI Data Assistant, Nimbia | Name, site, product, tags, launch timing, points, rank: 5/5. Founder background: 0/5. |
| Crunchbase | 4 exact-name lookups from the YC sample | Correct profile: 2/4. Key dates and funding values were gated or obfuscated. |
| Hacker News | 5 latest Show HN submissions | URL, author, timestamp, points, comments: 5/5. Verifiable company/founder identity: 0/5. |
| Twitter/X | 4 exact-name searches from the YC sample | No reliable exact-match candidate set; results were noisy and API reads require payment. |

The small sample is directional, not statistically representative.

## Standardized YC signal set

| Segment | Fields | Partner value |
|---|---|---|
| Identity | `name`, `website_url`, `canonical_domain`, `yc_profile_url` | Deduplication and citation |
| Product | `tagline`, `description`, `categories` | Infer customer, problem, solution, and thesis fit |
| Team | `founders[]`, `founder_bios[]`, `team_size` | Infer domain expertise, technical depth, and prior founder/operator signal |
| Company state | `founded_year`, `yc_batch`, `status`, `location` | Stage and operating context |
| Traction | `traction_type`, `traction_value`, `traction_period`, `traction_evidence` | Strongest stated business evidence; mark `self_reported` |
| Provenance | `source_record_id`, `source_url`, `captured_at` | Auditability |

## Standalone freshness metric

`is_current_batch: boolean`

- `true` when `yc_batch` equals the directory's current batch at `captured_at`.
- Quality: **8/10** — reliable recent cohort evidence, but not continuous product activity.
- Coverage: **10/10** across the five YC samples.
- Score it once; do not also score founded year or batch recency.
- **Candidate eligibility:** A company counts toward the required 10–20 only when `is_current_batch = true` or its strongest permitted YC traction signal is non-null. Other matched records remain preserved as incomplete but do not count toward the candidate target. `is_current_batch` represents cohort recency, not current product activity.

## Proxy and no-double-count rules

1. **Identity:** canonical domain is primary; normalized name is fallback. Never merge conflicting domains on name alone.
2. **Product:** description is primary; tagline is fallback. Categories classify but do not add another thesis-fit score.
3. **Team:** founder bios are primary; launch-post team text is fallback. Founder count and team size do not proxy founder quality.
4. **Freshness:** `is_current_batch` is primary; `founded_year == current_year` is fallback only when batch metadata is missing.
5. **Traction:** retain one strongest signal: revenue/ARR/MRR → paid customers → active usage → deployments/design partners. Do not sum correlated claims.
6. **Product proof:** performance benchmarks and feature counts are product evidence, not traction proxies.
7. **Text claims:** retain the cited passage and mark it `self_reported`; missing evidence stays `null`, not zero.

## Limitations and assumptions

- YC covers only YC-backed companies and has accelerator-selection bias.
- Founder-authored descriptions and traction claims are not independently verified.
- `is_current_batch` measures recent cohort disclosure, not ongoing activity. Exact launch dates, funding news, or linked GitHub `pushed_at` may enrich it later when citable.
- The directory is public, but YC has no documented company-directory API and its terms restrict automated extraction. Production ingestion needs permission or another compliant acquisition method.
- Current-batch membership changes as companies are revealed; every run must store `captured_at`.

## References

- [YC directory purpose](https://www.ycombinator.com/blog/the-yc-directory/) and [Summer 2026 directory](https://www.ycombinator.com/companies?batch=Summer%202026)
- YC samples: [Mireye](https://www.ycombinator.com/companies/mireye), [Ultrasonium](https://www.ycombinator.com/companies/ultrasonium), [Baud](https://www.ycombinator.com/companies/baud), [Tenor](https://www.ycombinator.com/companies/tenor), [83 Sciences](https://www.ycombinator.com/companies/83-sciences)
- [Product Hunt archive](https://www.producthunt.com/leaderboard/daily/2026/8/25) and [API documentation](https://www.producthunt.com/v2/docs)
- [Official Hacker News API](https://github.com/HackerNews/API)
- [Crunchbase free versus paid access](https://support.crunchbase.com/hc/en-us/articles/360062989313-What-is-the-Difference-between-a-Free-Crunchbase-Account-and-Crunchbase-Paid-Subscriptions)
- [X API pricing](https://docs.x.com/x-api/getting-started/pricing)
- [YC terms](https://www.ycombinator.com/legal/)
