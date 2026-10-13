# ADR-0009 — D30 privacy-first onboarding and optional pseudonymous recovery (PROPOSED)

**Date:** 2026-10-13  
**Status:** PROPOSED — architecture, security, legal and UX gates OPEN; **NOT ACCEPTED, NOT IMPLEMENTED**  
**Product authority:** IAMINA decision #30, approved as product direction only on 2026-10-13. [Notion decision register](https://app.notion.com/p/3f377c663362812dbe78cead75e71922).  
**Implementation lanes:** V1-04 first-use/profile, V1-03 privacy/egress, V1-11 certification. This **does not create V1-12 or change the original 29-decision dependency order**.  
**Do not confuse:** product decision D30 is unrelated to historical GitHub issue #30 (Gate A history remediation).

## Goal / observable success / proof

**Goal:** a real IAMINA patient can start and retain a device-local clinical record without supplying name, email, phone number or a remote account. A user may later choose pseudonymous, authenticated remote synchronization and recover their *own* encrypted record without exposing another patient's record.

**Success (all mandatory before any release claim):**
1. Fresh local-only enrollment and first *real* synthetic test entry work offline, without a remote bearer/account, demo fixture, mandatory identity field, or patient payload egress.
2. Local reopen and app-lock work across offline/restart cases. Unauthenticated requests to backend-gated patient endpoints always fail closed; local app-lock is **not** remote Django authentication.
3. Sync is opt-in, patient-scoped, versioned, revocable, and never marks data synced before an authenticated server ACK. A↔B switches, stale epochs, replay, conflicts, offline retries, user deletion and a clean second device never leak, overwrite or silently lose records.
4. Encrypted backup/recovery succeeds with a tested separately-held recovery factor and fails safely without it. Erasing Web/PWA storage or losing all keys has an honest, test-verified unrecoverable mode. Never claim a biometric unlock or syncable passkey alone decrypts the vault.
5. Data flows, security/privacy audit, real PWA/browser evidence, authorized clinician/privacy/CNDP gates, and exact-head tests are documented and green **before** patient-real-data activation.

**Current proof status:** these are **acceptance criteria, not proven implementation results**. No D30 code, UI, API, cryptographic protocol, consent or legal approval is certified by this ADR.

## Evidence-based boundaries from main (2026-10-13, a6284c4)

- `docs/ROADMAP.md` records local-first first enrollment and reopen, remote enrollment OFF by default, remote and device-local session separation, and WebAuthn local app-lock merged through #649. These existing boundaries must not regress. Their historical certification does not prove this new end-to-end D30 journey.
- `docs/architecture/ARCHITECTURE.md` describes Django-native registration/login, signed bearer tokens and legacy Firebase migration; **remote password-based auth and device-local WebAuthn app-lock are not already a passkey-only pseudonymous account system**.
- D7 treatment profile remains on DRAFT PR [#986](https://github.com/hraaaaf/IAMINA-MVP/pull/986). Local-vault binding, logout, auth epoch, recovery on a new device and multi-device sync are active unresolved integration concerns. D30 must not race a second identity implementation onto D7's open branch.
- Local Drift state, remote Django record, and consent state have different ownership. The installation ID must **never** become proof of remote identity or a secret substitute.
- Current product is pre-pilot, `NOT_RELEASE_AUTHORIZED`; P5 historical 6/12=50% is independent of D30 progress.

## Decision boundaries: fixed requirement versus candidate design

### Fixed product requirement (approved D30)

- **Default local-only**: no required name/email/phone, no remote account or automatic upload of clinical records; no demo-data contamination.
- **Optional remote**: technical random identity, auth on the Django side and user-controlled consent for every additional purpose; no fabricated bearer. Prefer standard WebAuthn passkeys subject to genuine platform compatibility tests and dedicated authenticated registration/recovery routes.
- **Privacy by construction**: backend and external AI/media/CGM processors receive only explicitly authorized minimal data. Pseudonymized data and encrypted health data still require privacy/legal review.
- **Never weaken** clinical deterministic safety, patient isolation, CSRF for cookie writes, global AI opt-out or the existing app-lock.

### Candidate architecture, NOT implementation authorization

1. **Local root:** random per-installation identifier and a device-local patient vault. Enumerate actual storage/crypto implementation; do **not** state the vault is encrypted until encryption, key custody and PWA backing storage are demonstrated on supported devices.
2. **Remote account:** opt-in, server-issued pseudonymous principal with registered WebAuthn credential(s), verified registration origin/rpId/challenges/user presence/verification, strict Django patient-scoped bearer/session authority, replay protection, rate limits, auditable revocation and account lifecycle. Existing Django email/password bootstrap must not be silently repurposed to claim passkey support. If prerequisites are missing, remote sync stays OFF.
3. **Separation of keys:** remote authentication credential ≠ encryption/decryption key ≠ local app-lock credential. A server that verifies a passkey assertion cannot infer possession of the local encryption key. `WebAuthn PRF` is a **possible**, support-dependent client-side wrapping input, not a generic guarantee across devices or authenticators; must prevent accidental server exposure of PRF outputs.
4. **Optional encrypted backup:** design a versioned cryptographic envelope with random data encryption keys, authenticated encryption, unique nonces, domain-separated key wrapping, anti-replay/integrity checks, metadata minimization, protected client-only keys, rotation/revocation and backward-compatible recovery. Select exact primitives/library/storage only after security review. Neither `zero-knowledge` nor `E2EE` is a current product fact.
5. **Preferred independent recovery factor (candidate):** generate a high-entropy user-held recovery secret / recovery kit locally, display once and require confirmed storage; use an established audited KDF/wrapping protocol to recover the vault DEK on a fresh device without transmitting plaintext secret or DEK. No server-held plaintext backdoor. Optional second passkey can supplement availability **only if actual decryption-key portability is demonstrated**.
6. **Consent and sync:** initial sync OFF. Explicit notice, purpose scope, enable/disable, server-side authorizations, epoch checks, CAS/ETags/revisions, outbox + ACK, idempotent replay, safe conflicts, local-first functioning under network outage, revocation and export/erasure. No last-write-wins for clinical records. Remote health content may be plaintext only if separately justified/approved; the proposed encrypted-sync design must prove cryptographic properties before being described as such.
7. **Local-to-remote binding:** never claim remote account owner from old installation IDs or email collisions. New account linkage must be consciously initiated and server authenticated; keep any pre-existing independent patient vault isolated unless explicit, reviewed, non-destructive migration is proven.
8. **Deletion semantics:** distinguish device-only purge, unlink device, remote-account erasure, delete backup copies/retention, and revoke access. Explain that a lost local secret can make decryption impossible even if encrypted server bytes remain. Tombstones, replicas and processor logs need separate review.

## Threat model (initial; security review required)

| Threat / failure | Must fail safe or prove | Blocking evidence |
| --- | --- | --- |
| Erased browser/PWA storage; device loss | No false recovery promise; restore only with available validated factor, otherwise explicit irreversible-loss UX | Fresh profile, cleared site data, uninstall/reinstall, recovery yes/no |
| Stolen/unlocked device or compromised browser | Local app-lock and keys isolated to their real threat boundaries; no claim of protection against full runtime compromise | Browser/device threat review, XSS/CSP, key-at-rest and OS keystore inventory |
| Unauthorized backend / guessed ID / forged bearer | All remote PHI endpoints authenticate and authorize scoped patient; no local-ID login shortcut | 401/403, forged/expired/revoked bearer, A vs B on SQLite+PostgreSQL |
| Lost/replaced passkey; unsupported PRF | Remote login alone cannot recover encrypted backup; explicit fallback/recovery kit | Separate recovery factor, PRF support matrix, new device |
| Offline edits and concurrent changes | No silent overwrite, replay or false “synced” badge | outbox generation, CAS 409, ACK check, retry, conflict UI, two devices |
| Logout, identity switch A→B→A | No cross-patient access, cache bleed, stale async callback or orphaned vault adoption | Epoch tests, scoped vault, app-lock, consent reset and UI cache |
| Telemetry / IP / support / CGM / AI provider | Pseudonymization ≠ anonymity, remote metadata and raw media may identify patients | Actual egress network capture, logs redaction, processor inventory |
| Malicious recovery request / brute force | Recovery secret never accepted as low-entropy account password; rate-limit remote entrypoints; avoid key oracle | Abuse/rate-limit, cryptographic misuse/fault tests |
| Compromised remote DB / backups | Confidentiality depends on properly reviewed client-held keys; minimize metadata and validate ciphertext | Key custody, threat simulation, ciphertext inspection, backup retention |
| Erasure / account deletion | Precise semantics, no undeclared orphan server copy or accidental deletion of other patient's data | Deletion cascade, revocation, retention audit |

**Non-goals in this ADR:** deploying an auth provider, replacing Django auth, implementing new cryptographic primitives, turning on remote account creation, adopting D7 implementation, changing clinical recommendations, or making patient-facing visual changes. Only spec/roadmap/acceptance plan is in scope.

## Data-flow matrix to verify (candidate, not audited)

| Mode / action | Data leaving device | Identity required | User-controlled gate | Status |
| --- | --- | --- | --- | --- |
| First local enrollment and real local log | **Target: no patient payload**; transport/host request metadata must be separately observed | No nominative or remote account | local privacy notice / app-lock policy | Network capture PENDING |
| App reopen offline | **Target: no required auth traffic** | local continuity + device lock | local only | D30 regression test PENDING |
| Enable optional remote principal | technical credential assertions/challenge + minimum service metadata; **no clinical record by registration** | Django-bound remote pseudonymous principal | explicit opt-in | Route and origin audit PENDING |
| Sync/backup | candidate opaque versioned encrypted payload plus unavoidable minimal metadata | verified remote patient | separate sync consent, revocable | E2EE/transport/log tests PENDING |
| Recovery on new device | public account discovery/verified auth, downloaded ciphertext, client-held recovery factor | remote auth + independent decrypt capability | explicit initiation | Fresh-device test PENDING |
| CGM or external AI/media | governed, purpose-specific data; no implicit full dossier | service-specific scoped identity, if required | consent, processor/legal gates | V1-03 and CGM reviews PENDING |
| Export/delete/logout | local export only unless explicit transfer; remote erasure requires verified principal | depends on operation | explicit destructive action | erase/revoke/audit PENDING |

**Important:** “no mandatory name/email/phone” does **not** mean “anonymous” or “zero data collected.” The host's IP, HTTP logs, passkey credential IDs and encrypted-backup account metadata may remain regulated personal data.

## Recovery UX contract (target, no UI modification in D30-0)

- User chooses **Continue on this device** (default) or **Enable encrypted sync** later. Neither path may prefill fake clinical records.
- Explain the loss risk before a local-only user relies on permanent storage, especially on Web/PWA, without making signup mandatory.
- Before remote encrypted backup, generate and **verify** an independent recovery mechanism. Never show “backup protected” without a tested round trip and server ACK.
- Provide two independent error states: **not authenticated to remote account** and **authenticated but cannot decrypt existing backup**. Neither silently creates or takes over a new patient vault.
- On browser data wipe: allow a clearly chosen **restore** if factor present, otherwise a separate empty local profile only after warning about non-recoverability. Do not auto-link to prior patient.
- For future UX: BEFORE → written Goal → mockup reviewed → AFTER identical viewports 390×844, 768×1024, 1280×900, a11y and FR/AR/RTL; no D30 UI change is authorized by this documents-only lot.

## Implementation order and explicit gates

**D30-0 — THIS PR: design/inventory only.** Proposed ADR, threat/data matrix, source pointers, roadmap traceability; no runtime/UX or certification claim. Acceptance: PR diff only docs, links and mandatory negative test plan. **Builder complete when pushed; reviewer/security/architecture acceptance pending.**

**D30-1 — baseline inventory + permanent fail-closed regressions:** inspect actual `AuthService`, local vault, WebAuthn lock, Django bearer routes, storage/browser behavior, sync/consent paths. Add test fixtures for *local offline first log with zero patient egress*, unauthenticated remote denial, A/B local separation and browser wipe. Work from clean main with D7 changes reconciled, not guessed. No backend passkey route yet.

**D30-2 — recovery protocol design + independent crypto review (human gate):** specify cipher/KDF/envelope/metadata/rotation, browser support, threat model and key custody. Independently review **before** creating real recovery endpoints. Reject unsupported claims; choose an explicit alternative or keep backup off if no safe implementation.

**D30-3 — optional remote identity / sync vertical slice:** authenticated Django WebAuthn remote principal (not existing local app-lock); signed user opt-in; server isolation; encrypted backup, scoped outbox/ACK/CAS and lifecycle. Include 401/403 and concurrency tests on SQLite+Postgres and device-to-device PWA evidence. Coordinate D7/9/10 to avoid competing identity/vault migrations.

**D30-4 — UX/recovery/certification:** real BEFORE/AFTER identical viewports, informed consent and loss warnings, negative UX scenarios, independent specialist reviews, legal/CNDP and exact-HEAD CI/post-merge. No real-patient release until V1-11 + P5-6A/B and separate explicit authorization.

## Regulatory and standards check (engineering baseline, NOT legal approval)

- W3C Web Authentication Level 3, WebAuthn PRF support and credential behavior: https://www.w3.org/TR/2026/REC-webauthn-3-20260825/ . Registration/assertion or a passkey sync claim is **not** evidence of recoverable content keys.
- OWASP [Cryptographic Storage](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html) and [Key Management](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html): threat model, key isolation, backup, generation/rotation and the irreversible consequences of losing encryption keys.
- CNDP [conditions](https://www.cndp.ma/conditions/), [health-sensitive processing](https://www.cndp.ma/notifier-un-traitement/) and [foreign transfers](https://www.cndp.ma/transfert-de-donnees-a-letranger/). Law 09-08 status and any Article 22 exception require qualified legal interpretation for IAMINA's *actual* operator and processing context. A pseudonym never waives data-health obligations.
- Repo legal baseline: `docs/architecture/PILOT_CONSENT_PROCESSOR_GOVERNANCE.md`, plus P5-6A/P5-6B, must be rechecked against the **actual patient runtime**, not development Vercel infrastructure.

## Acceptance/proof register — all OPEN

- [ ] D30-0 doc review: architecture owner + security auditor assess design risks and contradictions; exact-HEAD diff/CI.
- [ ] D30-1 first real local entry + offline/no-network proof (browser and mobile where applicable).
- [ ] No patient data/demo contamination, unsigned bearer or unreviewed egress.
- [ ] A→logout→B→A, backend A/B isolation, old epoch and concurrent writes.
- [ ] Optional remote passkey origin/rpId/challenge/auth/revocation/consent.
- [ ] E2EE keys and metadata independently audited, including recovery-factor portability; **no "zero knowledge" marketing in meantime**.
- [ ] New-device restore with factor, denial/loss without factor, lost passkey, PWA storage wiped, XSS/browser failure.
- [ ] Export/delete/tombstone/backup purge, accessibility and FR/AR.
- [ ] Exact-head SQLite+Postgres+Flutter/Web/PWA, real viewport BEFORE/AFTER for future UI work.
- [ ] Independent clinical/privacy/security reviewers, human architecture/UX decisions, legal/CNDP and V1-11 pilot gates.

## Closeout state (2026-10-13)

D30-0 is a **documented proposal**, not an accepted ADR and not a functioning onboarding implementation. V1 architectural implementation %, D30 test pass count, and date of any future authorization are **unknown**. No merge or Vercel deploy is authorized by this document.
