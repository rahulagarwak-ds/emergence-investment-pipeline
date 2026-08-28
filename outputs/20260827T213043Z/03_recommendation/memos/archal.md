# Archal

**Thesis score:** 49/100  
**Evidence coverage:** 100%

## Rationale
- Clear product for agent and integration testing via stateful clones of popular SaaS APIs, targeting agent developers and integration teams (self-reported). [E1 · self-reported](<https://archal.ai/>) [E2 · self-reported](<https://docs.archal.ai/>) [E3 · self-reported](<https://www.ycombinator.com/companies/archal>)
- Developer adoption signal via a published Vitest integration/package for running tests against Archal sandboxes. [E4](<https://www.npmjs.com/package/%40archal/vitest?activeTab=code>)
- Category tailwinds as recent research formalizes AI sandbox threat models and design guidance, indicating growing market interest. [E6](<https://arxiv.org/abs/2606.18532>) [E7](<https://arxiv.org/abs/2608.02679>)

## Key risks
- Operational burden to maintain parity with many fast-changing third-party APIs given the stateful cloning approach (inference from self-reported model). [E2 · self-reported](<https://docs.archal.ai/>)
- Emerging competitive pressure from similar YC startup(s) in agent sandboxing. [E5](<https://www.ycombinator.com/companies/arga-labs>)

## What would change the decision
- Who are the current reference customers and usage metrics (e.g., active sandboxes per day, CI runs)?
- How closely do the stateful clones track upstream SaaS behavior and version changes?
- What is the security posture and compliance roadmap (data handling, isolation guarantees, SOC2/ISO timelines)?

**Recommendation: Pass**
