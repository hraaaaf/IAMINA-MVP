"""Fail-closed capability check for atomic mode-0600 private exports.

Windows os.chmod cannot provide POSIX ACL isolation; do not treat it as
sufficient for patient, incident, pilot or safety-review artifacts.
"""

import os


def supports_private_file_mode() -> bool:
    return os.name == "posix" and callable(getattr(os, "fchmod", None))
