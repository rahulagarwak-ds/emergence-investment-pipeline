# OneTriangle

**Thesis score:** 54/100  
**Evidence coverage:** 80%

## Rationale
- Rapid external validation of KV-cache transfer (vendor docs, media, and academia) supports feasibility and timing of the approach [E16](<https://nvidia.github.io/TensorRT-LLM/developer-guide/kv-transfer.html>) [E17](<https://venturebeat.com/technology/nvidia-finds-that-simple-linear-math-can-replace-costly-ai-model-handoffs>) [E18](<https://arxiv.org/abs/2608.03893>) [E20](<https://onnx.ai/onnx/technical/kv_cache.html>)
- Product claims large TTFT/cost gains and shows a live demo plus active research cadence (self-reported) [E3 · self-reported](<https://onetriangle.ai/>) [E4 · self-reported](<https://onetriangle.ai/>) [E5 · self-reported](<https://onetriangle.ai/>) [E9 · self-reported](<https://onetriangle.ai/demo>) [E6 · self-reported](<https://onetriangle.ai/blog>) [E14 · self-reported](<https://onetriangle.ai/blog>)
- Low integration friction and coverage of major open-weight models with usage-based pricing could ease adoption (self-reported) [E13 · self-reported](<https://onetriangle.ai/>) [E8 · self-reported](<https://onetriangle.ai/>) [E10 · self-reported](<https://onetriangle.ai/models>)

## Key risks
- Technique is being productized by incumbents and standardized, risking commoditization and margin pressure [E16](<https://nvidia.github.io/TensorRT-LLM/developer-guide/kv-transfer.html>) [E17](<https://venturebeat.com/technology/nvidia-finds-that-simple-linear-math-can-replace-costly-ai-model-handoffs>) [E20](<https://onnx.ai/onnx/technical/kv_cache.html>)
- Performance and pricing results are self-reported with limited third-party benchmarks or customer proofs [E9 · self-reported](<https://onetriangle.ai/demo>) [E10 · self-reported](<https://onetriangle.ai/models>) [E6 · self-reported](<https://onetriangle.ai/blog>)
- Intent to upstream into vLLM could erode defensibility if core methods become widely available (self-reported) [E15 · self-reported](<https://www.ycombinator.com/companies/onetriangle>)

## What would change the decision
- Are there production customers and independent third-party benchmarks or case studies validating cost/latency and quality claims?
- What are the failure modes across model pairs, when does the system revert to native prefill, and how is quality regression monitored in production?
- What is the current security and compliance posture (e.g., SOC 2/ISO 27001), data handling practices, and PII safeguards for managed inference?

**Recommendation: Pass**
