#!/usr/bin/env python3
"""Static P5-4 pilot packaging contract.

Default mode validates repository-side preparation that can be proven without
private signing material or external Apple/Firebase configuration. --release-ready
adds permanent mobile-identity and FlutterFire rebinding floors required before
a signed pilot build is accepted.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_APP_ID = "ma.iamina.app"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-ready", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    gradle = read("frontend/android/app/build.gradle.kts")
    android_ignore = read("frontend/android/.gitignore")
    release_doc = read("docs/PILOT_RELEASE.md")

    require(
        "signingConfigs.getByName(\"debug\")" not in gradle,
        "Android release path still references the debug signing key",
        errors,
    )
    require(
        'create("release")' in gradle and "releaseSigningConfigured" in gradle,
        "Android release signing is not fail-closed on private key.properties",
        errors,
    )
    require(
        "key.properties" in android_ignore and "**/*.jks" in android_ignore,
        "Android signing material is not explicitly ignored",
        errors,
    )
    require(
        f"`{CANONICAL_APP_ID}`" in release_doc,
        "Pilot release document does not freeze the canonical app ID",
        errors,
    )

    pubspec = read("frontend/pubspec.yaml")
    require(
        re.search(r"(?m)^version: \d+\.\d+\.\d+\+\d+$", pubspec) is not None,
        "pubspec version must remain SemVer+integer build number",
        errors,
    )

    if args.release_ready:
        ios_project = read("frontend/ios/Runner.xcodeproj/project.pbxproj")
        firebase_options = read("frontend/lib/firebase_options.dart")
        main_activity_path = ROOT / (
            "frontend/android/app/src/main/kotlin/ma/iamina/app/MainActivity.kt"
        )

        require(
            f'applicationId = "{CANONICAL_APP_ID}"' in gradle,
            "Android applicationId is not the canonical pilot ID",
            errors,
        )
        require(
            f'namespace = "{CANONICAL_APP_ID}"' in gradle,
            "Android namespace is not the canonical pilot ID",
            errors,
        )
        require(
            main_activity_path.exists()
            and main_activity_path.read_text(encoding="utf-8").startswith(
                f"package {CANONICAL_APP_ID}\n"
            ),
            "Android MainActivity package does not match the canonical pilot ID",
            errors,
        )
        require(
            "com.example.amina" not in ios_project,
            "iOS project still contains placeholder com.example.amina identifiers",
            errors,
        )
        require(
            f"PRODUCT_BUNDLE_IDENTIFIER = {CANONICAL_APP_ID};" in ios_project,
            "iOS Runner bundle ID is not the canonical pilot ID",
            errors,
        )
        require(
            "com.example.amina" not in firebase_options
            and f"iosBundleId: '{CANONICAL_APP_ID}'" in firebase_options,
            "FlutterFire mobile options are not rebound to the canonical pilot identity",
            errors,
        )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    mode = "release-ready" if args.release_ready else "foundation"
    print(f"P5-4 packaging {mode} contract: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
