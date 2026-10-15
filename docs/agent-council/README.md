## 15 October 2026 — audited infrastructure closeout (NOT model audit)

**Goal / success / evidence.** Prepare a complete 15-specialist IAMINA audit *system* without granting write or patient-data access. Success for this infrastructure lot = exact 15 specialist profiles + coordinator + skill + deterministic baseline CI + hardened permissions on `main`, all backed by readback and workflows; **not** 15 finished medical/security reviews.

**Verified:**
- [PR #1028](https://github.com/hraaaaf/IAMINA-MVP/pull/1028) **MERGED** at `e9e2eedba109fef062fb2603b9cab1e0710f0bb2`: 15 Copilot specialist prompts + coordinator, Agent Skills-compatible `SKILL.md`, readme and Python evidence checks / workflow. [Exact-head CI #38699624901](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38699624901) **SUCCESS**, [council #38699624947](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38699624947) **SUCCESS**; test + fifteen individual **STATIC PROBES** + artifact `11954324864`. Report identifies **`llm_subagents_executed: 0`**, `release_verdict: NOT_CERTIFIED`.
- [PR #1030](https://github.com/hraaaaf/IAMINA-MVP/pull/1030) **MERGED** at `cbf7871a4a170ec608bf086446a859f606a35e07`: all 15 specialist profiles now restrict to `read/search/web`, the coordinator to `read/search/web/agent`, and all 16 require `include-custom-instructions: true` to inherit `AGENTS.md` when spawned as subagents. [Council #38700149413](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38700149413) and [CI #38700149354](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38700149354) **SUCCESS** on exact PR head `118441da`. [Main CI #38700199388](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38700199388) was **IN_PROGRESS** at initial postmerge check; reread conclusion before final gate.
- Official source documentation checked: [GitHub Copilot CLI custom agents](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli), [tool aliases and least privilege](https://docs.github.com/en/copilot/reference/custom-agents-configuration), [Agent Skills specification](https://agentskills.io/specification).

**Open execution gate — [issue #1029](https://github.com/hraaaaf/IAMINA-MVP/issues/1029):** all fifteen **actual AI subagent runs NOT STARTED**. Only a connected Copilot CLI or similarly capable orchestrator can provide fifteen distinct run/session IDs. The registered Remote Desktop Commander Windows device was OFFLINE when checked; Notion agent sessions are not enabled for this connection. No fake independence claim. The user explicitly prefers subagents instead of human specialists for exploratory review; this **does not waive any clinical or regulatory authority required for releasing real-patient use**.

**Next exact:** connect a subagent-capable runtime to this GitHub repo, run `iamina-council-coordinator` with immutable `main` HEAD, delegate IA01–IA15 under read-only policies, record actual session IDs and each `SHA:path:line` finding; IA15 rechecks the findings adversarially. Publish fifteen reports and a contradictions/risk register, then exact-head CI, separate certifier review, merge/postmerge. No Vercel production deployment without owner approval.

**Project P5 historical progress remains 50%**, not recalculated from infrastructure implementation.

---

# IAMINA Full-Application Agent Council — 15 domains

This council is a **tooling layer**, not a new authority replacing `AGENTS.md`. GitHub Copilot custom agents are in `.github/agents/iamina-ia*.md`; `.agents/` keeps its existing seven canonical Builder/Reviewer/Certifier briefs; `.skills/full-app-agent-council/SKILL.md` is the orchestration skill. The user supplied an Oct 4 `SKILLS.md` document marked **draft, not canonical**; its 15-role taxonomy was adapted only for this scoped execution.

**Profiles**: IA01-ARCHITECTURE, IA02-CLINICAL-SAFETY, IA03-DIABETES-CLINICAL, IA04-CGM-METRICS, IA05-MEDICATION, IA06-NUTRITION, IA07-MENA-LANGUAGE, IA08-SECURITY-PRIVACY, IA09-DATA-OFFLINE, IA10-COMPANION-AI, IA11-QA-VERIFICATION, IA12-UX-ACCESSIBILITY, IA13-RELEASE-OPS, IA14-REGULATORY-QMS, IA15-ADVERSARIAL plus `iamina-council-coordinator`.

**Full app:** Flutter mobile+web, Django/Ninja/Postgres, Drift offline, diabetes deterministic safety, glucose/CGM, medicines, nutrition, MENA, AI/egress, UX, CI, compliance. Each role must report SHA:path:line and whether actually executed.

**Start** in a Copilot CLI/other agent runtime supporting sub-agents: assign `iamina-council-coordinator` the prompt « Run fifteen isolated read-only specialist reviews across all of IAMINA at exact main HEAD. Apply online official references and matching skills, attach evidence; never deploy/edit patients' data; mark human gates. » All fifteen specialist contexts are required for a genuine agent-council result.

**Deterministic baseline**: run `python3 scripts/ci_full_app_agent_council.py --all --output-dir artifacts/full-app-council` or the GitHub Action `IAMINA full app council baseline`. It produces 15 **static evidence probes**, not 15 LLM agent sessions; report this limitation explicitly. No verdict of clinical production readiness is implied.

**Official references**: https://agentskills.io/specification | https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-custom-agents | https://mas.owasp.org/MASVS/ | https://www.nist.gov/itl/ai-risk-management-framework | https://professional.diabetes.org/standards-of-care | https://www.w3.org/TR/WCAG22/ | https://www.iso.org/standard/72704.html | https://www.cndp.ma/images/lois/Loi-09-08-Fr.pdf.
