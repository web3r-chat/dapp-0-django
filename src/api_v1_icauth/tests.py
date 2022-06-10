"""Tests

https://github.com/vitalik/django-ninja/issues/258
https://docs.djangoproject.com/en/4.0/topics/testing/tools/
https://docs.djangoproject.com/en/4.0/topics/testing/tools/#testing-asynchronous-code
"""

from django.test import TestCase, AsyncClient  # type: ignore[attr-defined]


class ApiV1IcauthTestCase(TestCase):
    """Unit tests"""

    def setUp(self) -> None:
        """Every api test needs a client"""
        self.async_client = AsyncClient()

    async def test_api_v1_icauth_health(self) -> None:
        """Test api/v1/icauth/health"""
        response = await self.async_client.get("/api/v1/icauth/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ok")
