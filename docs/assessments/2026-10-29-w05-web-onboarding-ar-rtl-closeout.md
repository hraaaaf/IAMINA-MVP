# IAMINA — W05 onboarding Web : auto-défilement et AR/RTL (closeout ciblé)

**Date : 29/10/2026. Statut : code et audit AR/RTL fusionnés ; FUE globale D7 NON CERTIFIÉE.**

## Goal → critère observable → preuve

- **Goal UX :** après une action explicite en onboarding Web compact, révéler la question suivante sans demander un scroll manuel. Ne pas sauter automatiquement lors d'un choix parmi plusieurs traitements ; ne pas déplacer l'accueil desktop.
- **Succès UX observé :** FR + AR/RTL sur 390×844, 768×1024, 1280×900, pays explicitement choisi, type 2, deux traitements déclarés, accès aux unités et CTA ; Chrome sans exception ; desktop CTA complètement accessible après un scroll manuel.
- **Preuve :** PR produit [#1166](https://github.com/hraaaaf/IAMINA-MVP/pull/1166) et PR de certification [#1168](https://github.com/hraaaaf/IAMINA-MVP/pull/1168), GitHub Actions et captures ci-dessous. Tests réalisés uniquement avec données synthétiques.

## Code produit fusionné

- PR [#1166](https://github.com/hraaaaf/IAMINA-MVP/pull/1166), merge squash `07477defc3ad7f99fc5186b13008627865e88156` : reprise ciblée de `GlobalKey` + `Scrollable.ensureVisible` trouvée en PR non fusionnée [#1128](https://github.com/hraaaaf/IAMINA-MVP/pull/1128).
- Défilement sur actions explicites : langue → pays → type → traitements ; après la sélection multiple, bouton « Continuer vers les unités » en Web compact. AR : « المتابعة إلى الوحدات ».
- Desktop `>=900` : aucun défilement automatique ni bouton de défilement redondant. La dernière action reste inline et accessible manuellement.
- La sémantique des réponses, le pays non déduit de la langue, les unités médicales, les seuils, le backend, la DB et les contraintes de consentement restent inchangés.
- Avant fusion : 7/7 workflows GitHub SUCCESS sur l'exact HEAD produit `2422e4d8808da555caae769a730df55e9ee9c153`, notamment [CI #40794382504](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40794382504), [Chrome #40794382531](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40794382531), [artifact 12863341945](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40794382531/artifacts/12863341945).
- Après fusion #1166 : [CI push #40796117144](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40796117144), [UI screenshots #40796117216](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40796117216), [routes #40796117043](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40796117043) — 3/3 SUCCESS.
- [Preview Vercel](https://iamina-review-amkw4i4jp-achraf-benmoussa-s-projects.vercel.app/) `dpl_6ZJq5nxcauhHbx4HVcwTPKSG7Bc9` READY sur le HEAD **pré-merge** ; retour manuel propriétaire iPhone : « Working ». Cela n'est pas une preuve de l'ensemble de la FUE ; aucun nouveau déploiement n'a été autorisé pour le merge.

## Audit AR/RTL fusionné

- PR [#1168](https://github.com/hraaaaf/IAMINA-MVP/pull/1168), merge squash `cd5acc1327ff6c4d295a3c23c573bed715bf7b9b`, uniquement quatre fichiers de tests, fixture navigateur et workflow. Aucun changement dans `frontend/lib/features/auth/onboarding_chat_screen.dart` (blob identique `a4cd7897de4f21e2f23fadfa65969aaddef51d54`).
- Exact HEAD de la PR de test `45650a8130aa35622741d343eca072124453e4d3` : **6/6 workflows SUCCESS**, incluant [CI #40798782159](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40798782159) et [Chrome FR+AR #40798781860](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40798781860).
- [Artifact AR/RTL 12865311873](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40798781860/artifacts/12865311873) : Chrome réel, 390×844 / 768×1024 / 1280×900, `locale=ar`, pays utilisateur MA, type 2, deux traitements, unités, `pageErrors=0` ; captures avant/après. En desktop 1280×900, CTA rect après scroll explicite `(x=456.2, y=793, w=240, h=36)` : entièrement dans le viewport.
- Le premier audit Chrome avait échoué car le banc Playwright bloquait le Service Worker PWA ; `flutter_bootstrap.js` tentait ensuite `registration.update()` sur un enregistrement absent. Correction **du test uniquement** avec `serviceWorkers: 'allow'`, sans retirer la capture d'exceptions. Le dernier échec transversal UI Chrome 1280×900 provenait d'un délai de démarrage DevTools ; le job seul a été relancé (nouvel ID `123330552900`) et s'est achevé **SUCCESS** sans modification source.
- Après la fusion #1168 : [CI push #40839999595](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40839999595) **SUCCESS** sur le commit exact `cd5acc1327ff6c4d295a3c23c573bed715bf7b9b`, avec Flutter analyse, tests et build PWA. [UI browser screenshot push #40839999609](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40839999609) demeure **IN_PROGRESS** au dernier relevé ; sa conclusion ne doit pas être déduite des preuves prémerge.

## Limites et reprise exacte

- **Certifié sur données synthétiques :** progression et rendu AR/RTL Web, contrôles Flutter et Chrome aux trois viewports ; pas de débordement majeur constaté dans les captures inspectées.
- **Non certifié par ce lot :** la FUE complète D7 (vrais parcours de comptes A→logout→B→A, offline/reload, confidentialité et isolation du coffre, contrôles cliniques D22/#1165, tests utilisateur Safari arabe natif). Ne pas annoncer le chantier global terminé ou prêt production.
- **Next exact :** vérifier les deux runs post-merge de `cd5acc13` ; si erreur, diagnostiquer et corriger ; si verts, clore le présent lot Web UX et reprendre le lot Web prioritaire selon `docs/ROADMAP.md` sans Vercel Preview/Production additionnelle sans GO.

## Références

- Roadmap Web : [`docs/ROADMAP.md`](../ROADMAP.md), W05.
- Canonique décisions : [Notion IAMINA — D1–D30](https://app.notion.com/p/40777c6633628177b325d3cb5412fc18).
- Projet : `hraaaaf/IAMINA-MVP` / `main`. Aucune estimation globale d'avancement chiffrée n'est attribuée sans dénominateur observé.