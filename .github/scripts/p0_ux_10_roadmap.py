from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)

p = Path('docs/ROADMAP.md')
s = p.read_text()
s = replace_once(
    s,
    '> **Last updated:** 2026-08-07 — P0-UX-9 small-screen 360×560 certified at 9.2/10 after a second visual remediation pass; P0-UX-10 Importer / Pulper is next.',
    '> **Last updated:** 2026-08-07 — P0-UX-10 Importer / document flow certified at 9.4/10 after rejecting a first visual pass; P0-UX-11 first-use Dashboard is next.',
    'last updated',
)
s = replace_once(
    s,
    '| P0 visual UX remediation | 44% | 🟡 Active — P0-UX-10 next | P0-UX-6 through P0-UX-9 certified; PRs #53–#60; latest 360×560 recertification run `31208830202` |',
    '| P0 visual UX remediation | 56% | 🟡 Active — P0-UX-11 next | P0-UX-6 through P0-UX-10 certified; PRs #53–#61; latest Importer/document recertification run `31224557639` |',
    'progress dashboard',
)
s = replace_once(
    s,
    '| P0-UX-10 | Importer / Pulper | 0% | Next LOT — consolidate the import entry point and remove ambiguity between Importer and Pulper | ⏭️ |\n| P0-UX-11 | Dashboard premier utilisateur | 0% | Queued | ⬜ |',
    '| P0-UX-10 | Importer / document | 100% | **9.4/10** after second visual double-check; PR #61; one primary Importer entry; 16-view FR/AR recertification run `31224557639`, artifact `9011673527`, zero page errors | ✅ |\n| P0-UX-11 | Dashboard premier utilisateur | 0% | Next LOT — certify truthful first-use hierarchy and action priority | ⏭️ |',
    'lot table',
)
anchor = "**Final P0-UX-9 score: 9.2/10 — PASS.** The score was assigned only after the rejected 8.6/10 pass was corrected and recaptured. No critical/high small-screen defect remains in the certified FR/AR `360×560` scope. PR #60 is the merge unit for this LOT; P0-UX-10 is next.\n\n"
section = """### P0-UX-10 delivered work

- Code inspection established that Importer and the historical Pulper screen are not competing acquisition products: `/importer` is the sole primary acquisition hub, while `/pulper` is a subordinate document workflow that performs pick → ingest → preview → explicit confirmation.
- The technical `/pulper` route and internal `PulperPreview` / `PulperConfirmResult` model names remain implementation details; no backend, persistence or confirmation semantics were changed.
- User-facing `Pulper IAmina` branding was removed. The Importer hub now presents the localized task **Importer un document**, and the document screen uses the same task-first title without duplicating it in the hero.
- UI implementation names were aligned to the product model (`DocumentImportCard`, `DocumentFormatChip`, `DocumentImportIcon`) while preserving the historical internal route to avoid an unnecessary navigation migration.
- A permanent `p0_ux_10_importer_document_entry_contract_test.dart` proves that Importer is the only primary navigation entry, the document workflow remains subordinate and no user-facing Pulper branding returns.
- The first 16-view visual pass was explicitly rejected: the French `360×560` document screen partially clipped the primary **Choisir un document** CTA at the bottom.
- The same LOT was corrected with a short-height layout contract (`≤600 px`) that reduces only vertical spacing, icon size and CTA padding while preserving the complete privacy notice and all document-format choices.
- The second matrix covers Importer plus document import in FR/AR at `1440×1000`, `768×1024`, `390×844` and `360×560`: **16/16 rendered views, zero page errors**, no visible Pulper branding, clean RTL and a fully visible primary CTA at the harshest viewport.
- Certified product head `14e7a6d605aeb31d6c1813c614f9b72bbbf71d53`; visual evidence: run `31224557639`, artifact `9011673527`, digest `sha256:8e064f44d31f5422d8662cb8f88a962d74fcc8a676a6139cf5906110f2893710`.

**Final P0-UX-10 score: 9.4/10 — PASS.** The LOT was not closed on the first successful implementation: the clipped 360×560 French CTA forced a second remediation and complete recertification. PR #61 is the merge unit; P0-UX-11 is next.

"""
s = replace_once(s, anchor, anchor + section, 'delivered section')
p.write_text(s)
