# D10-B — Android backup exclusion (non-production hardening)

**Goal:** deny cloud Auto Backup and Android device-to-device backup of patient-local SQLite, credentials, preferences and files. This reduces unintended copying and is **not** an opt-out app-lock implementation.

**Proof:** `scripts/tests/test_d10_android_backup_protection.py` requires allowBackup=false plus nine domain-wide exclusions in both Android 11 legacy and Android 12+ cloud/D2D XML. `.github/workflows/d10-android-backup-protection.yml` compiles a **debug APK** and verifies the *merged manifest*. The GitHub Actions run result, not this statement, determines success.

**Risk/limitations:** Disabling system backups can prevent recovery/migration onto a new device; existing D9 owner-bound recovery and D31 physical verification remain separate. Android OEMs and future **cross-platform-transfer** pathways may behave differently; a compiled manifest test cannot prove their runtime behavior. Do not claim real-device protection without a backup/D2D restore experiment using synthetic data. No native APK signing/release, patient records, clinical outbound network calls or Vercel deployment in this lot.

**Primary references:** [Android backup guide](https://developer.android.com/identity/data/autobackup), [Android 12 D2D exceptions](https://developer.android.com/about/versions/12/behavior-changes-12).

**Next:** inspect release merged manifest and carry out Android 11/12+/OEM cloud/D2D/cross-platform synthetic-data tests before calling the Android protection certified. Independently address iOS protected files, Web storage, owner authorization, sync permission separation and the D10-B optional lock design.
