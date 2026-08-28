# Rindler

**Thesis score:** 66/100  
**Evidence coverage:** 100%

## Rationale
- Hosted MCP server is live with simple OAuth PKCE setup (no API key) and optional no-install usage via chat, enabling fast adoption. [docs_quickstart · self-reported](<https://rindler.ai/docs/quickstart>) [docs_browser_mcp · self-reported](<https://rindler.ai/docs/browser-mcp>) [site_faq · self-reported](<https://rindler.ai/faq>)
- Product maps websites into deterministic APIs to make agent web work more reliable versus brittle browser automation. [yc_profile · self-reported](<https://www.ycombinator.com/companies/rindler>) [site_how_it_works · self-reported](<https://rindler.ai/how-it-works>) [site_faq · self-reported](<https://rindler.ai/faq>)
- Plan-based, per-finished-run pricing with Teams/Enterprise tiers suggests a clear monetization model and team workflow fit. [site_pricing · self-reported](<https://rindler.ai/pricing>) [site_faq · self-reported](<https://rindler.ai/faq>)

## Key risks
- Not SOC 2, HIPAA, or PCI certified, which can block enterprise procurement in regulated industries. [site_security · self-reported](<https://rindler.ai/security>)
- Reliance on third-party sites (MFA, bot protections, UI changes) can cause task failures requiring remediation. [yc_profile · self-reported](<https://www.ycombinator.com/companies/rindler>) [site_faq · self-reported](<https://rindler.ai/faq>)
- Early-stage two-person team may face execution and support constraints as integrations scale. [yc_profile · self-reported](<https://www.ycombinator.com/companies/rindler>) [site_about · self-reported](<https://rindler.ai/about>)

## What would change the decision
- What percentage of first-run site mappings succeed without manual intervention, and what is the MTTR when sites change?
- What SLAs (if any) are offered for Enterprise beyond the number of portals kept working commitment?
- Which model providers and regions are supported; can customers bring their own LLM accounts or enforce data residency?

**Recommendation: Pass**
