import os

from django.core.management import call_command

from amina.wsgi import application

# One-shot preview-only operational hook for the explicitly authorized
# production schema catch-up. The Django migration is idempotent and this hook
# is removed immediately after runtime proof.
if (
    os.environ.get("VERCEL_ENV") == "preview"
    and os.environ.get("VERCEL_GIT_COMMIT_REF") == "fix/hosted-auth-remote-gate"
):
    call_command(
        "migrate",
        "core",
        "0019_auth_abuse_bucket",
        interactive=False,
        verbosity=1,
    )

app = application
