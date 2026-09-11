#!/usr/bin/env python3
"""Static P5-4 pilot packaging contract.

Default mode validates retained repository-side packaging foundations.
``--pwa-ready`` adds the PWA installability/identity floor for the current
PWA-first pilot path. ``--release-ready`` adds the deferred native iOS
permanent-identity floor required before signed native pilot artifacts are
accepted.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_APP_ID = "ma.iamina.app"
CANONICAL_PWA_NAME = "IAMINA"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pwa-ready", action="store_true")
    parser.add_argument("--release-ready", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    gradle = read("frontend/android/app/build.gradle.kts")
    android_ignore = read("frontend/android/.gitignore")
    release_doc = read("docs/PILOT_RELEASE.md")
    backend_firebase_policy = read("backend/core/firebase_migration_policy.py")
    flutter_firebase_policy = read("frontend/lib/services/firebase_migration_policy.dart")
    flutter_main = read("frontend/lib/main.dart")
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
        "com.google.gms.google-services" not in gradle,
        "Android pilot target still applies the Firebase Google Services plugin",
        errors,
    )
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
    require(
        'os.environ.get("ENABLE_FIREBASE_MIGRATION", "false")' in backend_firebase_policy,
        "Backend Firebase migration is not fail-closed by default",
        errors,
    )
    require(
        "defaultValue: false" in flutter_firebase_policy,
        "Flutter Firebase migration is not fail-closed by default",
        errors,
    )
    require(
        "if (kFirebaseMigrationEnabled)" in flutter_main,
        "Flutter startup does not gate Firebase initialization",
        errors,
    )

    pubspec = read("frontend/pubspec.yaml")
    require(
        re.search(r"(?m)^version: \d+\.\d+\.\d+\+\d+$", pubspec) is not None,
        "pubspec version must remain SemVer+integer build number",
        errors,
    )

    if args.pwa_ready:
        manifest = json.loads(read("frontend/web/manifest.json"))
        index = read("frontend/web/index.html")

        require(
            manifest.get("name") == CANONICAL_PWA_NAME,
            "PWA manifest name is not IAMINA",
            errors,
        )
        require(
            manifest.get("short_name") == CANONICAL_PWA_NAME,
            "PWA manifest short_name is not IAMINA",
            errors,
        )
        require(
            manifest.get("id") == ".",
            "PWA manifest must retain a stable relative id",
            errors,
        )
        require(
            manifest.get("start_url") == ".",
            "PWA manifest start_url must remain deployment-path portable",
            errors,
        )
        require(
            manifest.get("display") == "standalone",
            "PWA manifest display mode is not standalone",
            errors,
        )
        require(
            manifest.get("prefer_related_applications") is False,
            "PWA manifest must not prefer a native application on the PWA-first path",
            errors,
        )
        require(
            "A new Flutter project." not in manifest.get("description", ""),
            "PWA manifest still contains Flutter placeholder description",
            errors,
        )

        icon_contract = {
            ("icons/Icon-192.png", "192x192", None),
            ("icons/Icon-512.png", "512x512", None),
            ("icons/Icon-maskable-192.png", "192x192", "maskable"),
            ("icons/Icon-maskable-512.png", "512x512", "maskable"),
        }
        icons = {
            (icon.get("src"), icon.get("sizes"), icon.get("purpose"))
            for icon in manifest.get("icons", [])
        }
        require(
            icon_contract.issubset(icons),
            "PWA manifest is missing required 192/512 regular or maskable icons",
            errors,
        )
        for src, _, _ in icon_contract:
            require(
                (ROOT / "frontend/web" / src).is_file(),
                f"PWA icon file is missing: {src}",
                errors,
            )

        require(
            '<link rel="manifest" href="manifest.json">' in index,
            "Web index does not link the PWA manifest",
            errors,
        )
        require(
            '<meta name="mobile-web-app-capable" content="yes">' in index,
            "Web index is missing mobile-web-app-capable metadata",
            errors,
        )
        require(
            '<meta name="apple-mobile-web-app-capable" content="yes">' in index,
            "Web index is missing Apple PWA-capable metadata",
            errors,
        )
        require(
            '<meta name="apple-mobile-web-app-title" content="IAMINA">' in index,
            "Web index Apple title is not IAMINA",
            errors,
        )
        require(
            "<title>IAMINA</title>" in index,
            "Web document title is not IAMINA",
            errors,
        )
        require(
            "A new Flutter project." not in index,
            "Web index still contains Flutter placeholder description",
            errors,
        )

    if args.release_ready:
        ios_project = read("frontend/ios/Runner.xcodeproj/project.pbxproj")
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

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    modes = ["foundation"]
    if args.pwa_ready:
        modes.append("pwa-ready")
    if args.release_ready:
        modes.append("native-release-ready")
    print(f"P5-4 packaging {' + '.join(modes)} contract: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
