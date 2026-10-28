# W02 — Web BFF read-only integration candidate (2026-10-28)

Goal: enable same-origin W02 Web Preview BFF and fail-closed remote synthetic registration.

- W01 hosted Web→BFF→API SQL identity read-only returned database `iamina925_empty`, role `iamina_preview_app`, Neon project `noisy-truth-00115950`, branch `br-sweet-frog-b9ok6ptp`.
- This W02 code candidate reuses W01 Vercel OIDC BFF, moves Flutter Preview requests to browser origin, retains `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=false` and additionally blocks POST auth/register unless Preview-only IAMINA_W02_REMOTE_E2E_ENABLED=true AND attested SQL identity matches.
- Protected Backend Preview URL is still controlled by the Git-branch-scoped Vercel environment. Current W02 Preview points to an older backend deployment lacking SQL identity route: E2E cannot start yet.
- No deployment, database write, or production change authorized. Static local code verification only; do not claim hosted W02 E2E.
- Remaining: target a backend deployment with live identity attestation, explicitly authorize Preview deploy and synthetic exercise, verify genuine browser→BFF→API flow, A/B/A with cleanup and independently verify auth_user=0; at-rest clinical encryption and key-recovery security gate independent.
