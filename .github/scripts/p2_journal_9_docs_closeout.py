from pathlib import Path
import sys

root = Path(sys.argv[1])

roadmap = root / 'docs/ROADMAP.md'
text = roadmap.read_text()
replacements = {
    '> **Last updated:** 2026-08-10 — P2-JOURNAL-8 Personal metabolic response is merged and 100% closed; P2-JOURNAL-9 Post-save experience is next.':
        '> **Last updated:** 2026-08-10 — P2-JOURNAL-9 Post-save experience is certified pre-merge in PR #77; Journal metabolic-event redesign is at its final merge unit.',
    '| Journal metabolic-event redesign | 89% | 🟢 P2-JOURNAL-8 closed; P2-JOURNAL-9 next | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6/7 + P2-JOURNAL-8 merged; PR #76 deterministic personal-response patterns; UX 9.3/10; post-merge CI #1383 + drift #1195 green |':
        '| Journal metabolic-event redesign | 100% pre-merge | 🟢 P2-JOURNAL-9 certified; merge/post-merge pending | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6/7 + P2-JOURNAL-8 merged; PR #77 factual post-save receipt; exact-code CI #1387 + drift #1199 green; 16-view FR/AR UX 9.3/10; four specialist reviewer PASSes |',
    '| P2-JOURNAL-9 | Post-save experience | ⬜ Planned | immediate factual confirmation only; longitudinal insights appear separately only when evidence requirements are met |':
        '| P2-JOURNAL-9 | Post-save experience | 🟢 PR #77 merge unit | persistent factual local receipt after successful save; no instant interpretation/advice; mobile next actions remain reachable; longitudinal insights stay separate behind J8 evidence requirements; UX 9.3/10 |',
}
for old, new in replacements.items():
    if text.count(old) != 1:
        raise SystemExit(f'ROADMAP anchor mismatch: {old[:80]}')
    text = text.replace(old, new, 1)

marker = '\n\n---\n\n# P0 visual UX remediation — CLOSED'
section = '''

### P2-JOURNAL-9 durable merge-unit contract

PR #77 is the merge unit for the post-save experience. After the existing Drift insertion succeeds, the Add Log flow now remains on a persistent factual receipt instead of showing a transient snackbar and immediately redirecting away. The receipt restates only the facts just recorded: glucose, timestamp and any explicitly entered measurement context, meal, already-taken insulin and additional context observations. It states only that the entry was saved on the device; it does not claim server synchronization or external persistence.

The receipt does not classify a non-low glucose value as good/bad or inside a personal target, does not call AI, and does not generate prediction, diagnosis, causal explanation, treatment optimization or dose advice. Longitudinal personal-response patterns remain a separate Journal surface governed by P2-JOURNAL-8 evidence requirements. The existing deterministic low-glucose safety classification continues to execute before persistence and is unchanged by this LOT.

After a successful save, the prior draft is cleared before another entry can begin, preventing previous meal/context/insulin facts from being silently reused. The next actions are explicit: **View in Journal / Add another reading / Done**. The first real FR/AR visual pass scored **8.9/10 and was rejected** because a rich receipt on `360×560` pushed all next actions below the fold. The same LOT was remediated so the receipt body scrolls independently while the action panel remains persistently reachable on mobile; Arabic numeric insulin values remain LTR.

**Pre-closeout evidence on product head `ec701826a2f2be6edc075742d3c6d349564b77db`:** canonical CI #1387 SUCCESS; migration drift #1199 SUCCESS; focused FR persistence→render/reset and AR/RTL tests PASS; exact-code visual audit run `31389858816` SUCCESS with 16/16 FR/AR minimal/rich receipt renders across `1440×1000`, `768×1024`, `390×844` and `360×560`; artifact `9063210662`, digest `sha256:62b67588d47b0f5a441f38ebb11cbc362d6e7e56b4e3b8deef0e22213bba77f6`; UX Auditor **9.3/10 PASS**; Clinical Safety, Security/Privacy, Persistence/Database and UX reviewers FINAL PASS; unresolved review threads 0. Canonical documentation changes make these anchors pre-closeout evidence, so exact-final-head recertification, Release Certifier, expected-head merge and post-merge gates remain mandatory before Journal is declared 100% closed.
'''
if text.count(marker) != 1:
    raise SystemExit('ROADMAP closeout insertion marker mismatch')
text = text.replace(marker, section + marker, 1)
roadmap.write_text(text)

specs = root / 'docs/SPECS.md'
text = specs.read_text()
marker = '\n### Insulin logging v2 contract\n'
section = '''
### Post-save experience contract

- a successful Add Log write transitions to a persistent factual receipt only after the local Drift insertion has completed successfully;
- the receipt may restate only the facts from that saved entry: glucose, timestamp and explicitly entered measurement context, meal, already-taken insulin and additional context observations;
- local persistence is described narrowly as saved on the device; this receipt does not imply server synchronization, external backup or provider processing;
- one saved reading must not trigger a good/bad glucose verdict, personal-target claim, prediction, causal explanation, AI analysis, diagnosis, treatment optimization or insulin-dose advice;
- P2-JOURNAL-8 longitudinal personal-response patterns remain separate from the immediate receipt and retain their own minimum-evidence contract;
- after successful insertion, the previous draft is cleared before another entry is started so prior meal/context/insulin facts cannot be silently reused;
- the user can explicitly view the saved entry in Journal, start another reading, or finish; on compact screens those actions remain persistently reachable while receipt detail may scroll;
- FR/EN/AR copy follows the application localization contract and numeric insulin values remain LTR under Arabic RTL.

'''
if text.count(marker) != 1:
    raise SystemExit('SPECS insertion marker mismatch')
text = text.replace(marker, '\n' + section + marker.lstrip('\n'), 1)
specs.write_text(text)

medical = root / 'docs/MEDICAL_DATA_PLAN.md'
text = medical.read_text()
marker = '\n### Ramadan profile context\n'
section = '''
### Immediate post-save presentation

The immediate post-save surface belongs to the **observed / patient-entered data presentation layer**. It may confirm that a local Journal write succeeded and restate the facts just stored, but that success event does not create new clinical meaning. A single saved glucose reading, meal/context label or already-taken insulin quantity must not be turned into a good/bad judgment, causal interpretation, prediction, treatment response estimate, dose recommendation or treatment adjustment.

The storage statement must match the evidence available at that moment. A successful local Drift insertion may be described as saved on the device; it must not be upgraded into a server-sync, cloud-backup or external-processing claim without separate proof. Longitudinal associations remain a different deterministic pattern layer and may surface only through the P2-JOURNAL-8 sufficiency and wording contract. Draft clearing after a successful write is a data-integrity behavior: a subsequent entry starts without silently carrying forward the prior meal/context/insulin observations.

'''
if text.count(marker) != 1:
    raise SystemExit('MEDICAL_DATA_PLAN insertion marker mismatch')
text = text.replace(marker, '\n' + section + marker.lstrip('\n'), 1)
medical.write_text(text)
