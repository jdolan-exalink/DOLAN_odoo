import base64
import json
import os
import tempfile
import time
from unittest import mock

from odoo.tests import TransactionCase, tagged

from ..models import chatgpt_oauth as ai


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


@tagged("post_install", "-at_install")
class TestDolanAiOauth(TransactionCase):

    def setUp(self):
        super().setUp()
        self._old_state = os.environ.get("DOLAN_AI_STATE_DIR")
        self.tmp = tempfile.mkdtemp(prefix="dolan-ai-test-")
        os.environ["DOLAN_AI_STATE_DIR"] = self.tmp

    def tearDown(self):
        if self._old_state is None:
            os.environ.pop("DOLAN_AI_STATE_DIR", None)
        else:
            os.environ["DOLAN_AI_STATE_DIR"] = self._old_state
        super().tearDown()

    # --- usercode -------------------------------------------------------
    def test_parse_usercode_ok(self):
        ok, data = ai.parse_usercode_response(
            200, json.dumps({"device_auth_id": "d1", "user_code": "ABCD-1234", "interval": 5}))
        self.assertTrue(ok)
        self.assertEqual(data["user_code"], "ABCD-1234")
        self.assertEqual(data["verification_uri"], ai.DEVICE_VERIFICATION_URI)

    def test_parse_usercode_404(self):
        ok, data = ai.parse_usercode_response(404, "")
        self.assertFalse(ok)
        self.assertEqual(data["error"], "device_code_no_disponible")

    def test_parse_usercode_bad_json(self):
        ok, _ = ai.parse_usercode_response(200, "no-json")
        self.assertFalse(ok)

    # --- device poll ----------------------------------------------------
    def test_parse_poll_pending_and_slowdown(self):
        self.assertEqual(ai.parse_device_poll(403, "")[0], "pending")
        self.assertEqual(ai.parse_device_poll(200, json.dumps({"error": {"code": "deviceauth_authorization_pending"}}))[0], "pending")
        self.assertEqual(ai.parse_device_poll(200, json.dumps({"error": "slow_down"}))[0], "slow_down")

    def test_parse_poll_complete(self):
        status, payload = ai.parse_device_poll(
            200, json.dumps({"authorization_code": "c1", "code_verifier": "v1"}))
        self.assertEqual(status, "complete")
        self.assertEqual(payload["authorization_code"], "c1")

    # --- token response -------------------------------------------------
    def _fake_resp(self, status, payload):
        resp = mock.Mock()
        resp.status_code = status
        resp.json.return_value = payload
        resp.text = json.dumps(payload)
        return resp

    def test_exchange_parses_and_extracts_account(self):
        header = _b64url(json.dumps({"alg": "RS256"}).encode())
        payload = _b64url(json.dumps({ai.JWT_ACCOUNT_CLAIM: {"chatgpt_account_id": "acct-1"}}).encode())
        token = f"{header}.{payload}.sig"
        with mock.patch.object(ai.requests, "post") as post:
            post.return_value = self._fake_resp(200, {
                "access_token": token, "refresh_token": "r1", "expires_in": 3600})
            data = ai.exchange_tokens("code", "verifier")
        self.assertEqual(data["account_id"], "acct-1")
        self.assertGreater(data["expires_at"], time.time() + 3500)
        body = post.call_args.kwargs.get("data") or post.call_args[1].get("data")
        self.assertEqual(body["grant_type"], "authorization_code")
        self.assertEqual(body["redirect_uri"], ai.DEVICE_REDIRECT_URI)
        self.assertNotIn("client_secret", body)

    def test_token_response_invalid(self):
        with mock.patch.object(ai.requests, "post") as post:
            post.return_value = self._fake_resp(200, {"access_token": "x"})
            self.assertIsNone(ai.exchange_tokens("c", "v"))

    # --- archivo de tokens ---------------------------------------------
    def test_token_file_roundtrip_and_0600(self):
        ai._atomic_write_json(ai._token_path(), {"access_token": "a", "refresh_token": "r", "expires_at": time.time() + 9999, "account_id": "acc"})
        mode = os.stat(ai._token_path()).st_mode & 0o777
        self.assertEqual(mode, 0o600)
        with mock.patch.object(ai.requests, "post") as post:
            post.side_effect = AssertionError("no debe refrescar: esta vigente")
            tokens = ai.get_valid_tokens()
        self.assertEqual(tokens["access_token"], "a")

    def test_refresh_when_expired(self):
        ai._atomic_write_json(ai._token_path(), {"access_token": "old", "refresh_token": "r0", "expires_at": time.time() - 10, "account_id": "acc"})
        with mock.patch.object(ai.requests, "post") as post:
            post.return_value = self._fake_resp(200, {"access_token": "new", "refresh_token": "r1", "expires_in": 3600})
            tokens = ai.get_valid_tokens()
        self.assertEqual(tokens["access_token"], "new")
        body = post.call_args.kwargs.get("data") or post.call_args[1].get("data")
        self.assertEqual(body["grant_type"], "refresh_token")

    # --- start + poll integrado con mocks -------------------------------
    def test_start_writes_device_state(self):
        with mock.patch.object(ai.requests, "post") as post:
            post.return_value = self._fake_resp(200, {"device_auth_id": "d1", "user_code": "WXYZ-9876", "interval": 4})
            data = ai.start_device_flow()
        self.assertEqual(data["user_code"], "WXYZ-9876")
        self.assertTrue(os.path.exists(ai._device_path()))
        self.assertEqual(os.stat(ai._device_path()).st_mode & 0o777, 0o600)

    def test_poll_success_writes_tokens_and_clears_device(self):
        ai._atomic_write_json(ai._device_path(), {"device_auth_id": "d1", "user_code": "U", "started_at": int(time.time())})
        header = _b64url(b"{}")
        payload = _b64url(json.dumps({ai.JWT_ACCOUNT_CLAIM: {"chatgpt_account_id": "acct"}}).encode())
        token = f"{header}.{payload}.sig"
        with mock.patch.object(ai.requests, "post") as post:
            post.side_effect = [
                self._fake_resp(200, {"authorization_code": "c1", "code_verifier": "v1"}),
                self._fake_resp(200, {"access_token": token, "refresh_token": "r1", "expires_in": 3600}),
            ]
            res = ai.poll_once()
        self.assertEqual(res["status"], "connected")
        self.assertTrue(os.path.exists(ai._token_path()))
        self.assertFalse(os.path.exists(ai._device_path()))

    # --- cuenta JWT -----------------------------------------------------
    def test_extract_account_id_malformed(self):
        self.assertIsNone(ai.extract_account_id("not-a-jwt"))
        self.assertIsNone(ai.extract_account_id("a.b.c"))
