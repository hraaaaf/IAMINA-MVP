"""Strict branch-and-email allowlist for ephemeral D1 Preview signup."""
import os
from unittest import TestCase
from unittest.mock import patch

from core.api.v1.auth import _native_registration_allowed_in_environment as allowed

LAB="preview/d1-test-accounts-backend-20261114"
class TestD1PreviewRegistration(TestCase):
    def test_preview_denies_everything_by_default(self):
        with patch.dict(os.environ,{"VERCEL_ENV":"preview","IAMINA_ENV":"development",
            "VERCEL_GIT_COMMIT_REF":LAB},clear=True):
            self.assertFalse(allowed("synthetic-a@d1-preview.test"))
    def test_opt_in_accepts_only_synthetic_test_domain_and_branch(self):
        env={"VERCEL_ENV":"preview","IAMINA_ENV":"development",
             "VERCEL_GIT_COMMIT_REF":LAB,"IAMINA_PREVIEW_ALLOW_REGISTRATION":"true"}
        with patch.dict(os.environ,env,clear=True):
            self.assertTrue(allowed("synthetic-a@d1-preview.test"))
            self.assertTrue(allowed("synthetic-b@d1-preview.test"))
            for email in ("real@gmail.com","user@iamina.com","patient@example.org",
                          "synthetic-a@d1-preview.test.evil","@d1-preview.test",""):
                self.assertFalse(allowed(email),email)
    def test_other_preview_branch_cannot_inherit_opt_in(self):
        with patch.dict(os.environ,{"VERCEL_ENV":"preview","IAMINA_ENV":"development",
            "VERCEL_GIT_COMMIT_REF":"main","IAMINA_PREVIEW_ALLOW_REGISTRATION":"true"},
            clear=True):
            self.assertFalse(allowed("synthetic-a@d1-preview.test"))
    def test_production_semantics_unchanged(self):
        with patch.dict(os.environ,{"VERCEL_ENV":"production","IAMINA_ENV":"production",
            "VERCEL_GIT_COMMIT_REF":"main"},clear=True):
            self.assertTrue(allowed("existing-production-register@any-domain.example"))
