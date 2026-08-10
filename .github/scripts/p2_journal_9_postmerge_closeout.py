from pathlib import Path
import sys

root = Path(sys.argv[1])
path = root / 'docs/ROADMAP.md'
text = path.read_text()
replacements = {
    '> **Last updated:** 2026-08-10 — P2-JOURNAL-9 Post-save experience is certified pre-merge in PR #77; Journal metabolic-event redesign is at its final merge unit.':
        '> **Last updated:** 2026-08-10 — P2-JOURNAL-9 Post-save experience is merged and 100% closed; the Journal metabolic-event redesign is fully closed. The active critical path returns to MENA launch blockers.',
    '| Journal metabolic-event redesign | 100% pre-merge | 🟢 P2-JOURNAL-9 certified; merge/post-merge pending | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6/7 + P2-JOURNAL-8 merged; PR #77 factual post-save receipt; exact-code CI #1387 + drift #1199 green; 16-view FR/AR UX 9.3/10; four specialist reviewer PASSes |':
        '| Journal metabolic-event redesign | 100% | ✅ Closed | P0-JOURNAL-1/2 + P1-JOURNAL-3/4/5/6/7 + P2-JOURNAL-8/9 merged; PR #77 merged as `d841d926d1b7fe076827a3086306daa09399e38d`; UX 9.3/10; post-merge CI #1390 + drift #1202 green |',
    '# Journal metabolic-event redesign — ACTIVE':
        '# Journal metabolic-event redesign — CLOSED',
    '| P2-JOURNAL-9 | Post-save experience | 🟢 PR #77 merge unit | persistent factual local receipt after successful save; no instant interpretation/advice; mobile next actions remain reachable; longitudinal insights stay separate behind J8 evidence requirements; UX 9.3/10 |':
        '| P2-JOURNAL-9 | Post-save experience | ✅ Closed | PR #77 merged as `d841d926d1b7fe076827a3086306daa09399e38d`; persistent factual local receipt; no instant interpretation/advice; mobile actions remain reachable; post-merge CI #1390 + drift #1202 green; UX 9.3/10 |',
}
for old, new in replacements.items():
    if text.count(old) != 1:
        raise SystemExit(f'final ROADMAP anchor mismatch: {old[:100]}')
    text = text.replace(old, new, 1)

old = "Canonical documentation changes make these anchors pre-closeout evidence, so exact-final-head recertification, Release Certifier, expected-head merge and post-merge gates remain mandatory before Journal is declared 100% closed."
new = "Canonical documentation changed the pre-merge head to `cc529c378eea7cb4908a57fdad2e85db5bde75bd`; exact-final-head CI #1389, drift #1201 and visual audit #4 all passed, the four specialist reviewers re-anchored FINAL PASS, and Release Certifier authorized the expected-head merge. PR #77 merged as `d841d926d1b7fe076827a3086306daa09399e38d`; post-merge CI #1390 and migration drift #1202 passed. **P2-JOURNAL-9 and the complete Journal metabolic-event redesign are 100% closed.**"
if text.count(old) != 1:
    raise SystemExit('final J9 evidence anchor mismatch')
text = text.replace(old, new, 1)
path.write_text(text)
