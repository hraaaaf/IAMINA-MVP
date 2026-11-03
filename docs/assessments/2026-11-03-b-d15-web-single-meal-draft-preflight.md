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