# IAMINA — Décision D22 Web : dossier de clôture et gates humains (NON APPROUVÉ)

**Date de référence :** 03/11/2026. **Portée :** D22 uniquement ; Web/PWA, non clinique. **Statut cible actuel :** `OPEN / G1–G7 PENDING / PATIENT GATE B NO-GO`. Ce document est un **dossier de décision**, pas un accord médical, un merge, une certification produit ou une autorisation Vercel.

## Decision — D22 : unités et objectifs glycémiques

**Goal :** conserver la valeur brute et sa provenance, distinguer unité de source / stockage / affichage, et n’afficher de classification ou métrique liée à une cible que lorsque patient, unité, source et autorité sont effectivement vérifiés.

**Succès observable de la préparation :** chaque condition de clôture a un propriétaire, une décision explicite, une preuve identifiable (SHA GitHub + test + comportement observé), une dépendance et un statut. Aucun champ de signature n’est prévalidé.

**Preuve de cette préparation :** analyse des sources GitHub, fiche canonique `docs/assessments/2026-10-29-d19-d22-web-clinical-decision-gate.md`, contrat `2026-11-02-d22-g1-g4-g7-evidence-contract-gate.md`, répétition `2026-11-02-d22-g7-synthetic-migration-rehearsal.md`, PR et workflows cités ci-dessous.

## 1. Congeler les lots verts, sans les recommencer

| FUE / PR | Preuve disponible au 03/11/2026 | Limite exacte |
|---|---|---|
| F01/F03/F07 browser scoped [#1231](https://github.com/hraaaaf/IAMINA-MVP/pull/1231) `36aab03329ad969fd441bb9cbcab542204368233` | **20/20 workflows SUCCESS** ; Chrome EN/FR/AR 390/768/1280, persistance préférence, cibles inconnues non éditables et clavier FR/AR ; preuves de reflow CSS | Pas de cible clinique autorisée, pas de zoom NATIF Chrome 200 %, pas de revue linguistique native |
| F04 [#1238](https://github.com/hraaaaf/IAMINA-MVP/pull/1238) `a69e91eee10e925d3e83046f2e8a8834ffb6cd6f` | **7/7 SUCCESS** ; Flutter/SQLite + Chromium/IndexedDB : modification du contexte, brut synthétique 103.25 inchangé à 390 et 1280 ; 4 captures SHA | Pas d’identité distante/remote sync, aucun facteur clinique ou arrondi signé |
| F06 [#1241](https://github.com/hraaaaf/IAMINA-MVP/pull/1241) `b04ea588f3b1ac68c3f0f8ed591c92248a4e7068` | **2/2 SUCCESS** ; Chrome réel, contrôleur de vault local, faux principaux A/B, retour A après logout, valeurs synthétiques A=103.25 / B=222.5 sans contamination | Les FakePrincipal ne certifient PAS AuthService, Django, SSO, API distante ni consentement clinique |
| F07 texte 200 % [#1242](https://github.com/hraaaaf/IAMINA-MVP/pull/1242) `aa7c64abced94fce18b0729f44e0bfb8cd5d0f88` | **20/20 SUCCESS** ; six tests Flutter `TextScaler.linear(2.0)` FR/AR × 390/768/1280 ; invariants descriptifs et RTL | `TextScaler` n’est PAS le zoom natif Chrome, pas de test lecteur d’écran / audit arabe indépendant |
| F05 rapport [#1240](https://github.com/hraaaaf/IAMINA-MVP/pull/1240) `a3c75f116d25ba3c75457b4007ae74a5d796d41c` | [Chrome #41659326395](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41659326395) **SUCCESS** ; artifact #13241271798 : `PASS_BOUNDED_REAL_CHROME`, 4/4 scénarios FR/AR × 390/1280, 4 PNG SHA corrects, 22 demandes de polices **refusées** ; cibles legacy non classantes | **19/19 workflows SUCCESS** au HEAD exact, [CI générale #41659326542](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41659326542) SUCCESS ; vrais PDF/CSV, capteur CGM et API KPI toujours non certifiés |
| Gate A source [#1225](https://github.com/hraaaaf/IAMINA-MVP/pull/1225) `8e7a081a252848f10b785c2b2729b189c217a659` | 18/18 workflows antérieurement verts ; suppression des cibles historiques non vérifiées dans les surfaces prioritaires | PR Draft/non fusionnée ; ne constitue pas approbation clinique ni migration |

**Règle d’ingénierie :** les PR vertes restent **DRAFT / figées**. Les tests nouvellement ajoutés dans d’autres PR peuvent partager des parents non mergés (notamment #1240 sur #1225 et #1242 sur #1231) ; documenter les dépendances avant toute fusion. **Ne pas recommencer une suite verte simplement pour sa couleur.** Tout changement ultérieur crée obligatoirement une nouvelle preuve sur le nouveau SHA.

## 2. Décisions humaines G1–G7 — dossier prêt à signer, aucune signature présumée

| Gate | Proposition technique à arbitrer (pas validée) | Autorité et preuve indispensables | État |
|---|---|---|---|
| **G1 — autorité d’unité** | Préférer valeur source + unité UCUM explicites, valeur canonique distincte, préférence d’affichage jamais traitée comme provenance ; refuser unité inconnue | Responsable données/DB + privacy, revue clinique des usages ; schéma/payload et exemples invalides | **PENDING** |
| **G2 — autorité de la cible patient** | Aucun `70/180` ou défaut legacy classant ; nouvelle cible seulement avec patient, clinicien/source, timestamp et confirmation, statut révoquable | Clinicien/endocrinologue + responsable produit ; contrat patient→target→consumers, consentement | **PENDING** |
| **G3 — traitement des historiques** | Conserver les valeurs brutes `unknownLegacy`, aucune déduction d’unité/cible, aucun backfill silencieux | Clinicien + privacy + migration/DB ; inventaire, non-adoption, rollback sur jeu synthétique | **PENDING** |
| **G4 — facteur, arrondi, édition** | Décider **une** convention et sa version ; conflit observé 18.0 écran, 18.018 helper main, 18.016 D19 #920. Préserver la valeur source lorsqu’on ne change pas la mesure | Responsable calcul D19 + clinicien ; protocole d’arrondi, perte/reversibilité, frontière API, tests d’extrêmes | **PENDING** |
| **G5 — classifications/CGM/export** | Aucun « dans la cible » sans G2/G1 ; aucun ratio de relevés manuels présenté comme **temps CGM** ; métriques CGM exigent capteur, fenêtre, continuité, provenance et contrat approuvé | Clinicien/endocrinologue + API/analytics + privacy ; producteurs→consommateurs rapports/PDF/CSV/AGP/TIR | **PENDING** |
| **G6 — parcours FR/AR/RTL** | Unité avant objectif, titres sans unité mensongère, fail-closed lisible et accessible, zoom natif 200 % | Clinicien pour copy, relecteur arabe natif et responsable accessibilité produit ; captures *même état/mêmes viewports*, clavier, lecteur d’écran | **PENDING** |
| **G7 — migration, propriété, consentement** | Migration additive/versionnée seulement après sauvegarde+restauration prouvées, identité propriétaire cryptographiquement liée, non-propagation legacy ; aucune migration réelle actuelle | Sécurité/privacy/DB + produit ; plan 12→13, tests browser IndexedDB et remote API/auth, rollback, audit des données | **PENDING** |

**Choix à proposer :** G1 représentation avec source + UCUM explicitement versionnée, G3 préserver legacy inconnu sans inférer, G5 pas de CGM/TIR sans source. **Ce sont des recommandations non approuvées.** Aucune ligne d’autorité ne peut être complétée à partir de tests verts.

### Fiche de signature à remplir par un humain autorisé — pour chaque Gx

- Gate et décision A/B/« modifications demandées » :
- Identité, rôle/qualification et organisation du signataire :
- SHA GitHub exact et version du contrat/fixtures examinés :
- Date/heure de signature, fondement/document/risques acceptés :
- Tests supplémentaires exigés, critères d’arrêt/rollback :
- Verdict : `APPROUVÉ / MODIFICATIONS DEMANDÉES / REFUSÉ` — **actuellement PENDING**.

## 3. Tests restant réellement nécessaires — séquencés pour ne pas traiter un rouge déjà vert

| ID | Test/objectif précis | Exécutable sans approbation ? | Verdict actuel |
|---|---|---|---|
| **F02** | Une **cible validée** avec vraie provenance, conversion mg/dL↔mmol/L↔mg/dL avec facteur/arrondi signés ; reload/offline et aucune mutation des bruts | **NON** avant G1+G2+G4 ; préparation synthétique/fail-closed seule permise | **NOT_RUN** |
| **F05-A** | Rapport sans cible autorisée, FR/AR responsive et aucun TIR imaginaire | **OUI — réalisé** : Chrome #41659326395 | **PASS_BOUNDED** |
| **F05-B** | Vérifier les vrais exports PDF et CSV et le consumer API KPI, notamment `ApiClient.getKpis` dont paramètres source par défaut 70/180 exigent contrat G5 | Scénarios négatifs de sécurité : oui ; classification/export clinique positif : **NON** avant G1/G2/G5 | **NOT_RUN** |
| **F05-C** | CGM AGP/TIR/GMI à partir de données capteur tracées et continues, jamais dérivées d’une lecture manuelle | **NON** sans source et critères approuvés G5 ; audit statique permis | **NOT_RUN** |
| **F06-B** | Compte réel A→logout→B avec authentification, token expiré/invalidé, consentement, API + DB locale/offline et sync après reconnexion | Jeu synthétique et préprod protégée après revue G7 de l’identité/consentement ; jamais de comptes de patients | **NOT_RUN** |
| **F07-B** | Vrai zoom **natif Chrome** à 200 %, FR/AR RTL 390/768/1280, Tab/Shift+Tab, focus/scroll, lecteur d’écran, relecture arabe native, BEFORE/AFTER au même état | QA synthétique possible, revue linguistique humaine indispensable ; ne pas confondre viewport CSS ou `TextScaler` avec zoom natif | **NOT_RUN** |
| **G7 Migration** | Drift 12→13 additive, sauvegarde chiffrée/restauration et idempotence sur vrais formats Web/IndexedDB, API compatibility, no foreign vault | **NON** en runtime patient avant revue signée ; modèle SQLite isolé déjà passé 11/11 en #1222 | **NOT_RUN** pour application réelle |

### Source-to-sink à ne pas omettre

- `frontend/lib/services/api_client.dart` expose `targetLow=70.0` et `targetHigh=180.0` en paramètres par défaut du KPI : **un nombre technique n’est pas une autorité clinique**. Vérifier tous les producteurs avant d’autoriser un consumer.
- `frontend/lib/features/dashboard/clinical_engine.dart` contient un calcul de ratio de relevés manuels ; ne pas l’appeler « CGM time-in-range ».
- `frontend/lib/features/journal/reports_screen_presentation.dart` bloque la classification en l’absence de cible approuvée. **Ce comportement local fail-closed n’atteste pas l’export distant ou une consultation médicale.**
- Le modèle de contrat [#1221](https://github.com/hraaaaf/IAMINA-MVP/pull/1221) et la répétition SQLite [#1222](https://github.com/hraaaaf/IAMINA-MVP/pull/1222) ont été fusionnés **sans câblage clinique runtime** ; consulter leurs SHAs et la CI au moment de leur réutilisation. La répétition 11/11 ne démontre pas une migration Drift réelle.

## 4. Critères de clôture D22 — non négociables

- [ ] G1–G7 : sept décisions signées, responsables qualifiés + date + SHA relu + justification, absence de contradiction entre sources.
- [ ] F02 cible approuvée et G4 calculs/arrondis validés en Web réel ; valeurs legacy inconnues toujours intactes.
- [ ] F05 PDF/CSV/API/CGM avec bornes vérifiées ou statut `indisponible` si la preuve manque, sans producer non autorisé.
- [ ] F06 auth+consentement réel sur comptes synthétiques, isolation A/B offline/remote et invalidation de session.
- [ ] F07 zoom natif et revue FR/AR/RTL clavier/lecteur d’écran ; BEFORE→AFTER cohérent, score visuel et corrections.
- [ ] G7 migration réelle, backup/restauration vérifiés hors production, rollback documenté et tests de réinstallation/idempotence.
- [ ] Revue indépendante clinique + données/sécurité + UX **sur les SHAs définitifs**, exceptions écrites et décisions explicites.
- [ ] Réconcilier dépendances PR #1225/#1231/#1238/#1240/#1241/#1242, CI exactes, merge **seulement autorisé**, post-merge tests, closeout des .md pertinents et roadmap.
- [ ] Vercel **uniquement** après approbation explicite distincte ; aucun GO patient implicite par CI, maquette ou preview.

## 5. Prochaine action exacte et séquence conditionnelle

**Next exact sans human gate :** conserver cet evidence pack en PR **DOCS ONLY**, déjà reliée à issue [#1165](https://github.com/hraaaaf/IAMINA-MVP/issues/1165) et Notion D22 ; F05 désormais **19/19 SUCCESS** au HEAD exact, ne plus relancer ses tests verts. Préparer l’arbitrage G1/G2/G4/G5/G7 (formule, ownership, CGM et exports) pour signatures sans activer de code clinique.

**Si signatures obtenues :** implémenter séparément les contrats source/objectif et migration additive sous tests, F02 positif et F05/06/07 de bout en bout → revue indépendante → CI de chaque PR au SHA final → autorisation distincte de fusion → post-merge → closeout canonique → human gate Vercel. **Si une signature manque :** D22 reste `OPEN / GATE B NO-GO`.

**Fichier source antérieur à respecter :** `docs/assessments/2026-10-29-d19-d22-web-clinical-decision-gate.md`. Ce dossier actualise l’état des preuves au 03/11 ; il ne réécrit pas rétrospectivement les statuts historiques de cette fiche.
