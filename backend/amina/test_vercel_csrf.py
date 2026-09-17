from django.test import RequestFactory, SimpleTestCase, override_settings

from amina.middleware.vercel_csrf import (
    IAMINA_FRONTEND_STABLE_ORIGIN,
    IaminaVercelCsrfViewMiddleware,
    is_iamina_frontend_origin,
)


class IaminaVercelCsrfOriginTests(SimpleTestCase):
    observed_deployment_origin = (
        "https://iamina-review-cyutt5fcm-achraf-benmoussa-s-projects.vercel.app"
    )

    def test_stable_alias_is_allowed(self):
        self.assertTrue(is_iamina_frontend_origin(IAMINA_FRONTEND_STABLE_ORIGIN))

    def test_observed_iamina_deployment_origin_is_allowed(self):
        self.assertTrue(is_iamina_frontend_origin(self.observed_deployment_origin))

    def test_unrelated_vercel_origin_is_rejected(self):
        self.assertFalse(is_iamina_frontend_origin("https://other-app.vercel.app"))

    def test_lookalike_account_origin_is_rejected(self):
        self.assertFalse(
            is_iamina_frontend_origin(
                "https://iamina-review-cyutt5fcm-attacker-projects.vercel.app"
            )
        )

    @override_settings(
        ALLOWED_HOSTS=["testserver"],
        CSRF_TRUSTED_ORIGINS=[IAMINA_FRONTEND_STABLE_ORIGIN],
    )
    def test_allowed_origin_does_not_bypass_csrf_token_validation(self):
        request = RequestFactory().post(
            "/api/v1/account/consent",
            HTTP_ORIGIN=self.observed_deployment_origin,
        )
        middleware = IaminaVercelCsrfViewMiddleware(lambda req: None)

        response = middleware.process_view(request, lambda req: None, (), {})

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)
