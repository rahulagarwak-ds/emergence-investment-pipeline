# Understudy Labs

**Thesis score:** 67/100  
**Evidence coverage:** 100%

## Rationale
- Founders with strong execution fit from Instacart ML infra/experimentation and prior GTM/founding experience. [yc_profile · self-reported](<https://www.ycombinator.com/companies/understudy-labs>)
- Drop-in LLM gateway with BYO key passthrough or managed catalog, deterministic traffic splitting, and instant rollback supports low-friction adoption and iterative optimization. [docs_intro · self-reported](<https://docs.understudylabs.com/>) [docs_quickstart · self-reported](<https://docs.understudylabs.com/quickstart>) [docs_proxy_endpoints · self-reported](<https://docs.understudylabs.com/reference/proxy-endpoints>) [docs_routing · self-reported](<https://docs.understudylabs.com/concepts/routing>) [docs_replace_model · self-reported](<https://docs.understudylabs.com/tutorials/replace-a-model>)
- Self-reported benchmarks and positioning indicate potential for material cost/latency gains by tuning smaller models for bounded tasks. [site_home · self-reported](<https://understudylabs.com/>) [site_bench · self-reported](<https://understudylabs.com/bench>) [bench_ops · self-reported](<https://understudylabs.com/bench-operations>)

## Key risks
- Product is in private preview; evolving surface may limit immediate self-serve or enterprise adoption. [docs_intro · self-reported](<https://docs.understudylabs.com/>)
- Default capture of raw request/response payloads introduces data-handling, privacy, and compliance review needs. [docs_capture · self-reported](<https://docs.understudylabs.com/concepts/capture>)
- Competitive alternatives (e.g., Distil Labs) pursue similar cost-reduction via custom SLMs and traces. [distil_comp](<https://www.distillabs.ai/>)

## What would change the decision
- What is the pricing and commercial model across gateway usage, managed-model serving, and training/tuning, including any minimums or commitments?
- What is the current security posture (e.g., SOC 2/ISO 27001, encryption, key management, data residency) and controls for capture access and retention?
- Are there reference customers in production with scale metrics (volumes, latency SLOs, incident history)?

**Recommendation: Watch**
