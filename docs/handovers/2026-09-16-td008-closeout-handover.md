## 15 octobre 2026 — POST-MERGE GREEN : incident de runner TD-008 clos

- **Échec précédent exact** : [#38654612593](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38654612593) FAILED au boot Android/ADB `Broken pipe (32)`, sans exécution du scénario pilote. Cause runner/infrastructure identifiée, non certifiée comme régression clinique.
- **Réparation workflow seule** : [PR #1010](https://github.com/hraaaaf/IAMINA-MVP/pull/1010) MERGED `7cdda5a3284306d0dd15ae54f05c0420583413a9` (KVM/config Android 15). Premerge [Android #38656735672](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38656735672) SUCCESS et CI #38656735687 SUCCESS sur SHA `1875a6a9`.
- **Preuve postmerge** : [TD-008 Android #38657927043](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38657927043) **COMPLETED SUCCESS** et [CI #38657927045](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38657927045) SUCCESS, tous deux sur `7cdda5a3`. Les tests synthétiques du scénario Android ont réellement tourné ; cela ne remplace pas D31 sur deux vrais téléphones.
- **Documentation closeout** : [PR #1014](https://github.com/hraaaaf/IAMINA-MVP/pull/1014) MERGED `a38285ab72d2cebbcc0f9738096adfc459547932`, et [CI du nouveau main #38658178252](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38658178252) **SUCCESS**. Aucun code patient, aucune DB de production ni Vercel modifiés par ces PR.
- **NEXT** : sous-lot technique runner TD-008 clôturable, D31 physique [#1006](https://github.com/hraaaaf/IAMINA-MVP/issues/1006) indépendante et ouverte ; D10-B sécurité [#1013](https://github.com/hraaaaf/IAMINA-MVP/issues/1013) ouverte. P5 historique 50 % inchangé.

---

## 15 octobre 2026 — Régression runner postmerge D7/D9 puis reprise vérifiée

- **Incident de CI distinct du lot TD-008 historiquement clos :** [postmerge D7/D9 run #38654612593](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38654612593) FAILED, émulateur Android 15 ~467 secondes au boot puis `adb Broken pipe (32)`, **sans résultat de test Flutter produit**. Cela ne remet pas à lui seul en cause les preuves TD-008 antérieures.
- **Correction bornée** : [PR #1010](https://github.com/hraaaaf/IAMINA-MVP/pull/1010), seul fichier workflow `.github/workflows/td008-device-integration.yml` modifié (KVM, Pixel 5, Google APIs, 1536 Mo, options sans snapshot). Reprend la configuration de la CI double émulateur D7/D9 déjà vérifiée. Aucun runtime ou donnée clinique modifiés.
- **Preuves prémerge exact SHA `1875a6a9af8f695800997e6499c6d31d45c8387a` :** [run Android #38656735672](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38656735672) **COMPLETED SUCCESS**, étape d'intégration Android confirmée SUCCESS ; CI #38656735687 SUCCESS.
- **Merge** [PR #1010](https://github.com/hraaaaf/IAMINA-MVP/pull/1010) au commit `7cdda5a3284306d0dd15ae54f05c0420583413a9`, main relue à ce SHA avant merge suivant D10 test-only. Postmerge [TD-008 #38657927043](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38657927043) **initialement IN_PROGRESS** et CI #38657927045 **SUCCESS** ; prochain contrôle de conclusion indispensable.
- **Next exact :** si run postmerge vert, noter certification runner sur SHA ; si rouge, examiner étape et différencier panne infrastructure/régression réelle avant tout closeout. Cette correction n'atteste pas des 2 téléphones physiques D31 [#1006](https://github.com/hraaaaf/IAMINA-MVP/issues/1006).

---

# HANDOVER — IAMINA / TD-008 closed → TD-012 next

Date: 2026-09-16

## Closed lot

TD-008 — Device-level critical-flow coverage is incomplete.

## Verified closeout

- PR #636 squash-merged to `main` at `532376020d4696d4098994a97a764a1994c7f92f`.
- Exact PR merge validation included current `main` through GitHub's merge ref `bfc301b609e82e40961200c83d4ae6752cc5a36a`.
- TD-008 device integration run #8 passed on the current merge ref.
- Post-merge TD-008 run #9 (`35074054081`) passed on `main`.
- Android pilot-critical journeys passed 3/3:
  - real app shell auth safe-failure;
  - glucose logging with local in-memory persistence;
  - Companion typed provider-timeout safe UX.
- Issue #635 closed as completed.
- PR #641 removed TD-008 from `docs/TECHDEBT.md`.
- Documentation closeout merged to `main` at `8d54168674c316ddcc64846384b0bcac72650fe4`.
- `docs/ROADMAP.md` remains 6/12 = 50.0%; TD-008 was technical debt, not one of the 12 atomic roadmap lots.

## Guardrails retained

- No Vercel deployment was performed.
- No production DB mutation was performed.
- No real-patient data was used.
- Existing widget/accessibility/browser/PWA/mobile packaging checks remained green during exact-head validation.

## Next lot

TD-012 — Large Flutter surfaces and silent catches reduce maintainability.

Tracker: #637.

### Goal

Reduce the highest-risk broad/silent Flutter error handling on pilot-critical paths without changing user-visible behavior, then narrow or remove TD-012 only to the extent proved.

### Priority order

1. Inventory broad/silent catches on pilot-critical frontend paths.
2. Classify by risk: swallowed failure, unsafe fallback, unobservable failure, or cosmetic-only path.
3. Replace the smallest high-value set with typed and/or explicitly logged handling.
4. Add targeted regression tests before cosmetic decomposition.
5. Preserve current UI/UX and clinical behavior unless a separately proven defect requires change.

### Success proof

- targeted tests green;
- existing CI/non-regression checks green;
- no production DB or patient-data mutation;
- `docs/TECHDEBT.md` updated only after verified residual compromise is known;
- merge requires explicit owner approval.

## First actions in next window

1. Read this handover from `main`.
2. Verify current `main` SHA, issue #637 state, and current CI before editing.
3. Read current TD-012 wording in `docs/TECHDEBT.md`.
4. Audit pilot-critical Flutter catches and select the smallest highest-risk slice.
5. Create a dedicated implementation branch only after the audit.

## Canonical references

- `docs/ROADMAP.md`
- `docs/TECHDEBT.md`
- issue #637
