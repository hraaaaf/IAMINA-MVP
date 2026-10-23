### 23/10/2026 — additional cross-lot mismatch, found before rerun

The same old Dashboard browser tool `tools/dashboard_capture.js` awaited an HTTP 2xx from `/api/v1/companion/overview`. On the combined Web RELEASE build, [Companion #1140] prohibits this network request: `CompanionService.fetchOverview` returns `null` without HTTP when `kReleaseMode`. The old browser oracle would **time out even with a healthy Flutter dashboard**.

Patch candidate also replaces the impossible HTTP wait with an explicit Flutter Web mounting check (`flutter-view` or `flt-glass-pane`), then inspects the screenshots as before (9 distinct captures, no blank/JS errors, 5xx). It adds an **assertion that zero `/api/v1/companion/*` HTTP requests were issued** in the local-only build. This strengthens the no-egress requirement rather than weakening it. It does not bypass authentication, seed a backend patient, or change production code. **No CI PASS claimed until new shared-HEAD run.**

## 23/10/2026 — Cross-lot CI fail found: Dashboard visual must respect D11

**BEFORE**: on combined HEAD `9d557ff9` [Dashboard responsive visual #39968326382](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39968326382) FAILED at step « Create and seed synthetic certification identity » because it uses `curl -f POST /api/v1/demo/seed` and gets **HTTP 403**, exactly the fail-closed behavior introduced in D11. Backend, migrations and account registration succeeded beforehand. **This is a harness contradiction between two already-green isolated PRs, not evidence to roll back D11**.

**Corrective candidate (harness-only)**: retain synthetic registration in ephemeral PostgreSQL CI but replace the disallowed seed call with an **assertion that authenticated /demo/seed returns exactly 403**. The frontend audit entrypoint seeds its own ephemeral unscoped browser-only database via `AppDatabase.defaults().seedDemoData()`; it does not seed a real patient vault. Dashboard screenshots retain their responsive contract; backend overview now has an *empty synthetic account*, and this empty-state must be genuinely tested. Do **not** reintroduce HTTP demo seeding, loosen D11 or fabricate patient data.

**Goal/tests**: Dashboard responsive workflow SUCCESS on integration SHA, 9 screenshots pixel-distinct and no JS errors, API overview HTTP okay on empty account, D11 negative 403 test PASS, other 15 workflows PASS. If dashboard visualization requires remote fixture data, redesign audit harness strictly inside synthetic browser context; no production endpoint workaround. **Current patch only prepared; CI not yet run.**

---

# IAMINA WEB — L0 INTEGRATION COMPLETE (CANDIDAT PRÉMERGE) — 23 octobre 2026

## Objectif / succès / preuve

**Objectif :** vérifier ensemble, à partir de `main@8ada5aab8e8006bbbdc275eabbabf014a4714e0b`, les trois candidats L0 **déjà codés** mais non intégrés : [PR #1140](https://github.com/hraaaaf/IAMINA-MVP/pull/1140) (CGM + Companion local-only Web), [PR #1141](https://github.com/hraaaaf/IAMINA-MVP/pull/1141) (glycémie finie et sauvegarde protégée), [PR #1142](https://github.com/hraaaaf/IAMINA-MVP/pull/1142) (zéro démo dans comptes réels).

**Succès observables requis** : tous workflows CI au HEAD exact PASS ; test runtime non-sortie de données cliniques, navigation/urgence honnêtes, écritures Drift résistantes aux retours, auth A→B→A et tests négatifs de seed de données, UI BEFORE/AFTER 390/768/1280 FR/AR, reprise PWA et relecture sécurité/clinique/privacy indépendantes ; pas de Production ni de compte patient réel.

## Preuves de non-collision et provenance

- Git compare entre `main@8ada5aab8e8006bbbdc275eabbabf014a4714e0b` et chaque source : **18 chemins dans #1140, 6 dans #1141, 12 dans #1142**, **36 fichiers sources distincts, zéro chemin en conflit**.
- Chaque blob ajouté/modifié est repris par son **SHA Git d'origine**, sans réécriture des trois protections. Les docs de chaque lot sont maintenues.
- CI des sources : #1140 **9/9 SUCCESS** au SHA `3249c5ca`; #1141 **8/8 SUCCESS** au SHA `337a7e73`; #1142 **6/6 SUCCESS** au SHA `450c0f93`. Ce ne sont **pas** des preuves de réussite du build commun avant sa propre CI.

## Gates de sécurité et de livraison

- **Clinical/Privacy human gate** : [issue #1134](https://github.com/hraaaaf/IAMINA-MVP/issues/1134), traduction et prise en charge urgence, comportement local-only, validation CGM et impossibilité de promettre chat/voix serveur. Aucun triage clinique local certifié.
- **W01** [PR #1128](https://github.com/hraaaaf/IAMINA-MVP/pull/1128) est encore Draft/NO-GO : branche Neon runtime réelle, Redis, CSRF, A→B→A hosted et DR non certifiés. **W02 gelé**.
- **L0 glycémie** : une CI verte sur contrat statique n'est pas une preuve du vrai timing Drift sous abandon/race ; test événementiel reste un gate.
- **L0 D11** : bloquer les seeds dans PostgreSQL y compris DEBUG ne prouve pas que tout SQLite est synthétique. Aucun patient réel testé.
- **Pas de merge ni de Vercel Preview/Production autorisé pour cette nouvelle branche.** Le déploiement auto de `main` doit être évalué avant tout merge.

## Résultats du lot commun

**ÉTAT INITIAL :** branche d'intégration candidate, **CI À EXÉCUTER**, aucune certification globale. Scores visuels/indépendants à établir à partir d'artefacts réels. Gate humain = revue clinique/privacy/security, plus autorisation Vercel distincte si un merge déclenche un déploiement.

**Next exact :** CI du HEAD commun → diagnostiquer/corriger → FUE visuel et tests comportements sur même SHA → closeout documentaire → évaluation indépendante → décision de livraison avant merge ; W01 reste priorité pour un vrai usage patient.