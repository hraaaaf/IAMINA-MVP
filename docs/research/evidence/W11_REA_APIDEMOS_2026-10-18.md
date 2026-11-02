# W11 — REA Android public APK: execution evidence (18 October 2026)

Scope: public, Apache-2.0 **Appium ApiDemos**, not any CGM application, no medical data.

## Goal → observable success → proof
- Goal: establish that the actual REA Android static inspection executes in a sandbox without vendor credentials, sensors or patient data.
- Observable success: REA CLI exact 6.7.0 and JADX 0.7.1 run on SHA-verified APK, produce machine-readable package inventory and class search.
- Proof: [GitHub Actions run #39153022150](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39153022150) **SUCCESS** on `8e1c89f4e6209e439451a0ce31afb6da3cfce94d`; [artifact #12145743184](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39153022150/artifacts/12145743184), extracted and JSON parsed. Artifact retention expires 2026-10-25.

## Verified hashes / versions
- `rea-agents`: 6.7.0, `rea --version` observed in job log.
- APK: `appium/android-apidemos` release v6.0.18, `ApiDemos-debug.apk`, SHA256 `a9eecf37b26cd084855c530db81c2bb1b91f4c1b095a04f47aa7c20e2791f686` (GitHub release metadata and successful runner check).
- JADX: `jadx-headless-mcp-0.7.1-all.jar`, SHA256 `6e5eacf500b64292bfb73c49797c1958f6ee44646e43e868039ae7feb573ff75` (REA source metadata and successful runner check).
- Engine: JADX 0.7.1, revision `5844800a486d2248fa949b74c9896285f5b54de2`, evidence ties to JAR SHA.

## Parsed evidence files
| File | Bytes | SHA256 |
|---|---:|---|
| `inspect.json` | 323994 | `ff035765382a4349e6ec3de898b30c7b143d987bc2860e3b84f1d6014e9ec74e` |
| `classes.json` | 3556 | `0d6f021a36bf2f3cc2c49d97fd0d7bf8e0677a2c3d83fe25cb0ea03f0d96cab5` |
| `doctor.json` | 6536 | `778947a73224c97ce15e850fc3ca74712317fb6cc9f092ded7ab6676817847e8` |
| `evidence-summary.json` | 327 | `cb3d7aab1ce046e769f732ffdf2f81d5e03e67ee720ff67466e8324b49315fa2` |

Decoded `inspect.normalized_result`: package `io.appium.android.apis`; version `6.0.18` (`version_code=44`), minSdk 26, targetSdk 33; `classes.normalized_result`: total_classes **2876** and two matches `io.appium.android.apis.ApiDemos` / `...ApiDemosApplication`, `coverage=complete` for queried class inventory. **Static only**.

## First failed run and remediation
Run [#39152544792](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39152544792) failed before inspection because `rea doctor` exited nonzero for optional Hopper/Ghidra/IDA/Kuna/skill absence, while Node/JADX checks were healthy in the saved artifact. Commit `8e1c89f4e6209e439451a0ce31afb6da3cfce94d` retains doctor JSON and explicitly gates on healthy Node and JADX; subsequent run above passed. This is NOT bypass of engine integrity.

## Not certified
No vendor APK, live network call, reverse-engineered authentication, iOS capability, real CGM feed, Django/Flutter Web integration or medical accuracy has been demonstrated. A separate independent review, software supply-chain check for npm transitive dependencies, privacy/clinical gates W01/W02 and authorized vendor artifact would be required to go further. **Do not use this success as production or clinical acceptance.**

**Next**: verify final exact-head CI after incorporating this report, then seek independent Reviewer + Certifier for the W11 research deliverable. No merge until gates satisfied.