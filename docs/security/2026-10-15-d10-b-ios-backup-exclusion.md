# D10-B iOS — bounded backup exclusion, source and synthetic tests

**Goal:** reduce accidental iCloud backup of existing patient-scoped Drift SQLite files, without moving/opening/copying existing databases, changing the lock, modifying medical data, or excluding unrelated user documents.

**Verified path/source:** `driftDatabase(name: scope.databaseName)` uses `getApplicationDocumentsDirectory()/$name.sqlite` on native platforms in the current drift_flutter API. The patient prefix is `amina_vault_v1_`, so the code only considers that prefix plus `.sqlite`, `.sqlite-wal` and `.sqlite-shm`; legacy `amina.sqlite` and unrelated Documents remain untouched.

**Bounded implementation:** at launch, enter-background and enter-foreground, AppDelegate marks existing patient-scoped SQLite and WAL/SHM files with Apple's `isExcludedFromBackup` property. Tests in `RunnerTests.swift` use only temporary synthetic files and check scoped matching, real backup resource attributes, unrelated files left unaffected, and repeatability. GitHub Actions compiles an unsigned simulator app and executes XCTest; **only a successful exact-run result establishes these synthetic tests passed.**

**Critical limitations:** Apple's backup exclusion is advisory, file modification may reset it, files created while foregrounded are not immediately marked, and no actual iCloud backup or device migration has been performed. This is **NOT proof of end-to-end backup exclusion or encryption**. The app-lock remains mandatory. No file-protection class `NSFileProtectionComplete` is changed because switching it without a verified database lifecycle may break SQLite in background. iOS data-at-rest hardening and migration/recovery testing remain a separate gate [#1052](https://github.com/hraaaaf/IAMINA-MVP/issues/1052).

Primary sources: [Apple isExcludedFromBackup](https://developer.apple.com/documentation/foundation/urlresourcevalues/isexcludedfrombackup), [Apple FileProtectionType](https://developer.apple.com/documentation/foundation/fileprotectiontype), [drift_flutter native database path](https://pub.dev/documentation/drift_flutter/latest/drift_flutter/driftDatabase.html).

**Next:** if compile/test green, merge this narrow change, verify postmerge. Then qualify stronger iOS file protection + lifecycle and Web vault encryption/owner policy for optional lock B. No patient data and no Vercel deployment in this lot.


## UIKit scene lifecycle correction — 15 Oct 2026

`Info.plist` enables `UIApplicationSceneManifest`; UIKit dispatches
scene foreground/background transitions to `FlutterSceneDelegate`, rather
than equivalent `AppDelegate` callbacks. Added `SceneDelegate` reapplication
of `ClinicalVaultBackupExclusion.applyToDocumentsDirectory()` in
`sceneWillEnterForeground` and `sceneDidEnterBackground`, retaining
launch handling in `AppDelegate`. Reference: [Apple scene lifecycle](https://developer.apple.com/documentation/uikit/uiscenedelegate) and [sceneDidEnterBackground](https://developer.apple.com/documentation/uikit/uiscenedelegate/scenedidenterbackground(_:)).
This reduces missing lifecycle hooks; it does not address newly created
database files during an active foreground session or provide evidence of
actual iCloud backup exclusion.
