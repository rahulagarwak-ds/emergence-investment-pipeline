# Context.dev

**Recommendation: Watch**

**Thesis score:** 75/100 · **Evidence coverage:** 100%

| Pillar | Score | Evidence |
| --- | ---: | --- |
| Product adoption | 80/100 | [E4](<https://docs.context.dev/introduction>) [E7](<https://www.context.dev/pricing>) [E10](<https://www.context.dev/customers>) |
| Workflow habit and importance | 76/100 | [E8](<https://www.ycombinator.com/companies/contextdev>) [E10](<https://www.context.dev/customers>) [E11](<https://docs.context.dev/introduction>) |
| Employee to team expansion | 65/100 | [E6](<https://docs.context.dev/introduction>) [E10](<https://www.context.dev/customers>) |
| Enterprise procurement path | 73/100 | [E7](<https://www.context.dev/pricing>) [E13](<https://trust.context.dev/>) |
| Founder execution fit | 80/100 | [E1](<https://www.ycombinator.com/companies/contextdev>) [E3](<https://www.ycombinator.com/companies/contextdev>) |

## Rationale
- The product offers broad web-data extraction through APIs, SDKs, MCP, and no-code integrations, supporting low-friction adoption. [E4 · self-reported](<https://docs.context.dev/introduction>) [E5 · self-reported](<https://docs.context.dev/introduction>) [E6 · self-reported](<https://docs.context.dev/introduction>)
- Self-reported customer examples indicate meaningful production workloads, including more than one million scrapes and monitoring roughly 6,000 websites. [E9 · self-reported](<https://www.ycombinator.com/companies/contextdev>) [E10 · self-reported](<https://www.context.dev/customers>)
- A free tier and paid plans starting at $25 per month provide an accessible path from experimentation to production use. [E7 · self-reported](<https://www.context.dev/pricing>)

## Key risks
- Cold crawls may approach the five-minute platform timeout, creating latency risk for user-facing applications. [E11 · self-reported](<https://docs.context.dev/introduction>)
- Brand data may remain cached for approximately 90 days by default, which may not satisfy freshness-sensitive use cases. [E12 · self-reported](<https://www.context.dev/>)
- The record does not establish web-coverage reliability, legal durability, or enterprise security maturity beyond self-reported SOC 2 Type I compliance; Type II is in progress. [E4 · self-reported](<https://docs.context.dev/introduction>) [E13 · self-reported](<https://trust.context.dev/>)

## What would change the decision
- What are current revenue, paid-customer conversion, retention, gross margins, and request-volume trends?
- What are success rates, p95 latency, freshness SLAs, and failure rates across website types and geographies?
- How does Context.dev differentiate sustainably from competing APIs and in-house crawling stacks?
