# IAMINA B — D15 Web : brouillon repas multimodal unique — préflight du 03/11/2026

**Décision et Goal** : saisie manuelle catalogue, description texte ou dictée, portions explicitement choisies et suggestions photo confirmées convergent vers un seul brouillon local ; pas de sauvegarde sans action utilisateur, pas de calcul de dose et pas d'ingestion automatique de candidats photo.

**Ordre canonique** : chantier B D14 puis D15 ; D15 dépend de D13 et D14. Le 03/11/2026, D14 est volontairement **PAUSED** pour D24 et autorisations externes, activation photo patient NO-GO ; D13 non prouvée clôturée (ancienne PR #1215 fermée sans merge au contrôle). D15 peut être testée par sous-lot isolé, mais **ne peut pas être close ni mise en service**.

**Origine et situation BEFORE** : [issue #977](https://github.com/hraaaaf/IAMINA-MVP/issues/977) et [PR historique #978](https://github.com/hraaaaf/IAMINA-MVP/pull/978). Celle-ci se limite à 4 tests de propositions photo simulées et un insert Drift manuel ; base vieillie, mergeable=false ; elle ne prouve pas le bouton Save réel. Baseline actuelle : `main@c2fc32bbd31a24fe17542e6abda96d937905737b`. Aucune modification de runtime/UX dans ce sous-lot.

**Lot D15.1 — contrat réel local sans fournisseur** :
- Conserver les 4 tests synthétiques historiques : photo candidate proposée, confirmation explicite requise, fallback incertain sans écriture, absence d'ID catalogue inconnu et unicité de l'insert simulé. Aucune photo ni reconnaissance fournisseur réelle.
- Ajouter **5 parcours Flutter widget** sur le véritable `AddLogSheet` : français et arabe × 390×844 et 1440×1000, sélection manuelle d'un aliment réel, grammes saisis par l'utilisateur, note bilingue, puis bouton `save-log-button` réel. Avant Save : 0 ligne ; après : exactement 1 `LogEntry` Drift avec ID, note, portion et glycémie cohérents. Contrôler insulinUnits null. Cinquième parcours : abandon du repas efface choix/grammes/note avant Save, sans perte de la mesure.
- Réutiliser les tests de dictée existants dans `add_log_sheet_test.dart` : voix simulée aboutit à la même note, sans écriture anticipée ; ne pas relancer de vrai transfert audio.
- La UI reste celle de main : aucun changement de pixels, aucune note de qualité visuelle inventée. Le test widget n'est **pas** une vraie recette Safari ni un Chrome navigateur hébergé.

**Critère de succès** : les 9 tests spécifiques D15 + les tests existants doivent réussir sous Flutter 3.41 sur HEAD exact en CI, sans fichier runtime touché ; PR DRAFT et sans Vercel/merge. Aucun PASS anticipé.

**Dépendances non levées / gates** : D13 conservation du brouillon en navigation/sauvegarde, D14 image avec consentement média et suppression des réponses tardives, D24 consentement/egress au serveur ; provenance clinique des portions et incertitude, revues privacy, audio et mineurs. Quand ces prérequis seront établis, réaliser un vrai FUE Web par le bouton Save dans Chrome/Safari avec les deux modes, visual BEFORE→AFTER si modification UI, revue clinique et release humaine.

**Next exact** : vérifier CI exacte du sous-lot, corriger tout test rouge sur la branche D15 sans toucher D14/D18/D24 ; si vert mettre la preuve dans Notion et GitHub puis attendre les dépendances pour la clôture.
## Reprise vérifiée — 04/11/2026
- PR Draft #1257 OPEN, D15 HEAD `916a2a683aa6e4b48fd3613054dd6e7464838fa1`. CI #41749225511 : Frontend analyze/tests/PWA SUCCESS (job #126309917604), Backend SQLite et PostgreSQL FAILURE **avant** la résolution des échéances de gouvernance. P5-5 rehearsal #41749225623 SUCCESS.
- Correctif Backend indépendant PR #1259 MERGED sur main `8bcc6a16710a16d202a7b3f5c48d1c0ac4cc9288`; son CI #41803012808 Backend SQLite/PostgreSQL SUCCESS. Ce résultat **ne certifie pas** la CI de D15 : PR #1257 doit intégrer la nouvelle base et exécuter ses propres jobs.
- Comparaison GitHub actuelle : D15 diverged, ahead 6 / behind 1. Fichiers D15 et Backend modifiés distincts ; absence de conflit de chemins ne garantit pas automatiquement un merge propre. `mergeable=false` signalé par GitHub au contrôle.
- La photo est encore une proposition simulée suivie d'un insert Drift manuel : **pas de preuve** photo confirmée → vrai `AddLogSheet` Save. D15.1 = preuve partielle ciblée, pas D15 globale.
- Next exact : synchroniser prudemment PR #1257 avec main sans perdre les tests D15 ; relancer CI Flutter + Backend ; ensuite combler le test photo confirmée → Save réel si compatible avec D14 PAUSED et sans activer de transfert média. Ne pas merger ni déployer D15 tant que D13/D14/D24 et validation humaine ne sont pas levés.

## Validation CI après photo→Save — 04/11/2026
- HEAD testé : `00450da80a0b04c3b1e4160ab52f2ab252a2ea06` ; CI `#41809869976` COMPLETED SUCCESS, jobs Frontend analyze/tests/PWA, Backend ruff+pytest et PostgreSQL SUCCESS ; rehearsal synthétique `#41809869791` SUCCESS.
- Sept autres workflows de certification UI associés au même HEAD : SUCCESS ; ce résultat ne constitue pas une recette manuelle Chrome/Safari du parcours D15.
- Nouveau test `add_log_sheet_test.dart` : candidat photo synthétique, confirmation explicite, zéro écriture avant Save, saisie utilisateur des grammes/note, véritable `save-log-button`, une ligne Drift et insuline null. Callback de reconnaissance injectable uniquement pour les tests ; consentement photo requis via profil, aucune reconnaissance réelle ni transfert patient activé.
- **Verdict D15.1 : preuve automatisée verte sur HEAD cité.** Ne pas confondre avec D15 globale : D13/D14/D24 et revue humaine toujours gates, D14 PAUSED. PR #1257 reste DRAFT, pas de merge ni déploiement.
