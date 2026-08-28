# Waddle Labs

**Thesis score:** 51/100  
**Evidence coverage:** 100%

## Rationale
- Most capability and positioning claims are self-reported, and the team itself notes benchmarking comparability challenges; there is limited external validation beyond the SDK’s presence on PyPI. [E1 · self-reported](<https://www.ycombinator.com/companies/waddle-labs>) [E2 · self-reported](<https://www.waddlelabs.ai/>) [E3 · self-reported](<https://www.waddlelabs.ai/research/introducing-waddle>) [E4](<https://pypi.org/project/waddle-sdk/>)
- Offering is in preview/early access rather than GA, suggesting enterprise readiness and production fit remain unproven. [E1 · self-reported](<https://www.ycombinator.com/companies/waddle-labs>) [E2 · self-reported](<https://www.waddlelabs.ai/>)
- Agents inherit properties of underlying LLMs, creating dependency on external model performance and interfaces. [E1 · self-reported](<https://www.ycombinator.com/companies/waddle-labs>) [E3 · self-reported](<https://www.waddlelabs.ai/research/introducing-waddle>)

## Key risks
- Results are hard to compare across tasks/robots due to lack of standardized benchmarks, impeding proof of reliability and ROI. [E3 · self-reported](<https://www.waddlelabs.ai/research/introducing-waddle>)
- Reliability and safety may fluctuate with changes in foundation models and tools the agents depend on. [E1 · self-reported](<https://www.ycombinator.com/companies/waddle-labs>) [E3 · self-reported](<https://www.waddlelabs.ai/research/introducing-waddle>)

## What would change the decision
- Who are the first paying customers and in which industries or workflows are pilots running?
- What are measured success rates, cycle times, and safety incident rates for representative tasks on real hardware?
- What robots and sensors are officially supported out of the box, and what integration effort is required per site?

**Recommendation: Pass**
