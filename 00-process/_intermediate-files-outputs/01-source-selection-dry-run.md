# Source selection dry run

Research date: 2026-08-26  
Input feed: **YC Winter 2025 batch (W25)**  
Source tested: **Y Combinator Startup Directory**  
Current YC batch at capture: **Summer 2026 (S26)**

## Result

**Completeness verdict: conditional pass.** YC supplies the identity, team, company-state, provenance, and most product fields required by `00-source-selection.md`. It does not consistently supply qualifying company traction, and the standalone freshness metric is complete but not discriminating for a historical W25 feed.

| Overall score | Score | Reason |
|---|---:|---|
| **Coverage** | **9/10** | 196 of 220 tested field slots were available or operationally derivable under the stated rules (89%). Most missing slots were traction fields. |
| **Quality** | **7/10** | Core YC facts are structured and attributable. Product and founder text is self-authored, traction is sparse and self-reported, and W25 membership does not establish current operating activity. |

The minimum candidate output is complete for **9/10 companies**. Operand has no YC tagline, description, or categories; its launch post explains the product, but launch text is not an allowed product-description proxy in the current rules. All ten candidates have a freshness value, but it is `is_current_batch = false` for every company.

## Method

- Inspected ten public W25 company profiles spanning software, AI, legal tech, space, robotics, recruiting, and e-commerce.
- Tested only the fields and proxy rules defined in `00-source-selection.md`.
- Counted missing evidence as `null`, not zero.
- Retained only the strongest permitted traction signal per company.
- Treated company product claims, market statistics, product benchmarks, future plans, and founders' previous-company results as non-traction.
- Coverage score is `round(10 × covered field slots / tested field slots)`. Quality is a 1–10 judgment of reliability and investment usefulness, not another measure of presence.

This is a completeness audit of a deliberately varied ten-company sample, not a statistical estimate of the entire W25 batch.

## Candidate dry run

Legend: **✓** complete; **△** present but weak or relative; **—** no qualifying value, therefore `null`.

| Candidate | Product | Team | Company state | Strongest qualifying traction | `is_current_batch` |
|---|---|---|---|---|---:|
| [Peppr AI](https://www.ycombinator.com/companies/peppr-ai) | ✓ | △ Founder names and bios present; bios are generic | ✓ Founded 2025; W25; team 4; Active; San Francisco | — The 90% statement is a market claim, not Peppr traction | `false` |
| [Operand](https://www.ycombinator.com/companies/operand) | — Tagline, description, and categories are blank | ✓ Three founders with bios; team 8 | ✓ Founded 2024; W25; Active; San Francisco | Customer outcome; “6-figure P&L improvements”; period `null`; `self_reported` | `false` |
| [OpenIntake](https://www.ycombinator.com/companies/openintake) | ✓ | ✓ Two founders with relevant bios; team 2 | ✓ Founded 2025; W25; Active; New York City | — Product benefit and prior TripleZip claims do not establish current OpenIntake traction | `false` |
| [awen](https://www.ycombinator.com/companies/awen) | ✓ | ✓ Founder bio present; team 6 | ✓ Founded 2023; W25; Active; Paris | — No qualifying business evidence | `false` |
| [Instinct Space](https://www.ycombinator.com/companies/instinct-space) | ✓ | ✓ Three founders with domain-specific bios; team 5 | ✓ Founded 2024; W25; Active; London | — Future tests and a planned Q4 2028 mission are roadmap, not traction | `false` |
| [Roark](https://www.ycombinator.com/companies/roark) | ✓ | ✓ Two founders with detailed bios; team 3 | ✓ Founded 2025; W25; Active; San Francisco | Active usage; over 10M call minutes; last 6 months; `self_reported` | `false` |
| [Mastra](https://www.ycombinator.com/companies/mastra) | ✓ | ✓ Three founders with detailed bios; team 30 | ✓ Founded 2024; W25; Active; San Francisco | Active usage; GitHub stars increased 1,500 → 7,500; one week; `self_reported` | `false` |
| [Revise Robotics](https://www.ycombinator.com/companies/revise-robotics) | ✓ | ✓ Two founders with bios; team 3 | ✓ Founded 2024; W25; Active; New York City | Deployment/pilot; one completed pilot; “last month”; `self_reported` | `false` |
| [Contrario](https://www.ycombinator.com/companies/contrario) | ✓ | ✓ Two founders with detailed bios; team 20 | ✓ Founded 2025; W25; Active; San Francisco | Revenue; $6M annualized revenue; under 6 months; `self_reported` | `false` |
| [Bezel](https://www.ycombinator.com/companies/bezel) | ✓ | ✓ Founder bio present; team 1 | ✓ Founded 2025; W25; Active; New York City | — Product-cost comparison and promotional credits are not traction | `false` |

## Covered metrics and scores

| Segment | Tested fields | Covered slots | Coverage | Quality | Completeness finding |
|---|---|---:|---:|---:|---|
| Identity | `name`, `website_url`, `canonical_domain`, `yc_profile_url` | 40/40 | **10/10** | **9/10** | Complete. Domains and YC URLs give strong deduplication keys. |
| Product | `tagline`, `description`, `categories` | 27/30 | **9/10** | **8/10** | All three fields are absent for Operand. The other profiles are decision-useful but founder-authored. |
| Team | `founders[]`, `founder_bios[]`, `team_size` | 30/30 | **10/10** | **7/10** | Complete presence, but bio depth varies materially; Peppr shows why presence is not the same as quality. |
| Company state | `founded_year`, `yc_batch`, `status`, `location` | 40/40 | **10/10** | **8/10** | Complete and consistently presented. No field-level update timestamp is exposed. |
| Traction | `traction_type`, `traction_value`, `traction_period`, `traction_evidence` | 19/40 | **5/10** | **5/10** | Five companies have a qualifying signal; four include a period. Every signal is self-reported, and some periods are relative to undated launch text. |
| Provenance | `source_record_id`, `source_url`, `captured_at` | 30/30 | **10/10** | **10/10** | Profile slug supplies the record ID, page supplies the URL, and the pipeline supplies capture time. |
| Freshness | `is_current_batch` | 10/10 | **10/10** | **8/10** | Accurately derivable for all profiles, but uniformly false for this historical feed. Ranking usefulness within W25 is only **2/10**. |

### Traction field detail

| Traction field | Coverage | Explanation |
|---|---:|---|
| `traction_type` | 5/10 | Operand, Roark, Mastra, Revise Robotics, and Contrario have a permitted signal. |
| `traction_value` | 5/10 | Each of those claims includes a value, though Operand's “6-figure” value is imprecise. |
| `traction_period` | 4/10 | Roark, Mastra, Revise Robotics, and Contrario state a period; Operand does not. |
| `traction_evidence` | 5/10 | The YC page preserves citable text, but all five claims remain `self_reported`. |

## Freshness reasoning

At capture time, the current directory cohort is [Summer 2026](https://www.ycombinator.com/companies?batch=Summer%202026). Therefore:

```text
yc_batch = Winter 2025
current_batch = Summer 2026
is_current_batch = false
```

This is a valid and high-coverage cohort-recency test. It answers, “Was this company disclosed in YC's current batch?” It does **not** answer, “Is this company active now?” or “When did its traction last change?”

The dry run demonstrates both sides of the metric:

- As an extraction field, it passes: **10/10 coverage** and no ambiguity in this sample.
- As a ranking signal inside a W25-only feed, it is non-discriminating: all ten values are identical.
- The YC `Active` status is useful company state but has no visible update time.
- Some profiles expose newer dated news—Mastra has news dated 2026-04-09 and Instinct Space has news dated 2026-06-17—but that coverage is inconsistent and `latest_activity_at` is not part of the selected signal set.

The **8/10 freshness quality** assigned in `00-source-selection.md` remains justified for current-batch sourcing: current-batch membership is reliable, recent cohort evidence. For this historical W25 dry run, however, its **within-feed ranking usefulness is 2/10**. These are different questions and should not be combined into one score.

## Final completeness decision

YC alone is sufficient to construct a traceable W25 candidate list with strong identity, product, team, and company-state coverage. It is **not sufficient to populate meaningful traction for every candidate or to prove ongoing activity for a historical batch**.

- **Pass:** identity, team, company state, provenance, and the mechanical freshness boolean.
- **Near-pass:** product; 9/10 profiles are complete.
- **Partial:** traction; qualifying signals appear for 5/10 profiles.
- **Constraint:** every W25 company is correctly `is_current_batch = false`, so the field cannot rank companies within this feed by freshness.

No missing traction or activity value should be inferred. It remains `null` until a cited source supplies it.

## Source pages

- [YC Summer 2026 directory](https://www.ycombinator.com/companies?batch=Summer%202026)
- W25 sample: [Peppr AI](https://www.ycombinator.com/companies/peppr-ai), [Operand](https://www.ycombinator.com/companies/operand), [OpenIntake](https://www.ycombinator.com/companies/openintake), [awen](https://www.ycombinator.com/companies/awen), [Instinct Space](https://www.ycombinator.com/companies/instinct-space), [Roark](https://www.ycombinator.com/companies/roark), [Mastra](https://www.ycombinator.com/companies/mastra), [Revise Robotics](https://www.ycombinator.com/companies/revise-robotics), [Contrario](https://www.ycombinator.com/companies/contrario), and [Bezel](https://www.ycombinator.com/companies/bezel)
