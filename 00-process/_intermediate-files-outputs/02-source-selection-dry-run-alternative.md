# Source selection dry run — Hacker News cross-reference

Research date: 2026-08-26  
Input feed: **the same ten YC Winter 2025 companies used in `01-source-selection-dry-run.md`**  
Alternative source tested: **Hacker News (HN)**  
Comparison source: **Y Combinator Startup Directory**

> **Decision status:** This document is retained as source-comparison evidence. Its recommendation to use HN as optional enrichment was not adopted and is superseded by `00-process/03-project-documents/00-source-selection.md`. YC is the sole MVP sourcing source.

## Result

**Cross-reference verdict: HN is useful enrichment, but it fails as a complete alternative source for this input set.** Exact HN evidence exists for 4/10 companies. It materially enriches Mastra and partially confirms Roark, Bezel, and Contrario; it supplies no exact record for the other six.

| Overall HN score | Score | Reason |
|---|---:|---|
| **Coverage** | **2/10** | 48 of 220 same-schema field slots were available (22%). Exact HN records were found for only 4/10 inputs. |
| **Quality** | **5/10** | HN item IDs, timestamps, points, and comments are precise. Company claims remain user-submitted, identity resolution is noisy, and company/team/state fields are rarely structured. |

Only **2/10 companies**—Roark and Mastra—meet the minimum output requirement of name, website, one-line product description, team signal, and at least one freshness or traction signal using HN evidence. YC met that minimum for 9/10 companies.

## Method

- Held the Prompt 2 sample constant: Peppr AI, Operand, OpenIntake, awen, Instinct Space, Roark, Mastra, Revise Robotics, Contrario, and Bezel.
- Searched HN stories by exact current domain, known historical domain where present in YC, and exact company name using the [HN Search API](https://hn.algolia.com/api).
- Rejected generic-name collisions and unrelated domains. Operand illustrates the issue: name search returns programming uses of “operand” and an unrelated `operand.ai`; none matches the W25 company or its known domains.
- Validated retained item IDs and canonical fields using the [official HN API](https://github.com/HackerNews/API).
- Tested the exact field set and proxy/no-double-count rules from `00-source-selection.md`.
- Did not give HN credit for fields known only from the YC input record.
- Did not treat HN points or comments as company traction. They measure HN engagement.
- Counted `captured_at` for every search attempt; `source_record_id` and `source_url` remain `null` when no exact HN item exists.

Coverage score is `round(10 × covered field slots / tested field slots)`, with a minimum displayed segment score of 1 when some coverage exists. Quality scores reliability and investment usefulness, not presence.

## Exact-input cross-reference

| Candidate | HN match | Retained HN evidence | Same-schema information available | Critical gaps |
|---|---:|---|---|---|
| Peppr AI | No | Exact name and `usepeppr.ai`: no story | Search capture provenance only | All candidate fields |
| Operand | No | `operand.com`, `tryoperand.com`, and contextual name search: no valid match | Search capture provenance only | Generic name produces unrelated results; all candidate fields |
| OpenIntake | No | Exact name and `openintake.ai`: no story | Search capture provenance only | All candidate fields |
| awen | No | Exact name and `awen.ai`: no story | Search capture provenance only | All candidate fields |
| Instinct Space | No | Exact name and `instinct-space.com`: no story | Search capture provenance only | All candidate fields |
| [Roark](https://news.ycombinator.com/item?id=43080895) | Yes | Launch HN; 2025-02-17; 60 points; 29 comments | Name, site/domain, product text, founders/team narrative, W25, and an unquantified deployment signal | Founder bios, team size, founded year, status, location, quantified traction period/value |
| [Mastra](https://news.ycombinator.com/item?id=46693959) | Yes | Mastra 1.0 Show HN; 2026-01-20; 213 points; 70 comments; supplemented by the [original Show HN](https://news.ycombinator.com/item?id=43103073) | Name, site/domain, product text, founders/team narrative, and complete active-usage traction: 300K+ weekly npm downloads | YC batch, founded year, status, location, team size, YC profile URL |
| Revise Robotics | No | Exact name and `reviserobotics.com`: no story | Search capture provenance only | All candidate fields |
| [Contrario](https://news.ycombinator.com/item?id=43230927) | Yes | Link-only HN story; 2025-03-02; 2 points; 0 comments | Company name and a short product tagline | Company domain, description, team, state, traction, batch |
| [Bezel](https://news.ycombinator.com/item?id=44051090) | Yes | Exact `trybezel.com` story; 2025-05-21; 67 points; 21 comments | Domain, partial product narrative, YC affiliation, and an unquantified customer/deployment claim | Company name is not explicit in the item; team, company state, batch, and current product alignment |

The Bezel HN record is an exact-domain match, but it describes agentic image-generation research and an earlier customer-persona use case rather than the complete current YC positioning. It is therefore useful evidence with low current-product completeness.

## Covered metrics and scores

| Segment | Tested fields | Covered slots | HN coverage | HN quality | Finding |
|---|---|---:|---:|---:|---|
| Identity | `name`, `website_url`, `canonical_domain`, `yc_profile_url` | 9/40 | **2/10** | **7/10** | Exact domains are strong when present, but only four candidates match and no HN item supplies a YC company-profile URL. |
| Product | `tagline`, `description`, `categories` | 7/30 | **2/10** | **6/10** | Roark, Mastra, and Bezel have narrative text; Contrario has only a title-level tagline. HN post tags are not sector categories. |
| Team | `founders[]`, `founder_bios[]`, `team_size` | 4/30 | **1/10** | **5/10** | Roark and Mastra name founders and provide launch-team narrative. No matched item states team size. |
| Company state | `founded_year`, `yc_batch`, `status`, `location` | 1/40 | **1/10** | **7/10** | Only Roark's title states W25. “YC” or “graduated from YC” does not identify a batch. |
| Traction | `traction_type`, `traction_value`, `traction_period`, `traction_evidence` | 8/40 | **2/10** | **5/10** | Three companies have qualifying self-reported signals; only Mastra has complete, quantified usage evidence. |
| Provenance | `source_record_id`, `source_url`, `captured_at` | 18/30 | **6/10** | **9/10** | Four matches have canonical HN IDs/URLs; all ten searches have capture time. |
| Freshness | `is_current_batch` | 1/10 | **1/10** | **8/10** | Derivable only for Roark because its HN title explicitly states W25. HN submission time is separate and cannot supply a missing YC batch. |
| **Overall** | 22 fields × 10 companies | **48/220** | **2/10** | **5/10** | Strong event data for a small matched subset; poor company-record completeness. |

### Traction detail

| Candidate | `traction_type` | `traction_value` | `traction_period` | `traction_evidence` | Treatment |
|---|---|---|---|---|---|
| Roark | Deployments/design partners | `null` | `null` | Working with teams in healthcare, legal, and customer service | `self_reported`; HN engagement excluded |
| Mastra | Active usage | 300K+ npm downloads | Weekly | Also states 19.4K GitHub stars and production use at named companies | Retain 300K+ weekly downloads as the strongest signal; `self_reported` |
| Bezel | Deployments/design partners | `null` | `null` | Building customer personas for large e-commerce companies | `self_reported`; current-product alignment is partial |
| All others | `null` | `null` | `null` | `null` | No qualifying HN evidence |

Mastra's GitHub stars and named production users corroborate the usage claim but are not added as separate traction scores. HN points and comments are also excluded from traction.

## HN-native metrics

HN exposes a useful signal set that is not present in the YC schema:

| HN-native fields | Coverage across ten inputs | Quality | Interpretation |
|---|---:|---:|---|
| `hn_item_id`, `submitted_at`, `submitter`, `points`, `comment_count` | **4/10** | **9/10** | Precise launch/discussion provenance and HN audience response for matched companies only. |

`submitted_at` is a reliable publication timestamp, but it establishes freshness of the HN event—not continuing company activity. Points and comments measure community attention, not revenue, customers, or usage.

## Quick comparison with YC dry run

| Metric | YC result | HN result | Difference |
|---|---:|---:|---|
| Exact candidate records | 10/10 | 4/10 | HN misses six inputs entirely. |
| Minimum complete candidate output | 9/10 | 2/10 | HN fully supports only Roark and Mastra. |
| Overall coverage | **9/10** (196/220) | **2/10** (48/220) | YC leads by 7 points and 148 fields. |
| Overall quality | **7/10** | **5/10** | HN's canonical event metadata is strong, but company claims are sparse and unstructured. |
| Product coverage | 9/10 | 2/10 | HN has detailed product text only when a founder/team member makes a substantive post. |
| Team coverage | 10/10 | 1/10 | HN has no structured team records or team-size field. |
| Company-state coverage | 10/10 | 1/10 | HN is not a company directory. |
| Traction coverage | 5/10 | 2/10 | HN adds a strong Mastra signal, but cannot match YC across the fixed sample. |
| `is_current_batch` coverage | 10/10 | 1/10 | HN titles rarely include YC batch metadata. |
| Native publication/engagement | Not in selected YC schema | 4/10, quality 9/10 | HN's primary complementary value. |

## Final cross-reference decision

- **YC remains the complete primary source** for this candidate feed.
- **HN should be used as optional enrichment**, not as a required join or replacement source.
- An exact HN match can add a dated launch narrative, founder-authored detail, community questions, and—in Mastra's case—newer quantified usage.
- Absence from HN is not negative evidence: six YC companies have no exact HN story in the searchable index.
- HN engagement must remain separate from business traction.
- Matches must use canonical-domain confirmation where possible; generic name-only results are unsafe to merge.

## References

- [HN Search API](https://hn.algolia.com/api) used for exact-name/domain discovery
- [Official Hacker News API](https://github.com/HackerNews/API) used to validate item IDs and canonical fields
- Retained HN records: [Roark](https://news.ycombinator.com/item?id=43080895), [Mastra 1.0](https://news.ycombinator.com/item?id=46693959), [original Mastra Show HN](https://news.ycombinator.com/item?id=43103073), [Contrario](https://news.ycombinator.com/item?id=43230927), and [Bezel](https://news.ycombinator.com/item?id=44051090)
- [YC dry-run comparison](./01-source-selection-dry-run.md)
