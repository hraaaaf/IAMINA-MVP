# IAMINA WEB — L0 : intégration candidat des barrières réseau Companion + CGM — 22 octobre 2026

## Goal → succès → preuve
**Goal exact :** réconcilier [CGM #1096](https://github.com/hraaaaf/IAMINA-MVP/pull/1096) et [Companion #1133](https://github.com/hraaaaf/IAMINA-MVP/pull/1133) sur `main@8ada5aab8e8006bbbdc275eabbabf014a4714e0b` pour le pilote **Web local-only**, sans transmettre d'informations médicales au serveur par leurs clients HTTP indépendants.

**Succès observable nécessaire :** (1) en build Flutter Web RELEASE, toutes les méthodes CGM refusent AVANT lecture de token et AVANT HTTP ; (2) Companion overview/proactive/next-action ne fait aucun HTTP ; chat/voix patient refusent AVANT bearer/network ; chat démo non authentifié reste strictement local et déterministe ; (3) aucune porte de contournement par callback synthetic en mode RELEASE ; (4) UX indique avec vérité FR/EN/AR la fonction indisponible, sans promesse de sécurité clinique non démontrée ; (5) aucune régression auth/CSRF/consent/profil; (6) FUE navigateur + traces réseau réelles + scores/avis qualifiés.

**Preuves héritées (PAS preuve d'intégration) :** #1096 **3/3 CI SUCCESS** au SHA `c73588cc`; #1133 **8/8 CI SUCCESS** au SHA `45685254`. Les PRs initiales restent OPEN/DRAFT, non fusionnées ; leurs tests ne certifient pas le comportement combiné.

## Audit source avant intégration
- Sources des PRs examinées, différences local-only connues, 10 chemins contrôlés contre les deux bases git indépendantes et le HEAD actuel de main. Tous les blobs main des chemins modifiés étaient **strictement identiques** aux ancêtres respectifs. Les 10 blobs retenus sont copiés bit pour bit des PRs sources, sans réécriture de protections.
- CGM `CgmService._headers` applique `kReleaseMode || callbackSynthetic != true` → refus 403 avant `AuthService.getIdToken`. Aucune autorisation distante pour l'application release.
- Companion `_clinicalTransportAllowed = !kReleaseMode && callbackSynthetic==true` : refus par défaut ; méthode de chat patient renvoie `clinical_transport_disabled_local_only`, message UX FR/EN/AR spécifique.
- Précaution : cette intégration **désactive** l'accès serveur CGM et Companion chat/voix ; ce n'est **pas** un remplacement local qualifié ni une fonction clinique terminée. Vérifier le parcours urgence et les affordances avant toute livraison.

## Tests / décisions requises
| Gate | Attendu | État initial |
| --- | --- | --- |
| SHA main et compatibilité des 10 fichiers | base exacte, pas de changements masqués | **PASS source** (Git trees) |
| Flutter tests CGM + Companion | zéro HTTP, zéro bearer et refus synthétiques appropriés | **À EXÉCUTER sur L0** |
| Release Web runtime HTTP no-egress | trace réseau Chrome, aucun payload patient, 390/768/1280 | **À EXÉCUTER sur L0** |
| UX BEFORE→AFTER FR/AR | messages vrais, bouton chat/voix et erreur, focus/touch, toutes tailles | **À EXÉCUTER sur L0** |
| Clinique urgence / option locale | aucun faux assistant médical, écran sécurité adéquat | **BLOQUANT : issue #1134** |
| Privacy/sécurité/clinique indépendantes | revue humaine de l'impact et du refus egress | **BLOQUANT** |
| Vercel / Production / merge | autorisation explicite distincte après tous gates | **NON AUTORISÉ** |

**Perfection Pass et scores** : différés jusqu'aux résultats sur SHA exact. Tant que la sécurité du chemin clinique urgence est ouverte, status `BLOCKED` (cap score 5.9/10), **pas de GO produit/Production**.

**Dépendances** : [W01 #1128](https://github.com/hraaaaf/IAMINA-MVP/pull/1128) NO-GO ; W02 gelé ; D21 Preview distincte. Aucun changement de Neon/API, aucune donnée patient, aucun déploiement Vercel voulu pour la construction de cette branche.

**Next exact :** créer PR DRAFT d'intégration, vérifier CI exact SHA et preuve Chrome sans réseau, corriger régressions, comparer UX, documenter reviewers/gates cliniques ; puis poursuivre L0 autres PRs sécurité en branch indépendante. Ne pas fusionner si impact clinique/UX non résolu.
