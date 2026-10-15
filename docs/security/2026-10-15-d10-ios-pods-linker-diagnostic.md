# D10-B / #1057 — evidence-only iOS Simulator linker diagnosis

Goal: identify why the iOS debug Simulator build fails at Pods_Runner before XCTest, while signed-off release packaging without signing succeeds. This is NOT a production code fix.

BEFORE: D10 iOS PR #1053 tried the CocoaPods Debug xcconfig fix and Flutter 3.41.4; its three simulator builds still failed with Framework 'Pods_Runner' not found. The macOS Foundation unit smoke test was successful and must not be relabelled iOS XCTest.

This workflow runs one instrumented debug Simulator build with Flutter 3.41.4, captures the actual error and xcodebuild Debug simulator effective search/architecture settings, and uploads only a curated JSON artifact. It intentionally reports the observed linker failure without failing the evidence collection job. It never runs on patient data, does not deploy to Vercel, and cannot prove iCloud restoration or medical readiness.

Success: the diagnostic JSON contains the actual build exit status, classification, generated Pods framework config/project/workspace presence, and selected linker settings. A green run means evidence was collected, not that iOS Simulator is fixed.

Next: inspect the diagnostic artifact and implement the minimum reproducible linker configuration fix on a separate code PR; require real Simulator XCTest before closing issue #1057. D11 draft #1021 and synthetic integration #1059 remain untouched.
