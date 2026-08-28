# OneTriangle

**Thesis score:** 62/100  
**Evidence coverage:** 100%

## Rationale
- Clear product focus on cross-model KV transfer with claimed cost/latency gains and a public demo showing material TTFT and cost improvements (self-reported). [https://www.ycombinator.com/companies/onetriangle · self-reported](<https://www.ycombinator.com/companies/onetriangle>) [https://onetriangle.ai/demo · self-reported](<https://onetriangle.ai/demo>) [https://onetriangle.ai/ · self-reported](<https://onetriangle.ai/>)
- Approach is directionally validated by external research and growing vLLM support for KV movement, and they state plans to upstream into vLLM. [https://arxiv.org/abs/2608.03893](<https://arxiv.org/abs/2608.03893>) [https://docs.vllm.ai/en/stable/api/vllm/config/kv_transfer/?utm_source=openai](<https://docs.vllm.ai/en/stable/api/vllm/config/kv_transfer/>) [https://vllm.ai/blog/2026-01-08-kv-offloading-connector?utm_source=openai](<https://vllm.ai/blog/2026-01-08-kv-offloading-connector>) [https://www.ycombinator.com/companies/onetriangle · self-reported](<https://www.ycombinator.com/companies/onetriangle>)
- Commercial packaging appears in place with usage-based pricing for managed open-weight models and differentiated cached-input rates. [https://onetriangle.ai/models · self-reported](<https://onetriangle.ai/models>)

## Key risks
- Technique may not generalize across model pairs; external paper shows notable degradation without nonlinear mapping for some pairs. [https://arxiv.org/abs/2608.03893](<https://arxiv.org/abs/2608.03893>)
- GTM friction from limited self-serve experience; emphasis on demos and no visible public API docs could slow adoption (self-reported). [https://onetriangle.ai/ · self-reported](<https://onetriangle.ai/>) [https://onetriangle.ai/models · self-reported](<https://onetriangle.ai/models>) [https://onetriangle.ai/api · self-reported](<https://onetriangle.ai/api>)
- Commoditization risk as vLLM already exposes KV transfer/offloading and distributed interfaces, narrowing room for proprietary advantage. [https://docs.vllm.ai/en/stable/api/vllm/config/kv_transfer/?utm_source=openai](<https://docs.vllm.ai/en/stable/api/vllm/config/kv_transfer/>) [https://github.com/vllm-project/vllm/blob/main/vllm/distributed/kv_transfer/README.md?utm_source=openai](<https://github.com/vllm-project/vllm/blob/main/vllm/distributed/kv_transfer/README.md>) [https://vllm.ai/blog/2026-01-08-kv-offloading-connector?utm_source=openai](<https://vllm.ai/blog/2026-01-08-kv-offloading-connector>)

## What would change the decision
- Do they offer a fully self-serve API/SDK with public docs and keys, or is onboarding sales-led via demos?
- Which source→target model pairs are production-ready today, and what are the qualification criteria and fallbacks under load?
- What validated customer deployments exist, and what cost/latency deltas versus customer baselines are achieved in production?

**Recommendation: Watch**
