# V1 #3 — Rappels locaux sur l'Accueil, analyse et référence UI

**Goal/BEFORE et référence établis avant code :** [issue #950](https://github.com/hraaaaf/IAMINA-MVP/issues/950). Captures réelles [Chrome BEFORE #38252290934, artifact #11749017316](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290934/artifacts/11749017316) pour 390×844, 768×1024 et 1280×900 : section gouvernée « À retenir aujourd'hui », aucune carte Rappels. Ne pas supprimer le Clinical Twin pour reproduire littéralement un ancien libellé « Your next step ».

**Design cible** : carte compacte AminaVisualLanguage sous la section gouvernée, titre `Rappels/Reminders/التذكيرات`, état réel du compte des rappels locaux actifs (`AppDatabase.watchReminders`), ouverture `/reminders`, icon `event_note_outlined`, CTA implicitement accessible, RTL directionnel. Pas de titre médical sensible dans le Dashboard, pas de faux rappel, pas d'OS push, pas de réseau ou nouvelle donnée patient.

**Implémentation candidate (DRAFT, non certifiée au dépôt)** : `dashboard_reminders_summary_card.dart`, liaison au Dashboard Premium, testWidgets FR/EN/AR sur SQLite Drift en mémoire (vide, ajout, opt-out d'un rappel, réactivation, pas de titre sensible, navigation). Pas de modification moteur clinique, DB/migrations, prévisions, LLM ou permissions.

**Validation à faire sur HEAD exact** : CI Flutter analyse/tests/PWA, preuve réelle responsive AFTER 3 viewports (9 images), comparaison BEFORE→AFTER, tests de navigation, pas de débordements/erreurs navigateur; score visuel exclusivement après preuve. #2 [PR #949](https://github.com/hraaaaf/IAMINA-MVP/pull/949) reste DRAFT/non mergée et ne fait pas partie de ce patch #3. Pas de merge/deploy sans permission.
