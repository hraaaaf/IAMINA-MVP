"""D10-B Android backup policy source and merged-manifest guardrail.

Source-level checks cannot prove Android OEM D2D, cloud or cross-platform transfer.
"""
from pathlib import Path
import sys
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "frontend/android/app/src/main"
ANDROID = "{http://schemas.android.com/apk/res/android}"
DOMAINS = {"root", "file", "database", "sharedpref", "external",
           "device_root", "device_file", "device_database", "device_sharedpref"}


def assert_manifest_policy(path: Path) -> None:
    root = ET.parse(path).getroot()
    application = root.find("application")
    if application is None:
        raise AssertionError("Android application element missing")
    expected = {
        "allowBackup": "false",
        "fullBackupContent": "@xml/iamina_full_backup_content",
        "dataExtractionRules": "@xml/iamina_data_extraction_rules",
    }
    for key, value in expected.items():
        actual = application.get(ANDROID + key)
        if actual != value:
            raise AssertionError(f"{path}: {key} expected {value!r}, got {actual!r}")


class BackupConfigTests(unittest.TestCase):
    def test_manifest_config_and_targets(self):
        assert_manifest_policy(APP / "AndroidManifest.xml")
        self.assertTrue((APP / "res/xml/iamina_full_backup_content.xml").is_file())
        self.assertTrue((APP / "res/xml/iamina_data_extraction_rules.xml").is_file())

    def check_all_excluded(self, node):
        self.assertIsNotNone(node)
        self.assertEqual(node.findall("include"), [], "No backup includes are permitted")
        exclusions = {(x.attrib.get("domain"), x.attrib.get("path"))
                      for x in node.findall("exclude")}
        self.assertTrue({(name, ".") for name in DOMAINS}.issubset(exclusions),
                        f"Missing exclusions: {DOMAINS - {d for d, p in exclusions if p == '.'}}")

    def test_android12_cloud_and_d2d(self):
        root = ET.parse(APP / "res/xml/iamina_data_extraction_rules.xml").getroot()
        self.assertEqual(root.tag, "data-extraction-rules")
        self.check_all_excluded(root.find("cloud-backup"))
        self.check_all_excluded(root.find("device-transfer"))

    def test_android11_legacy(self):
        root = ET.parse(APP / "res/xml/iamina_full_backup_content.xml").getroot()
        self.assertEqual(root.tag, "full-backup-content")
        self.check_all_excluded(root)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--merged-manifest":
        assert_manifest_policy(Path(sys.argv[2]))
        print("MERGED_MANIFEST_BACKUP_POLICY_OK:", sys.argv[2])
    else:
        unittest.main()
