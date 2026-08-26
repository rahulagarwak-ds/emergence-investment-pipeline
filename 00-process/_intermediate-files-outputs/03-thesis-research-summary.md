
# Thesis research done by google and summarised by ChatGPT

1. The underlying market: B2B SaaS

B2B SaaS has several distinct go-to-market models. Traditional enterprise software is sales-led: lead generation → SDR → discovery → demo/POC → negotiation/legal → contract → onboarding → renewal. The source you provided estimates an average B2B SaaS sales cycle around 84 days, with enterprise deals commonly taking 90–180 days because of larger buying committees, legal requirements and compliance.  

At the other end is Product-Led Growth (PLG):

Traditional enterprise
Vendor → Sales → Buyer → Security/IT → Legal → Procurement → Contract → User
Product-led / bottom-up
Product → Individual user → Repeated usage → Team adoption → Company → Commercial agreement

In PLG, the product itself performs much of the acquisition and qualification work. Free trials, freemium tiers and usage signals replace some of the traditional early sales process. The RemoteReps source describes 15–25% free-trial conversion as a benchmark for strong PLG motions, although I would treat vendor-published benchmarks as directional rather than authoritative market statistics.  

2. Why enterprise purchasing creates friction

Enterprise software isn’t simply bought by the person using it.

There can be several stakeholders:

End user
   ↓
Manager / champion
   ↓
Technical evaluator / IT
   ↓
Security
   ↓
Economic buyer
   ↓
Legal
   ↓
Procurement

B2B SaaS therefore has an unusual buyer/user problem: the person choosing or approving software may not be the person who uses it every day. Good B2B products eventually need to satisfy everyday users while also providing administration, permissions, auditability, SSO, security and other organizational controls.  

Procurement isn’t the only friction. Pricing opacity, mandatory account creation, limited payment methods and poor buying experiences can all cause B2B purchases to stall before contracting.  

So there are really two different frictions:

ADOPTION FRICTION
Can I start using this product?
COMMERCIAL FRICTION
Can my company officially buy this product?

That distinction is important.

3. SaaS fundamentally changed adoption friction

Historically, employees couldn’t easily introduce enterprise technology themselves.

Cloud and SaaS changed that.

IBM points out that modern SaaS can often be deployed by someone with little technical knowledge, sometimes with nothing more than a credit card. Productivity, collaboration, communication and storage applications can consequently enter companies without centralized IT deployment.  

This creates the possibility of:

Discover
   ↓
Sign up
   ↓
Get value
   ↓
Continue using
   ↓
Invite colleagues
   ↓
Team dependency develops

before formal enterprise purchasing occurs.

That phenomenon is not theoretical. It is part of the broader shadow IT problem.

⸻

4. Shadow IT is the extreme expression of bottom-up adoption

Shadow IT means technology being used inside an organization without normal IT approval or oversight.

The CIO article cites Gartner estimates that shadow IT represented 30–40% of IT spending in large enterprises, although importantly that article dates from 2017, so don’t present that number as a current 2026 market statistic.  

IBM describes a similar behavioral mechanism: employees adopt preferred tools because they believe they can work faster or more effectively, while teams sometimes bypass IT because formal procurement is perceived as too slow or burdensome.  

The causal chain described across these sources is roughly:

Employee has a problem
        ↓
Approved solution is inadequate / slow / unavailable
        ↓
Alternative SaaS is easy to access
        ↓
Employee adopts it independently
        ↓
Potential team adoption
        ↓
Shadow IT

The key industry insight isn’t necessarily that employees want to evade procurement.

It’s that employees optimize for getting their job done, while centralized IT optimizes for organizational requirements such as security, cost, standardization and governance.

Those incentives can conflict.

⸻

5. AI has intensified this behavior

This is where the current AI environment becomes particularly relevant.

One of your sources reports a 2025 survey of more than 3,500 knowledge workers in which 78% reported using AI tools their employer had not approved. It also reports 46% saying they would continue despite explicit prohibition.  

The precise percentages should be traced to the underlying surveys before using them as foundational evidence, but the broader behavior is important.

Generative AI has characteristics that make employee-led adoption unusually easy:

Browser accessible
+
Immediate signup
+
Often free/freemium
+
Individual utility
+
Little training
+
Immediate observable output

An employee doesn’t necessarily need their whole department to migrate to obtain value.

That makes AI tools particularly compatible with individual-first adoption.

⸻

6. But shadow adoption creates a serious contradiction

Easy unauthorized adoption is simultaneously a distribution advantage and an enterprise risk.

IBM identifies risks including:

* loss of IT visibility and control
* sensitive-data exposure
* compliance problems
* inconsistent data
* integration problems
* unmanaged infrastructure dependencies  

And organizations increasingly have mechanisms such as Cloud Access Security Brokers (CASBs) that can discover and control cloud services employees use.  

So:

Very easy employee adoption
          ↓
Potentially excellent distribution
BUT
Very easy unauthorized adoption
          ↓
Potential security/compliance problem

A product that literally depends upon staying invisible to IT is therefore structurally vulnerable.

The stronger business model is usually not:

evade enterprise controls forever.

It’s closer to:

Easy individual adoption
        ↓
Prove user value
        ↓
Spread within team
        ↓
Create organizational demand
        ↓
Become governable
        ↓
Enterprise purchase

That last transition matters enormously.

⸻

7. Individual utility alone isn’t sufficient

A product can have excellent bottom-up adoption and still have a poor SaaS business.

Consider:

Employee loves product
Employee uses product every day
Employee pays $10/month
BUT
Nobody else needs it
No shared data
No collaboration
No administration
No organizational control
No enterprise reason to purchase

You’ve created a useful individual SaaS product, but not necessarily an enterprise expansion engine.

For bottom-up B2B, the interesting transition is:

Individual value
      ↓
Repeated use
      ↓
Team value
      ↓
Organizational dependency
      ↓
Enterprise requirements
      ↓
Enterprise monetization

This is consistent with B2B SaaS design itself. As products mature organizationally, permissions, administration, shared data, billing, audit trails and SSO become important because the product is no longer serving only an individual.  

⸻

8. Workflow frequency matters, but frequency isn’t everything

Your source material supports focusing on products embedded in recurring workflows. B2B SaaS design is fundamentally about repeated use over long periods, rather than merely producing an impressive first interaction.  

There are two useful dimensions:

Frequency       ×       Criticality
How often?              How painful is failure?

For example:

Product	Frequency	Criticality
AI writing assistant	Daily	Medium
Developer IDE	Daily	High
Payroll	Monthly	Extremely high
Compliance software	Quarterly	Extremely high

This matters for your eventual scoring framework. A strict rule such as “used less than three times per week = 0” would exclude potentially valuable B2B software simply because the natural business process occurs monthly or quarterly.

So frequency is evidence of habit, but workflow criticality is a separate signal.

⸻

9. Friction can create opportunities for challengers

The “Friction Economy” source argues that incumbents can remain commercially successful while users become increasingly frustrated because organizational switching costs keep customers trapped. New entrants can attack specific workflow frustrations rather than competing feature-for-feature.  

Its examples are useful conceptually:

Figma vs Adobe: browser accessibility, real-time collaboration and eliminating file/version handoffs reduced important workflow friction.  

Linear/Notion vs Atlassian: simpler workflows and templates can encourage bottom-up adoption among users frustrated with incumbent complexity.  

Cursor vs incumbent developer tooling: the author highlights familiar workflows, low switching costs and individual developer adoption as mechanisms that accelerated adoption.  

I’d treat this source as an analytical framework/opinion piece rather than independent empirical research, but the mechanism it describes is relevant.

⸻

10. Procurement doesn’t necessarily disappear

This is probably the most important nuance in your original material.

Bottom-up adoption can delay procurement, create leverage before procurement, or make the eventual purchasing decision easier.

It doesn’t necessarily eliminate procurement.

Once software becomes organizationally important, enterprises may still demand:

Security review
Data processing agreements
SSO
RBAC
Audit logs
Compliance
Data residency
Legal terms
Central billing
Vendor management

There are also alternative ways of reducing procurement friction. For example, cloud marketplaces can let enterprises purchase software against existing AWS/Azure/GCP commitments instead of establishing an entirely new purchasing relationship. The RemoteReps source claims this can materially shorten procurement cycles.  

Therefore there are several possible GTM paths:

Traditional
Sales → Procurement → Deployment → Users
PLG
Users → Adoption → Sales → Procurement → Expansion
Bottom-up enterprise
Individual → Team → Internal champion → Enterprise contract
Marketplace
Vendor → Existing enterprise purchasing channel → Adoption

These are related but not identical models.

⸻

11. The industry picture in one model

The material you’ve collected essentially describes this tension:

                    ENTERPRISE
        Wants                       Employee wants
        -----                       --------------
        Security                    Speed
        Governance                  Convenience
        Compliance                  Best tool
        Standardization             Productivity
        Cost control                Immediate value
        Procurement                 Self-service
                 ↓ conflict ↓
          Traditional IT process
                   vs
          Bottom-up SaaS adoption
                       ↓
              Opportunity for SaaS
        Low adoption friction
                +
        Strong individual value
                +
        Recurring/critical workflow
                +
        Team expansion mechanism
                +
        Enterprise monetization path
                +
        Ability to become governable

That is the industry context I would carry into your thesis work.

One caution: your 11 sources aren’t equal-quality evidence. IBM and CIO are useful for establishing shadow-IT mechanisms; SaaSUI and the Friction Economy piece are useful conceptual material; RemoteReps/Demand Gen are practitioner/vendor material; and the 78% Shadow AI claim should ideally be traced to its original WalkMe/Software AG study before becoming a central quantitative premise. Your thesis will be stronger if you distinguish industry evidence from practitioner interpretation rather than treating [1]–[11] as equally authoritative.  

Sources you supplied:  ⁠IBM on Shadow IT,  ⁠CIO on enterprise Shadow IT,  ⁠Shadow AI research summary,  ⁠B2B SaaS design overview,  ⁠B2B SaaS sales overview,  ⁠Demand Gen on B2B purchasing friction, and  ⁠Friction Economy analysis.