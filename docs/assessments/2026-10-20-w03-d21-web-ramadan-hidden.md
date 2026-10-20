# IAMINA Web — W03 / D21 : masquer Ramadan dans le Profil

Date : 2026-10-20. Périmètre : **Flutter Web uniquement**. Décision source : D21, `docs/ROADMAP.md` (W03), `docs/assessments/2026-10-15-w00-web-inventory.md` et le registre Notion des 29 décisions.

**Statut : CANDIDAT — non déployé / non certifié visuellement.** W01 reste NO-GO, W02 gelé. Ce quick win est indépendant de W01/W02 selon la roadmap et ne touche ni la sécurité Production ni les notifications D2 (PR #1135).

## Goal → Succès → Preuve

- **Goal exact** : masquer la section saisonnière Ramadan du Profil **dans le Web** sans supprimer ses modèles, migrations, traitements historiques ou la version native ; aucune action Web pour saisir/enregistrer des dates Ramadan ne doit rester accessible via le Profil.
- **Succès observable** : dans un vrai navigateur Web, Profil montre `Informations médicales → IAmina → Données → Compte`, sans carte Ramadan ni boutons de dates/enregistrement. Les autres sections, la langue et la navigation sont inchangées.
- **Preuve requise** : Flutter analyze/tests+build ; captures BEFORE/AFTER strictement mêmes états/viewports Chromium **390×844, 768×1024, 1280×900**, FR/AR RTL, clavier et focus ; revue indépendante. Pas de score visuel >7,5/10 sans Target↔Render réel.

## BEFORE → cible/mise en page → AFTER candidat

**BEFORE code vérifié sur `main` :** `frontend/lib/features/profile/profile_screen_presentation.dart` construit `_buildMedicalSection`, puis `_buildRamadanSection` (avec dates de début/fin et `ramadan-save-period`), puis `_buildProfileSection` IAmina. La section Ramadan est visible par défaut si le profil est consultable. Aucun screenshot contrôlé du même état Web n'a encore été capturé : ne pas inventer une preuve visuelle.

**Cible/mockup écrit :** conserver la mise en page existante, le rythme vertical de 14 px, tous les intitulés/états des cartes. Dans le Profil Web, les cartes `Médical` et `IAmina` deviennent adjacentes ; les cartes Données et Compte restent identiques. Ne pas créer de remplacement décoratif ni supprimer des données.

**AFTER code candidat :**
- `profile_screen.dart` : `kWebRamadanUiEnabled=bool.fromEnvironment('IAMINA_WEB_RAMADAN_UI',defaultValue:false)`, plus `shouldShowRamadanProfileSection(isWeb:...)`.
- `profile_screen_presentation.dart` : `_buildRamadanSection` et son espacement sont ensemble derrière cette garde avec `kIsWeb`; Web par défaut OFF, code natif/conservation historique inchangés.
- `frontend/test/features/profile/w03_d21_ramadan_visibility_test.dart` : garde Web OFF, native non affectée, section et commandes restent compilables et regroupées, build Vercel n'active pas le flag.
- **Aucun backend, API, migration, calcul clinique, donnée patient, plugin, avis médical ou variable Vercel modifié.** Le code historique Ramadan existe toujours ; ce sous-lot ne prouve pas à lui seul qu'aucun autre module ne lit d'anciens champs Ramadan.

## Exclusions et décision de livraison

D2 notifications demeure sur PR #1135 distincte. D3 rappels sur PR #1085 DRAFT ancienne et CI rouge ; pas de réécriture concurrente du dashboard. W01 durcissement Production, restauration Neon et matrices de certification sont volontairement réservés aux décisions finales suivant instruction propriétaire. **Aucun Vercel deployment sans autorisation expresse** ; **aucun merge** avant CI, visuels et revue exigés.

**Next exact** : créer PR DRAFT dédiée depuis `main`, obtenir le verdict CI SHA exact ; ensuite capture Web synthétique avant/après et comparaison FR/AR aux trois tailles. Si les captures ne sont pas disponibles, classer D21 candidat partiel, pas VERIFIED et continuer aux autres décisions W03/W11 sans prétendre fermer D21.
