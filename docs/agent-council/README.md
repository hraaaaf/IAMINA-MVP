# IAMINA Full-Application Agent Council — 15 domains

This council is a **tooling layer**, not a new authority replacing `AGENTS.md`. GitHub Copilot custom agents are in `.github/agents/iamina-ia*.md`; `.agents/` keeps its existing seven canonical Builder/Reviewer/Certifier briefs; `.skills/full-app-agent-council/SKILL.md` is the orchestration skill. The user supplied an Oct 4 `SKILLS.md` document marked **draft, not canonical**; its 15-role taxonomy was adapted only for this scoped execution.

**Profiles**: IA01-ARCHITECTURE, IA02-CLINICAL-SAFETY, IA03-DIABETES-CLINICAL, IA04-CGM-METRICS, IA05-MEDICATION, IA06-NUTRITION, IA07-MENA-LANGUAGE, IA08-SECURITY-PRIVACY, IA09-DATA-OFFLINE, IA10-COMPANION-AI, IA11-QA-VERIFICATION, IA12-UX-ACCESSIBILITY, IA13-RELEASE-OPS, IA14-REGULATORY-QMS, IA15-ADVERSARIAL plus `iamina-council-coordinator`.

**Full app:** Flutter mobile+web, Django/Ninja/Postgres, Drift offline, diabetes deterministic safety, glucose/CGM, medicines, nutrition, MENA, AI/egress, UX, CI, compliance. Each role must report SHA:path:line and whether actually executed.

**Start** in a Copilot CLI/other agent runtime supporting sub-agents: assign `iamina-council-coordinator` the prompt « Run fifteen isolated read-only specialist reviews across all of IAMINA at exact main HEAD. Apply online official references and matching skills, attach evidence; never deploy/edit patients' data; mark human gates. » All fifteen specialist contexts are required for a genuine agent-council result.

**Deterministic baseline**: run `python3 scripts/ci_full_app_agent_council.py --all --output-dir artifacts/full-app-council` or the GitHub Action `IAMINA full app council baseline`. It produces 15 **static evidence probes**, not 15 LLM agent sessions; report this limitation explicitly. No verdict of clinical production readiness is implied.

**Official references**: https://agentskills.io/specification | https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-custom-agents | https://mas.owasp.org/MASVS/ | https://www.nist.gov/itl/ai-risk-management-framework | https://professional.diabetes.org/standards-of-care | https://www.w3.org/TR/WCAG22/ | https://www.iso.org/standard/72704.html | https://www.cndp.ma/images/lois/Loi-09-08-Fr.pdf.
