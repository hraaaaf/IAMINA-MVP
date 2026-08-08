from pathlib import Path

p = Path('docs/ROADMAP.md')
s = p.read_text()
s = s.replace(
    '> **Last updated:** 2026-08-07 — P0-UX-10 Importer / document flow certified at 9.4/10 after rejecting a first visual pass; P0-UX-11 first-use Dashboard is next.',
    '> **Last updated:** 2026-08-08 — P0-UX-11 first-use Dashboard certified at 9.3/10 after rejecting the baseline and a first post-patch small-screen pass; P1-UX-12 progressive Profile is next.',
    1,
)
s = s.replace(
    '| P0 visual UX remediation | 56% | 🟡 Active — P0-UX-11 next | P0-UX-6 through P0-UX-10 certified; PRs #53–#61; latest Importer/document recertification run `31224557639` |',
    '| P0 visual UX remediation | 67% | 🟡 Active — P1-UX-12 next | P0-UX-6 through P0-UX-11 certified; PRs #53–#62; latest first-use Dashboard recertification run `31248641421` |',
    1,
)
s = s.replace(
    '| P0-UX-11 | Dashboard premier utilisateur | 0% | Next LOT — certify truthful first-use hierarchy and action priority | ⏭️ |\n| P1-UX-12 | Profil progressif | 0% | Queued | ⬜ |',
    '| P0-UX-11 | Dashboard premier utilisateur | 100% | **9.3/10** after second post-patch visual double-check; PR #62; truthful loading/error/empty/offline states; 8-view FR/AR recertification run `31248641421`, artifact `9019314222`, zero page errors | ✅ |\n| P1-UX-12 | Profil progressif | 0% | Next LOT — progressive disclosure and hierarchy | ⏭️ |',
    1,
)
marker = '\nThis UX remediation workstream is separate from the MENA critical-path numerator.\n'
section = '''
### P0-UX-11 delivered work

- The existing first-use Dashboard was audited before modification across FR/AR at `1440×1000`, `768×1024`, `390×844` and `360×560`. The baseline scored **8.4/10** and was rejected: desktop was under-composed, the empty state could appear while local streams were still loading, and feature pills such as real-time AGP / AI analysis could imply capabilities before any patient data existed.
- Local data states are now explicit and truthful: loading and local-read error are distinct from an actually empty Dashboard, with a localized retry action for errors; offline state remains derived from the real `SyncService` state.
- The empty state presents no fabricated KPI, graph or sample patient value. The primary action is the real **add first measurement** route and document import remains a real secondary action.
- Ambiguous feature-promise pills and the emoji illustration were removed. A clinical Material icon and factual FR/AR/EN copy explain that the Dashboard is built only from real recorded data.
- Wide layouts use a two-zone first-use composition instead of a narrow mobile block stretched across desktop; mobile and RTL use a single directional column with 48 px actions.
- The first post-patch visual pass was also rejected because the French truth-note card was partially obscured by the bottom navigation at `360×560`. The same LOT was corrected so short-height screens prioritize the factual body and both acquisition actions without hiding content.
- The final matrix covers the Dashboard in FR/AR at `1440×1000`, `768×1024`, `390×844` and `360×560`: **8/8 rendered views, zero page errors**, stable RTL and fully visible primary/secondary actions. Baseline local API connection-refused console noise remains unchanged and is not presented as a new runtime regression.
- Certified product head `2b65e9c4357b59bbc2d53cdde2e6a3271e65911c` passed CI #1128 and migration drift #944. Visual evidence: run `31248641421`, artifact `9019314222`, digest `sha256:b1846c10a68a918ad0ea5484fe50726da3ae69710944b072bf88e947eb45dd03`.

**Final P0-UX-11 score: 9.3/10 — PASS.** The LOT exceeded the mandatory threshold only after the baseline and the first post-patch small-screen result were both rejected and remediated. PR #62 is the merge unit; P1-UX-12 is next.
'''
assert marker in s
s = s.replace(marker, '\n' + section + marker, 1)
p.write_text(s)
