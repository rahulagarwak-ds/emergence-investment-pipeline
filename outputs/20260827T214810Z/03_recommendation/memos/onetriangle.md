# OneTriangle

**Thesis score:** 54/100  
**Evidence coverage:** 80%

## Rationale
- Technique is rapidly commoditizing: NVIDIA is productizing KV transfer and media/academic coverage shows fast follower momentum, limiting differentiation and pricing power. [E16](<https://nvidia.github.io/TensorRT-LLM/developer-guide/kv-transfer.html>) [E17](<https://venturebeat.com/technology/nvidia-finds-that-simple-linear-math-can-replace-costly-ai-model-handoffs>) [E18](<https://arxiv.org/abs/2608.03893>) [E20](<https://onnx.ai/onnx/technical/kv_cache.html>)
- Performance and pricing gains are primarily self-reported with no independent, third-party benchmarks or customer proof points. [E9 · self-reported](<https://onetriangle.ai/demo>) [E10 · self-reported](<https://onetriangle.ai/models>) [E6 · self-reported](<https://onetriangle.ai/blog>)
- Stated plan to upstream into vLLM could disseminate the approach broadly, weakening moat and margins if widely adopted. [E15 · self-reported](<https://www.ycombinator.com/companies/onetriangle>)

## Key risks
- Incumbent platforms integrating KV transfer may outpace a startup’s defensibility and compress margins. [E16](<https://nvidia.github.io/TensorRT-LLM/developer-guide/kv-transfer.html>) [E17](<https://venturebeat.com/technology/nvidia-finds-that-simple-linear-math-can-replace-costly-ai-model-handoffs>)
- Open standards for KV cache interfaces reduce switching costs and enable rapid replication by larger providers. [E20](<https://onnx.ai/onnx/technical/kv_cache.html>)
- Lack of independent validation of claimed speed/cost improvements increases uncertainty on real-world impact. [E9 · self-reported](<https://onetriangle.ai/demo>) [E10 · self-reported](<https://onetriangle.ai/models>) [E6 · self-reported](<https://onetriangle.ai/blog>)

## What would change the decision
- Are there production customers and independent third-party benchmarks or case studies validating the claimed speed and cost improvements?
- What are the failure modes across different model pairs, and how are quality regressions detected and mitigated in production?
- Is the company procurement-ready with enterprise SLAs/SLOs, security certifications (e.g., SOC 2/ISO 27001), and data residency options?

**Recommendation: Pass**
