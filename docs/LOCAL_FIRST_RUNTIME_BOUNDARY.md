# IAMINA Local-First Runtime Boundary

Status: canonical architecture boundary for runtime placement. Release authorization remains governed by `docs/ROADMAP.md`.

## Goal

Keep IAMINA clinically usable without requiring Vercel, Neon, Firebase, SMTP or another remote processor to be reachable, including first device enrollment.

## Runtime authority

### Patient runtime

The patient-facing runtime is local-first:

- clinical persistence is device-local;
- deterministic clinical and safety logic required for local workflows runs locally;
- first device enrollment and subsequent reopen do not require network connectivity;
- local clinical read/write workflows do not require Vercel or Neon availability;
- remote synchronization or auxiliary services may degrade independently and must not destroy valid local state.

A local-first runtime is not permission to bypass consent, encryption, device access control, retention, or release gates. Those remain separate requirements.

### Remote development and certification stack

`iamina-certified` on Vercel, its Django runtime and the dedicated Neon database are development, integration and certification infrastructure. They are not the patient production runtime and must not be used as evidence that patient production depends on Vercel/Neon.

Unless a separately approved scope explicitly says otherwise, that remote stack is restricted to synthetic or non-patient engineering/certification data.

### Remote account functions

Django native identity is the current authoritative remote account identity for optional remote API functions. Firebase is a migration bridge only and is disabled by default unless a controlled migration window is explicitly enabled.

Patient first enrollment is device-local by default. Remote account creation is disabled by default and requires the explicit build-time flag `IAMINA_REMOTE_ACCOUNT_ENROLLMENT=true`. Calling the remote-registration API surface while that flag is disabled fails closed; it never silently substitutes local enrollment. Remote credential verification and password recovery may require connectivity, but their unavailability must not erase local enrollment or make locally persisted clinical data unusable.

Password-recovery email transport is therefore an auxiliary remote-account concern, not a patient-runtime availability dependency.

## Authentication boundary

IAMINA separates two states that were previously conflated:

1. **local enrollment/session**: a device-local enrollment marker plus opaque installation identifier held through `flutter_secure_storage`; it gates access to the enrolled local application and survives remote-service failure;
2. **remote API credential**: the Django-signed IAMINA bearer used only when calling remote APIs. It can expire or be revoked without erasing the local enrollment or device-local clinical state.

The local enrollment is deliberately **not described as a password, biometric, passkey or strong standalone user-authentication factor**. Until a separately reviewed biometric/passkey gate exists, physical device/OS/browser-profile access control remains part of the local security boundary. The unresolved app-specific re-authentication gap is tracked as `TD-014` in `docs/TECHDEBT.md` and remains high priority before identifiable real-patient release.

Legacy installs that already hold a syntactically valid `iamina.` native bearer but predate the explicit local-enrollment marker are migrated once to the local marker. Arbitrary secure-storage strings are never accepted as IAMINA enrollment evidence.

Rules:

- first patient enrollment: create opaque device identifier + local marker with zero network call;
- local boot: read local enrollment with zero network call;
- optional remote login can create/retain local enrollment and a separately verified bearer;
- remote account registration fails closed unless the explicit remote-account build flag is enabled;
- a remote API `401` invalidates the remote bearer only; it does not erase local enrollment;
- remote API calls remain independently authenticated and may be unavailable until remote re-authentication;
- explicit sign-out clears remote bearer, local marker and local device identifier regardless of remote availability.

This deliberately means a Vercel/Django outage, token expiry or remote credential revocation cannot remotely lock a patient out of enrolled device-local clinical data. Any future remote-wipe or device-revocation capability requires its own explicit product, safety and governance contract rather than piggybacking on the development API bearer.

## Infrastructure interpretation

Historical Vercel/Neon deployment evidence proves only that the development/certification Django path worked for the referenced source SHA. It does not establish, define or certify the patient production topology.

Before any real-patient release, compliance and safety evidence must be bound to the actual patient runtime and every genuinely enabled external processor. Development-only infrastructure must not be promoted into that inventory merely because it exists.

## Acceptance proof for AUTH-LOCAL-FIRST

The auth boundary is considered corrected only when automated tests prove:

- first device enrollment succeeds with zero network request;
- first enrollment creates a local marker and opaque device identifier but no remote bearer;
- local enrollment cannot occur before auth initialization;
- remote account enrollment fails closed by default and creates no local state;
- legacy native bearer migrates locally with zero boot network;
- marker-only local reopen requires zero network request;
- optional successful remote login retains local enrollment and independently verifies the bearer;
- remote-bearer invalidation preserves local enrollment;
- explicit sign-out clears local marker, remote bearer and local device identifier;
- malformed secure-storage text never becomes IAMINA enrollment evidence;
- existing auth, offline persistence and route-guard tests remain green.

UI wording must also tell the truth: the default patient enrollment action must not imply that an online Django account is being created when the remote-account flag is disabled.

This document does not itself authorize real-patient processing or a deployment.
