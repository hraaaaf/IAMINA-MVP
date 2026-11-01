# V1 #13 — Never abandon while a real glucose save is in progress

**Before/Goal in [issue #973](https://github.com/hraaaaf/IAMINA-MVP/issues/973).** AddLogSheet already has PopScope and explicit discard confirmation for unfinished glucose/context/meal drafts, and blocks exit during voice capture. Its _confirmLeave did not check the asynchronous _saving flag, so returning to Home could be presented as an abort while a write is still pending. This is a code-level race possibility, not an observed patient incident.

**Patch**: _confirmLeave returns false immediately while _saving is true, ahead of the other checks. The UI already displays a saving state; no new warning/modal, no new visual treatment, no file/DB/clinical or navigation change to ordinary canceled drafts. Android/system and UI back both call this function. Source-contract tests protect the order of checks and existing confirmation/continue-editing behavior.

**Limit**: these static tests are not a timing simulation of a slow Drift write; before release, run an asynchronous widget/route test with a controlled delayed storage operation and verify save completion/cancel behavior. No clinical recommendation, real patient data, CGM, provider or deployment. DRAFT and no merge without owner approval.


## 01/11/2026 — reprise bornée sur main actuel

- Ancienne PR #974 sur une branche divergeante (350 commits behind main) : non utilisée comme base de fusion.
- Correctif repris exclusivement dans la version courante de `AddLogSheet`, plus les deux tests source-contract existants ; aucune modification de valeur glycemique, seuil, cible, schéma ou unité.
- Vérification exacte de la CI et FUE Web réelle avec une écriture Drift ralentie : **NOT_RUN au moment de cette reprise** ; revue de confidentialité et navigation sur Web en attente.
- Il est interdit de qualifier D13 de CLOSED sur la seule preuve statique. Aucun déploiement Vercel ni merge autorisé par ce sous-lot.
