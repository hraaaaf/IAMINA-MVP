# P5-1 — Morocco linguistic certification closeout

> **Status:** CLOSED / HUMAN_APPROVED / EXACT_MAIN_V8_PACKET_RETAINED  
> **Closed:** 2026-09-12  
> **Authoritative tracker:** issue #515  
> **Exact-main evidence SHA:** `2d18428a0c59a18c82a1c0dfb410469f17f81e04`

## Goal

Certify the patient-facing language set selected for the Morocco PWA pilot without weakening deterministic clinical/safety authority and without confusing machine review with human linguistic approval.

## Success criteria

P5-1 closes only when:

1. the final Morocco contract is merged on `main`;
2. post-merge CI and migration drift are green;
3. an exact-main workflow-dispatch linguistic packet is retained;
4. the packet is synthetic/non-patient, one bounded provider call, and machine-PASS;
5. a retained human verdict explicitly approves the five current Morocco lanes;
6. no legal/CNDP, clinical-release, deployment or real-patient approval is inferred from this linguistic gate.

## Retained engineering evidence

Final remediation PR: #579.

Exact-main evidence:

- `main@2d18428a0c59a18c82a1c0dfb410469f17f81e04`;
- post-merge CI #34682380854 — SUCCESS;
- post-merge Django migration drift #34682380897 — SUCCESS;
- exact-main workflow-dispatch packet #34683056185 — SUCCESS;
- artifact #10295285314;
- digest `sha256:496d2aae06ab3f9cea934f93d37a461a228433aca91dff9f67cad04e040a751b`;
- dataset `iamina-p5-1-current-sha-linguistic-review-v8`;
- machine PASS 10/10;
- one Groq call;
- actual worst-case reported cost 531 µUSD;
- `synthetic=true`;
- `patient_data=false`.

## Retained human verdict

The repository owner/user explicitly approved the five final Morocco lanes on 2026-09-12 after the exact-main v8 packet was retained.

Approved set:

- FR: `Pas de souci, demain tu peux reprendre.`
- MSA: `لا تقلق، يمكنك العودة غداً دون أي ضغط.`
- Darija Arabic: `ما تقلقش، تقدر ترجع غدا بلا ضغط.`
- Darija Latin: `t9der terja3 ghdda bla daght w bla lom`
- FR↔Darija: `Pas de souci ما تقلقش، غدا نرجع بلا ضغط.`

Earlier retained human feedback rejected `ما تشدش...` in Darija Arabic and ambiguous first-person-plural `nrj3` in Darija Latin. v8 encoded those findings and the exact-main packet retained `retained_human_darija_feedback=true` for the corrected Darija lanes.

## Certification boundary

This closeout records a retained human approval plus exact-main machine evidence. It does not fabricate a machine-produced `native_speaker_certified=true` field. The human verdict retained in issue #515 is the authoritative human evidence for P5-1 closure.

Gulf expansion lanes remain deferred unless explicitly exposed in the selected pilot scope.

## Non-claims

P5-1 closure does **not** authorize:

- real-patient processing;
- clinical corpus approval under #318;
- CNDP/legal/processor/residency approval under #320;
- Vercel or other production deployment;
- provider cutover;
- native Android/iOS release readiness.

## Handoff to P5-6

P5-1 closure raises Pilot Readiness from 3/9 to 4/9 = 44.4% because P5-1 is now a closed whole lot. The retained MENA arithmetic remains 32/38 until its own canonical arithmetic is explicitly reconciled.

After this documentation closeout is merged and exact-main CI is green, freeze the resulting `main` SHA as the P5-6 candidate in issues #318 and #320. P5-6 remains `NOT_RELEASE_AUTHORIZED` until both external gates, all three exact-SHA approved audits and an explicit human release decision pass.
