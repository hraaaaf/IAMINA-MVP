"""D1-6 ephemeral HTTP interop fixture: NEVER a production settings module.

Run only with generated synthetic DB and runner-local network.
No Vercel route or deployment. Django sessions and CSRF stay enabled.
"""
from amina.settings import *  # noqa: F403,F401

ROOT_URLCONF = "core.tests.d1_passkey_test_urls"
D1_PASSKEY_RESEARCH_ENABLED = True
D1_PASSKEY_RESEARCH_RP_ID = (
    "iamina-review-9tskukqul-achraf-benmoussa-s-projects.vercel.app"
)
D1_PASSKEY_RESEARCH_ORIGIN = "https://" + D1_PASSKEY_RESEARCH_RP_ID
