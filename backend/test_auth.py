import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
from fastapi.testclient import TestClient

from backend.main import app, session_manager


TEST_USERNAME = "test-admin"
TEST_PASSWORD = "test-password"
TEST_SECRET = "test-secret-key-with-at-least-thirty-two-bytes"


class AdminAuthTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(
            os.environ,
            {
                "ADMIN_USERNAME": TEST_USERNAME,
                "ADMIN_PASSWORD": TEST_PASSWORD,
                "JWT_SECRET_KEY": TEST_SECRET,
            },
        )
        self.env.start()
        self.client = TestClient(app)
        session_manager._sessions.clear()
        session_manager._rate_limits.clear()

    def tearDown(self):
        self.env.stop()

    def test_login_returns_admin_jwt(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        payload = jwt.decode(
            result["access_token"],
            TEST_SECRET,
            algorithms=["HS256"],
        )
        self.assertEqual(result["role"], "admin")
        self.assertEqual(payload["sub"], TEST_USERNAME)
        self.assertEqual(payload["role"], "admin")

    def test_invalid_credentials_are_rejected(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": TEST_USERNAME, "password": "wrong"},
        )

        self.assertEqual(response.status_code, 401)

    def test_sync_requires_authentication(self):
        response = self.client.post("/api/admin/sync-solotodo")

        self.assertEqual(response.status_code, 401)

    def test_legacy_admin_page_is_not_served(self):
        response = self.client.get("/admin")

        self.assertEqual(response.status_code, 404)

    def test_sync_rejects_non_admin_role(self):
        now = datetime.now(timezone.utc)
        token = jwt.encode(
            {
                "sub": TEST_USERNAME,
                "role": "user",
                "iat": now,
                "exp": now + timedelta(minutes=5),
            },
            TEST_SECRET,
            algorithm="HS256",
        )

        response = self.client.post(
            "/api/admin/sync-solotodo",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, 403)

    def test_login_fails_closed_when_credentials_are_unconfigured(self):
        with patch.dict(
            os.environ,
            {"ADMIN_USERNAME": "", "ADMIN_PASSWORD": "", "JWT_SECRET_KEY": ""},
        ):
            response = self.client.post(
                "/api/auth/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )

        self.assertEqual(response.status_code, 503)

    def test_chat_session_token_is_required_for_chat_and_reset(self):
        session = self.client.post("/api/chat/session").json()
        body = {
            "session_id": session["session_id"],
            "session_token": session["session_token"],
        }

        unauthorized_chat = self.client.post(
            "/api/chat",
            json={**body, "mensaje": "Busco un notebook", "session_token": "wrong-token"},
        )
        self.assertEqual(unauthorized_chat.status_code, 401)

        unauthorized_reset = self.client.post(
            "/api/chat/reset",
            json={**body, "session_token": "wrong-token"},
        )
        self.assertEqual(unauthorized_reset.status_code, 404)

        authorized_reset = self.client.post("/api/chat/reset", json=body)
        self.assertEqual(authorized_reset.status_code, 200)

    def test_chat_quota_ignores_client_supplied_identifiers(self):
        with patch("guardrails.MIN_INTERVAL_SECONDS", 0):
            responses = []
            for index in range(11):
                session = self.client.post("/api/chat/session").json()
                responses.append(self.client.post(
                    "/api/chat",
                    json={
                        "mensaje": "Busco un notebook",
                        "session_id": session["session_id"],
                        "session_token": session["session_token"],
                        "client_id": f"forged-client-{index}",
                    },
                ))

        self.assertEqual(responses[9].status_code, 200)
        self.assertNotIn("límite", responses[9].json()["respuesta"])
        self.assertEqual(responses[10].status_code, 200)
        self.assertIn("límite", responses[10].json()["respuesta"])


if __name__ == "__main__":
    unittest.main()
