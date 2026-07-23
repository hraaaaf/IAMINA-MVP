# IAmina — Fable Business-Case Assessment

**Date:** 2026-06-12
**Companion to:** `fable-assessment.md` (16-dimension engineering review, 7.6/10)
**Scope:** the *idea and the business*, not the code. Two questions: **Is it a good idea? Is it well executed as a business?**
**Method:** Full read of the strategy record (ROADMAP.md, `v3.1-modular-monolith.md`, ADR-0008, platform-transformation-plan, MEDICAL_DATA_PLAN, CLAUDE.md session history) cross-checked against what the code actually does today. External market facts come from model training knowledge (cutoff Jan 2026) because web research was unavailable in this session — every such figure is marked **[unverified]** and should be re-sourced before being shown to an investor.

---

## 1. Scorecard

| # | Dimension | Score | One-line verdict |
|---|-----------|:-----:|------------------|
| 1 | Problem & need | **8.5** | Real, large, underserved: high diabetes prevalence + a genuine Darija content vacuum |
| 2 | Target-user clarity | **7.5** | "Moroccan Darija-speaking person with diabetes" is sharp; persona depth (age, T1/T2, payer) is not |
| 3 | Differentiation / moat | **6.0** | Darija-native warmth is a real wedge but a thin moat in the LLM era; safety layer is the more defensible asset |
| 4 | Beachhead choice (Morocco) | **7.0** | Right for learning and CAC, weak for revenue — and the docs know it (Morocco is explicitly not the monetization market) |
| 5 | Expansion logic (Gulf + pharma B2B) | **6.0** | Directionally credible, supported by precedent — but asserted, not evidenced; Gulf has incumbents and regulators |
| 6 | Retention thesis | **7.0** | The right central hypothesis, honestly framed as unproven — but the instrument to test it is still unbuilt |
| 7 | Business model / monetization | **4.0** | No pricing hypothesis, no unit economics, no named prospect; "who pays" is a slide, not a plan |
| 8 | Competition awareness | **4.0** | Zero documented competitive analysis; the landscape (mySugr, Droobi, GluCare, generic ChatGPT) is never named |
| 9 | Regulatory positioning | **8.0** | Companion-not-device is well-argued and *enforced in code* — unusually strong; Gulf-specific pathway unexamined |
| 10 | Validation evidence | **2.5** | No deployment, no real users, no customer conversations — every business claim is still a hypothesis |
| 11 | Go-to-market & distribution | **3.0** | Not started: staging undeployed (Phase 14 🔴), mobile auth stubbed (Phase 15 🔴), no pilot pipeline |
| 12 | Unit economics & cost structure | **4.5** | LLM-per-user costs unmodeled; currently riding Gemini quota with a fallback — fine for POC, unexamined as a business |
| 13 | Strategy discipline | **7.5** | The Retention Gate is genuinely good governance; the ADR-0008 reversal eroded it honestly but eroded it |
| 14 | Execution alignment (build ⇄ business) | **5.0** | Six months of building, ~zero of selling/measuring; the two business-critical gaps (Arabic UX, retention loop) are the least-built |
| | **Overall (weighted judgment)** | **5.7** | **A good idea, half-executed: the product is built, the business has not started** |

(For calibration: the engineering review scored 7.6. The 2-point gap *is* the finding.)

---

## 2. The two answers

### Is it a good idea? — Yes, conditionally.

The core insight is sound and the docs articulate it better than most funded startups: diabetes prevalence in Morocco is high (IDF-class estimates put adult prevalence around 10–13%, with roughly half undiagnosed **[unverified]**), Arabic-language — and especially Darija-language — diabetes support content is close to nonexistent, and the Gulf combines world-leading prevalence (~17–25% adult in Saudi/Kuwait/Qatar **[unverified]**) with high willingness to pay. "Companion, not medical device" is exactly the right regulatory wedge for a small team, and the codebase enforces that wedge structurally (triage middleware, no-diagnosis invariants) rather than just claiming it. The retention framing is also correct: diabetes apps do churn at 70–80%+ **[unverified but consistent with published health-app literature]**, and an emotionally warm, dialect-native companion is a plausible — not proven — answer.

The conditions: (a) the Darija moat is thinner than the docs assume — frontier LLMs already speak passable Darija, so the durable asset is the *clinical safety layer + trust + local distribution*, not the language itself; (b) the monetization story has two hops (Morocco → Gulf, consumer → pharma) and zero evidence on either hop; (c) the precedents that prove "diabetes companion" can be a business (Livongo's $18.5B Teladoc merger, Roche buying mySugr, Omada **[unverified]**) all paired software with hardware, human coaching, or payer integration — pure-software chat companions have a weaker track record.

### Is it well executed? — As engineering, yes. As a business, not yet — and the gap is widening.

The strategy record itself defines the test: *"You cannot improve a retention number you don't instrument"* (v3.1 memo), and Phase 16 is marked **TOP PRIORITY — gates everything** in the roadmap. Sixty-plus days after that was written, Phase 16 is still 🔴, the D90 threshold is still a placeholder awaiting a founder decision, staging has never been deployed, mobile Firebase config is still stubs, and the most-used screen still shows hardcoded French to a notionally Darija-first user. Meanwhile P0→P8.1 of platform chassis work — which ADR-0008 itself concedes is "overhead for a single-module system" and "sunk cost if the gate never passes" — got executed with precision. The project is running its *deferred* track instead of its *gating* track.

---

## 3. Dimension-by-dimension reasoning

### 3.1 Problem & need — 8.5

The need is real on three axes at once: epidemiological (high and rising prevalence in Morocco and the Maghreb **[unverified]**), linguistic (diabetes education content in Darija is essentially absent; even MSA Arabic content is thin and not how Moroccans actually speak), and cultural (the engine already handles Ramadan logging — Iftar/Suhoor meal moments — and Moroccan foods like harira and msemen, which no global app does). The clinical engine's localization choices (Moroccan food vocabulary, Darija fallback strings for all detectors, ar-MA triage keywords) show the team understands the user's life, not just their glucose. This is the strongest part of the whole case.

### 3.2 Target-user clarity — 7.5

Sharp at the headline ("Darija-speaking Moroccan with diabetes"), fuzzy underneath. The docs never commit to: Type 1 vs Type 2 (very different products — T2 is ~90% of the market and is a lifestyle/adherence problem, which fits the companion thesis better), age band and smartphone fluency, urban vs rural, or who in the family actually manages the condition (in Morocco, often a daughter or son manages a parent's diabetes — a "caregiver mode" question the docs never raise). No persona doc, no user-research artifact, no interview notes exist anywhere in the repo.

### 3.3 Differentiation / moat — 6.0

What's claimed: Darija = CAC edge, companion warmth = retention edge. What's true: both are real *wedges* but weak *moats*. Gemini/GPT-class models speak Darija today; a competitor (or a patient with ChatGPT) can get 70% of the conversational value free. The defensible assets are actually: (1) the clinical safety layer — triage registry, unit guard, fixed emergency responses — which generic LLMs categorically don't have and which becomes the credibility story with pharma/regulators; (2) accumulated longitudinal patient data + the deep-memory relationship (streaks, learned food sensitivities, relational stages); (3) eventual local distribution (pharmacies, CHU endocrinology services, associations like the Ligue Marocaine de Lutte contre le Diabète **[unverified existence/name]**). The docs lean on the weakest of the three.

### 3.4 Beachhead choice — 7.0

Morocco is the right *learning* market: cheap to operate, founder's home ground, underserved enough that a good free product can win attention. It is a bad *revenue* market — out-of-pocket health spending is high relative to income and consumer app-subscription willingness is low **[unverified]**; AMO/CNSS coverage expansion is recent and does not pay for apps. The strategy docs are commendably honest about this (monetization explicitly deferred to Gulf + pharma). The risk they don't price in: a free Moroccan user base must be *funded* through the entire validation period, with LLM inference costs per active chat user, before any revenue exists.

### 3.5 Expansion logic — 6.0

Gulf consumer + pharma B2B is directionally right and has regional precedent: Qatar's Droobi Health built a B2B2C model with payers/providers, GluCare in UAE runs a clinic-plus-continuous-monitoring model, and pharma companies do fund patient-support and adherence programs in MENA **[all unverified]**. But each precedent also shows the bar: Gulf entries went through institutional channels (regulators, insurers, clinics), not app-store consumer launches; and pharma adherence budgets buy *programs with evidence*, meaning IAmina needs retention + engagement data (the unbuilt Phase 16, again) before any pharma conversation converts. The roadmap's own "Open Decisions" table lists the first payer channel as "Probe pharma adherence" — a verb that, per the repo, no one has performed.

### 3.6 Retention thesis — 7.0

This is the project's intellectual spine and it's correctly framed: a falsifiable hypothesis (companion design beats 70–80% churn), a defined instrument (D1/D7/D30/D90 cohorts, drop-off funnel, chat-messages-per-active-patient as the differentiation signal), and a go/no-go gate. Two deductions: the instrument is unbuilt (events code exists from S4, the dashboard endpoint is partial, the threshold is a placeholder); and there's no interim proxy — with zero deployed users, even D7 data is months away, yet nothing in the docs plans for a small-cohort pilot (e.g., 30 patients via one endocrinologist) to get *any* retention signal early.

### 3.7 Business model / monetization — 4.0

The weakest dimension. Nowhere in ~12 architecture/strategy docs is there: a pricing hypothesis (consumer subscription price point in the Gulf? per-patient-per-month for pharma?), a revenue model sketch, a cost-per-user estimate, a named prospective customer, or a record of a single conversation with a pharma company, insurer, or clinic. "Gulf willingness-to-pay + pharma adherence budgets" is a true statement about the world, not a business model. For a project this rigorous about ADRs, the absence of even a one-page "who pays what for what" memo is the loudest silence in the repo.

### 3.8 Competition awareness — 4.0

No competitor is named in any document. The landscape that should be on one page: **mySugr** (Roche; global, Arabic availability limited **[unverified]**), **Droobi Health** (Qatar, Arabic-first diabetes management, payer-integrated), **GluCare** (UAE, clinic + CGM hybrid), Saudi digital-health programs under SEHA/NPHIES **[unverified]**, and — most importantly — **generic LLM chat** as the free substitute every smartphone user already has. Nothing here is fatal to IAmina (none serve Darija; none are companion-first), but "we checked and here's why we win" is table stakes for the pharma/investor conversations the strategy depends on.

### 3.9 Regulatory positioning — 8.0

The strongest *executed* business work in the repo, because it lives in code: no diagnosis, no prescription (a P0 fix removed an insulin-prescription suggestion from a detector), fixed pre-validated emergency responses that never touch the LLM, medical disclaimers on every AI response, RGPD/Law 09-08-compatible consent + erasure machinery. This positioning is viable in Morocco (no meaningful digital-health-app regulation as of cutoff **[unverified]**) and keeps the door open in the Gulf — though Saudi SFDA and UAE health authorities have active software-as-medical-device frameworks, and the moment a pharma program touches outcomes claims, the "wellness companion" badge gets scrutinized **[unverified]**. That Gulf-specific regulatory homework is unstarted, hence not a 9.

### 3.10 Validation evidence — 2.5

The hard truth: after ~6 months of building, the number of real patients who have used IAmina is, as far as the entire repo shows, **zero**. No staging environment (Phase 14 🔴), no mobile app distribution (Phase 15 🔴 — Firebase configs are stubs), no pilot, no waitlist, no user interviews, no letters of intent. Every score above 5 in this report rests on reasoning, not evidence. The only "validation" artifacts are demo data and 764 tests. The 2.5 (not lower) reflects that the *plan* to validate exists and is well-designed.

### 3.11 Go-to-market & distribution — 3.0

No distribution thinking is documented: how does a Moroccan T2 patient discover IAmina? (Facebook/WhatsApp health groups, pharmacist recommendation, endocrinologist referral, Ramadan-season content marketing — all plausible, none discussed.) The staging-deploy decision is "pending decision with the associé," which has held since at least early June. A product whose #1 metric is 90-day retention needs day-zero users to start the 90-day clock; every week undeployed pushes the gate decision a week into the future at minimum.

### 3.12 Unit economics — 4.5

Currently the app runs on Gemini 2.5 Flash with a quota guard and a planned Kimi failover (key pending for months). There is no estimate of: LLM cost per active patient per month (chat + thinking mode at 2048 tokens + vision OCR + document parsing add up), infra cost at 1k/10k users, or what those imply for a free Moroccan user base. Mitigating: Flash-class pricing is cheap, the pipeline caches aggressively, and a fallback exists. But "can we afford 10,000 free Moroccan users for a year" is a number the founder should know and doesn't have written anywhere.

### 3.13 Strategy discipline — 7.5

Genuinely above-average: a locked product strategy with explicit "not doing" lists, a falsifiable gate, ADRs that record *reversals* with their reasoning (ADR-0008 even lists "if the gate never passes, the chassis is sunk cost" under its own trade-offs — rare honesty). One real deduction: the 2026-06-03 memo said "stop spending on extensibility, start spending on measurement"; on 2026-06-04 — one day later — the founder reversed into platform-chassis work, and the subsequent ~8 phases (P0→P8.1) all went to extensibility while Phase 16 stayed at zero. The gate survived on paper; the *budget reallocation* it demanded did not.

### 3.14 Execution alignment — 5.0

The summary table of the misalignment:

| The business says | The repo shows |
|---|---|
| #1 metric: D90 retention, "gates everything" | Phase 16 🔴 not started; dashboard partial; threshold placeholder |
| Darija/Arabic-first is the differentiator | Hardcoded French clinical strings; no RTL scaffold (eng. review §3.11) |
| Morocco beachhead, get users | Never deployed; mobile auth stubbed; no pilot |
| Pharma B2B is the payer | No outreach, no pipeline, no evidence pack |
| Platform machinery: deferred until gate passes | P0–P8.1 chassis executed, CI-enforced |

The work done is *good* — disciplined, reversible, honestly tracked. It's the wrong work *first*, by the strategy's own ranking.

---

## 4. The risk register the docs don't have

1. **Validation starvation (existential, certain unless acted on).** The gate cannot pass or fail without users; every month pre-deployment is a month the central hypothesis stays untested while LLM commoditization erodes the wedge.
2. **Free-substitute risk (high).** ChatGPT/Gemini speak Darija and are free. IAmina's answer must be safety + memory + clinical structure — that story needs to be sharpened *now*, in product and pitch.
3. **Two-hop monetization risk (high).** Morocco proves retention → Gulf/pharma pays. If Moroccan retention data doesn't impress Gulf payers (different population, different care context), the bridge is weaker than assumed.
4. **Pharma evidence bar (medium).** Adherence programs buy outcomes evidence. Plan the data package (retention + engagement + logging adherence deltas) as a *product*, not a by-product.
5. **Solo-founder + associé decision latency (medium).** Two phases (7, 14) have been blocked "pending decision with the associé" for weeks. Decision bottlenecks on deployment are now the project's critical path.
6. **Regulatory drift on outcomes claims (low now, medium at pharma stage).** The companion badge holds only while marketing matches it; the first pharma deck promising "improved adherence" invites device-classification questions in SFDA-land.

---

## 5. Prioritized recommendations (business, not code)

| Priority | Action | Why |
|:--------:|--------|-----|
| **P0** | **Deploy staging and put the app in 20–30 real patients' hands** (one endocrinologist or diabetes association is enough) | Starts the only clock that matters; converts every score in §3.10 from 2.5 toward evidence |
| **P0** | Finish Phase 16 + set a provisional D90 threshold *this week* (25% is fine; a provisional gate beats a perfect placeholder) | The strategy's own #1 priority, 60+ days overdue |
| **P0** | Fix Arabic/RTL + French-string extraction before the pilot | Piloting a Darija companion in French invalidates the pilot's retention read |
| **P1** | Write the one-page monetization memo: pricing hypothesis per channel, cost-per-user estimate, 3 named pharma/insurer targets in Morocco/Gulf | Turns "who pays" from slide to plan; forces the unit-economics math |
| **P1** | Have 5 conversations: 3 endocrinologists/pharmacists (distribution), 2 pharma patient-support managers (payer) — log them in `docs/` like ADRs | Cheapest possible validation; the repo's documentation discipline applied to the market |
| **P1** | One-page competitive landscape (mySugr, Droobi, GluCare, generic LLMs) with the "why we win in Darija" argument written down | Needed for every payer/investor conversation anyway |
| **P2** | Re-source every market figure with live citations (this report's [unverified] tags) before external use | Web research was unavailable for this assessment; numbers are training-knowledge ballparks |
| **P2** | Freeze all further chassis work until the gate has data (re-affirm DA-03's budget rule, post-ADR-0008) | The architecture is done enough; its ROI now depends entirely on user evidence |

---

## 6. Bottom line

**Good idea: yes** — a real epidemic, a genuine language gap, the right regulatory wedge, and a falsifiable retention thesis, undermined mainly by a thinner-than-claimed language moat and a two-hop path to revenue.

**Well executed: half.** The half that's executed (product, safety, architecture, documentation) is excellent — 7.6/10 by its own engineering review. The half that decides whether this is a business — users, measurement, payer evidence, distribution — is at or near zero after six months, **5.7/10 overall**, and the strategy documents themselves predicted this failure mode and prohibited it (*"energy goes to Phase 16, not extensibility machinery"*). The fix is not more building. It is: deploy, recruit ~30 patients, finish the retention loop, fix the Arabic experience, and have five market conversations. Roughly three weeks of work, none of it architectural — and at the end of it, every hypothesis in this report starts becoming a fact.
