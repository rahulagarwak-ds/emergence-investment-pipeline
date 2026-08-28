# Riften

**Thesis score:** 55/100  
**Evidence coverage:** 100%

## Rationale
- Drop-in, OpenAI-/Anthropic-compatible gateway that routes to the lowest-cost capable model with model pinning and routing transparency, promising immediate cost savings via hosted open-weight models. [E1 · self-reported](<https://www.ycombinator.com/companies/riften>) [E4 · self-reported](<https://riften.ai/about>)
- Founder with relevant Palantir FDE and research background; YC materials corroborate founder and company details. [E2 · self-reported](<https://www.ycombinator.com/companies/riften>) [E5 · self-reported](<https://www.ycombinator.com/companies/riften/jobs>)
- Router/gateway category shows clear momentum with established offerings and documented multi-model routing and usage, signaling demand for this layer. [E6](<https://openrouter.ai/blog/insights/model-routing/>) [E7](<https://portkey.ai/docs/guides/getting-started/getting-started-with-ai-gateway>) [E8](<https://portkey.ai/docs/product/ai-gateway/conditional-routing>) [E10](<https://openrouter.ai/assets/State-of-AI.pdf>)

## Key risks
- Gateway trust/compliance: academic work shows commercial routers may substitute/dilute backends, creating verification and governance challenges. [E9](<https://arxiv.org/abs/2607.20860>)
- Data governance and security scrutiny since Riften hosts open-weight models and intermediates AI traffic, potentially using data for evaluation/training. [E1 · self-reported](<https://www.ycombinator.com/companies/riften>) [E4 · self-reported](<https://riften.ai/about>)
- Intense competition from existing OpenAI-compatible gateways with conditional/auto-routing features. [E6](<https://openrouter.ai/blog/insights/model-routing/>) [E7](<https://portkey.ai/docs/guides/getting-started/getting-started-with-ai-gateway>) [E8](<https://portkey.ai/docs/product/ai-gateway/conditional-routing>)

## What would change the decision
- Which reference customers are live in production and what measured cost/performance deltas have they achieved versus prior model mixes?
- What deployment modes (SaaS, private VPC, on-prem) and security attestations (e.g., SOC 2/ISO/HIPAA) are available?
- What safeguards and verification mechanisms prevent inadvertent model substitution or routing dilution, and can customers audit the served backend?

**Recommendation: Watch**
