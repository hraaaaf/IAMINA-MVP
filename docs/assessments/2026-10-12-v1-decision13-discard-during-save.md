# V1 #13 — Never abandon while a real glucose save is in progress

**Before/Goal in [issue #973](https://github.com/hraaaaf/IAMINA-MVP/issues/973).** AddLogSheet already has PopScope and explicit discard confirmation for unfinished glucose/context/meal drafts, and blocks exit during voice capture. Its _confirmLeave did not check the asynchronous _saving flag, so returning to Home could be presented as an abort while a write is still pending. This is a code-level race possibility, not an observed patient incident.

**Patch**: _confirmLeave returns false immediately while _saving is true, ahead of the other checks. The UI already displays a saving state; no new warning/modal, no new visual treatment, no file/DB/clinical or navigation change to ordinary canceled drafts. Android/system and UI back both call this function. Source-contract tests protect the order of checks and existing confirmation/continue-editing behavior.

**Limit**: these static tests are not a timing simulation of a slow Drift write; before release, run an asynchronous widget/route test with a controlled delayed storage operation and verify save completion/cancel behavior. No clinical recommendation, real patient data, CGM, provider or deployment. DRAFT and no merge without owner approval.
