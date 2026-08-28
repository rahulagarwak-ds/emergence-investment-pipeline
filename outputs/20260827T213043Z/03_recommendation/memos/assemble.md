# Assemble

**Thesis score:** 48/100  
**Evidence coverage:** 100%

## Rationale
- Real-world production use is unproven; Trailhead results are an early step and the team notes real enterprise environments are harder. [ev_blog_real_envs_harder · self-reported](<https://www.assemble.ai/blog/building-ai-salesforce-architects>) [ev_blog_trailhead_results · self-reported](<https://www.assemble.ai/blog/building-ai-salesforce-architects>)
- Go-to-market and procurement specifics (pricing, motion, data boundaries) are not specified publicly, creating uncertainty on enterprise adoption path. [ev_site_value_prop · self-reported](<https://www.assemble.ai/>) [ev_careers_roles · self-reported](<https://www.assemble.ai/careers>)
- Very early-stage company (founded 2026, team size 4) despite strong founder pedigrees, implying product and process immaturity. [ev_yc_meta · self-reported](<https://www.ycombinator.com/companies/assemble>) [ev_yc_founders · self-reported](<https://www.ycombinator.com/companies/assemble>)

## Key risks
- Operating agents inside mission-critical systems (Salesforce, SAP, Workday, etc.) demands robust safety, auditability, and rollbacks; any gaps could create high-severity incidents. [ev_site_trust_security · self-reported](<https://www.assemble.ai/>) [ev_site_integrations · self-reported](<https://www.assemble.ai/>)
- Unclear security/compliance posture (e.g., SOC 2) and deployment model could stall enterprise procurement. [ev_site_value_prop · self-reported](<https://www.assemble.ai/>) [ev_careers_roles · self-reported](<https://www.assemble.ai/careers>)
- Breadth of connectors appears aspirational; unclear which are GA vs. roadmap, risking limited early utility beyond Salesforce. [ev_site_integrations · self-reported](<https://www.assemble.ai/>) [ev_blog_real_envs_harder · self-reported](<https://www.assemble.ai/blog/building-ai-salesforce-architects>)

## What would change the decision
- Who are current design partners or paying customers, and what measurable outcomes have they achieved?
- What security/compliance certifications are in place and what deployment options are supported (SaaS, private cloud, in-tenant)?
- Which connectors are GA today versus roadmap, and what is the typical onboarding path?

**Recommendation: Pass**
