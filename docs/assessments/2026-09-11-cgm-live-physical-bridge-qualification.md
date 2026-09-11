# CGM-LIVE-1 — Physical bridge qualification harness

**Date:** 2026-09-11  
**Status:** ENGINEERING_CLOSED / EXTERNAL_DEVICE_GATE

## Goal

Prepare one fail-closed, reusable qualification path proving that a configured physical CGM can traverse the already-certified IAMINA boundary:

`physical CGM -> external bridge -> Nightscout-compatible API -> IAMINA sync -> normalized persisted readings`

The first target is LinX through the already-qualified external Juggluco/Nightscout path. The harness is generic for the currently qualified source provenances: `linx`, `dexcom`, and `libre`.

## Success

A physical-device run is successful only when all of the following are simultaneously true:

1. the operator explicitly confirms an authorized non-patient test subject;
2. the operator explicitly confirms that the external bridge is currently fed by a physical sensor;
3. the configured IAMINA CGM connection source exactly matches the requested source;
4. IAMINA executes the real `sync_patient_cgm` provider/network path;
5. the provider returns at least the configured minimum number of readings;
6. the newest reading returned by that provider call is recent and not materially in the future;
7. IAMINA contains at least the same minimum number of recent persisted readings from that source;
8. the newest persisted timestamp is recent and not materially in the future;
9. the evidence output contains no glucose value, credential, bridge URL, patient identifier, or device identifier.

Default acceptance window: at least **2 readings within 15 minutes**. Both thresholds are configurable for legitimate sensor cadence differences.

## Engineering implementation

Command:

```bash
python manage.py audit_cgm_live_bridge \
  --patient-id <LOCAL_TEST_USER_ID> \
  --source linx \
  --confirm-authorized-non-patient-test-subject \
  --confirm-physical-sensor
```

Runtime prerequisites already enforced by IAMINA:

- `CGM_CREDENTIAL_KEY` is configured;
- the test user's CGM connection is configured and enabled;
- the Nightscout-compatible host is present in `CGM_ALLOWED_BRIDGE_HOSTS`;
- the bridge target is public HTTPS and passes the existing SSRF/network policy;
- LinX provenance is configured explicitly rather than inferred from arbitrary device text.

## Retained output boundary

The command emits only qualification metadata such as source, counts and reading ages. It intentionally does **not** emit:

- glucose values;
- credentials or tokens;
- bridge URL/hostname;
- patient/user identifier;
- sensor serial/device identifier.

A `PASS` therefore proves the engineering transport/storage path under the operator attestations. It does **not** prove regulatory approval, clinical safety, real-patient release authorization, CNDP compliance, or production deployment readiness.

## Automated proof retained

Implementation candidate: `796aae03581c8b4caa9f8bd8c86068474d729aba`.

- PR #563 pre-merge CI #3896 / run `34621157895`: **SUCCESS** on the exact candidate head;
- PR #563 pre-merge Django migration drift #3661 / run `34621157886`: **SUCCESS** on the exact candidate head;
- PR #563 merged to `main` as `bb5d735d7a676ea2bcb551649f594a50997c0b82`;
- post-merge Django migration drift #3662 / run `34621793504`: **SUCCESS** on the merge commit;
- post-merge CI #3897 / run `34621793542`: **CANCELLED** after `main` advanced to a direct descendant;
- current descendant `main@6bc6d22e5280104f62ef0846b87de27aaf6dbc91` has parent `bb5d735d7a676ea2bcb551649f594a50997c0b82` and CI #3898 / run `34621834334`: **SUCCESS**.

The engineering gate is therefore retained on `main` with passing exact-head pre-merge proof, passing migration proof after merge, and a passing CI on the immediate descendant that contains the merge unchanged.

Automated behaviors covered by the gate:

- command refuses to run without both explicit attestations;
- source mismatch fails closed before any provider call;
- stale provider readings fail closed even if the database already contains fresh rows;
- stale persisted readings fail closed even if the current provider result is fresh;
- successful evidence is non-clinical and secret-free.

## Remaining external gate

No software-only test can truthfully prove that a specific physical sensor is attached upstream. Final closure therefore requires one controlled physical LinX run with an authorized non-patient test subject and retained command output.

**Engineering closure:** CLOSED.  
**Physical-device closure:** OPEN until retained LinX physical evidence exists.
