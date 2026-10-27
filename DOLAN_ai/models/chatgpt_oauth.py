"""ChatGPT (Codex) OAuth — device-code flow, espejado de pi (badlogic/pi-mono
packages/ai/src/utils/oauth/openai-codex.ts) y opencode (codex.ts), ambos MIT.

Seguridad del slice:
- Tokens SOLO en archivo local 0600 fuera del repo (estilo auth.json de
  opencode/pi). Nunca en BD, nunca en logs, nunca en el repo.
- Rutas de mutacion exigidas a grupo sistema (admin) en el controlador.
- Solo endpoints HTTPS oficiales de OpenAI.
"""
import base64
import json
import logging
import os
import time

import requests

_logger = logging.getLogger(__name__)

CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"  # cliente first-party Codex ( igual que opencode/pi )
AUTH_BASE = "https://auth.openai.com"
DEVICE_USER_CODE_URL = f"{AUTH_BASE}/api/accounts/deviceauth/usercode"
DEVICE_TOKEN_URL = f"{AUTH_BASE}/api/accounts/deviceauth/token"
DEVICE_VERIFICATION_URI = f"{AUTH_BASE}/codex/device"
DEVICE_REDIRECT_URI = f"{AUTH_BASE}/deviceauth/callback"
TOKEN_URL = f"{AUTH_BASE}/oauth/token"
CODEX_API_ENDPOINT = "https://chatgpt.com/backend-api/codex/responses"
JWT_ACCOUNT_CLAIM = "https://api.openai.com/auth"
DEVICE_TIMEOUT_SECONDS = 15 * 60
HTTP_TIMEOUT = 20

DEFAULT_MODEL = "gpt-5.4-mini"


def _state_dir():
    return os.environ.get("DOLAN_AI_STATE_DIR") or "/var/lib/odoo/.dolan"


def _token_path():
    return os.path.join(_state_dir(), "chatgpt_auth.json")


def _device_path():
    return os.path.join(_state_dir(), "chatgpt_device.json")


def _atomic_write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(payload, fh)
            fh.flush()
            os.fsync(fh.fileno())
    except Exception:
        os.unlink(tmp)
        raise
    os.replace(tmp, path)
    os.chmod(path, 0o600)


def _read_json(path):
    try:
        with open(path, "r") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        _logger.warning("DOLAN_ai: no se pudo leer %s: %s", path, exc)
        return None


def extract_account_id(access_token):
    """chatgpt_account_id desde el claim JWT https://api.openai.com/auth."""
    try:
        parts = access_token.split(".")
        if len(parts) != 3:
            return None
        payload = parts[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload))
        return (data.get(JWT_ACCOUNT_CLAIM) or {}).get("chatgpt_account_id")
    except Exception:
        return None


def build_usercode_payload():
    return {"client_id": CLIENT_ID}


def parse_usercode_response(status_code, body_text):
    """-> (ok, dict|error). Salida usada por tests y por el controlador."""
    if status_code == 404:
        return False, {"error": "device_code_no_disponible"}
    if status_code != 200:
        return False, {"error": f"usercode_http_{status_code}"}
    try:
        data = json.loads(body_text)
    except ValueError:
        return False, {"error": "usercode_json_invalido"}
    device_auth_id = data.get("device_auth_id")
    user_code = data.get("user_code")
    interval = data.get("interval")
    if isinstance(interval, str):
        try:
            interval = int(interval.strip())
        except ValueError:
            interval = None
    if not device_auth_id or not user_code or not isinstance(interval, int) or interval < 0:
        return False, {"error": "usercode_campos_invalidos"}
    return True, {
        "device_auth_id": device_auth_id,
        "user_code": user_code,
        "interval": interval,
        "verification_uri": DEVICE_VERIFICATION_URI,
        "expires_in": DEVICE_TIMEOUT_SECONDS,
    }


def start_device_flow():
    resp = requests.post(
        DEVICE_USER_CODE_URL,
        json=build_usercode_payload(),
        timeout=HTTP_TIMEOUT,
    )
    ok, data = parse_usercode_response(resp.status_code, resp.text)
    if not ok:
        _logger.warning("DOLAN_ai: usercode fallo (%s)", data.get("error"))
        return data
    data["started_at"] = int(time.time())
    _atomic_write_json(_device_path(), data)
    return {
        "user_code": data["user_code"],
        "verification_uri": data["verification_uri"],
        "interval": data["interval"],
        "expires_in": data["expires_in"],
    }


def parse_device_poll(status_code, body_text):
    """-> (status, payload). status: complete|pending|slow_down|failed."""
    if status_code == 200:
        try:
            data = json.loads(body_text)
        except ValueError:
            return "failed", {"error": "poll_json_invalido"}
        code = data.get("authorization_code")
        verifier = data.get("code_verifier")
        if code and verifier:
            return "complete", {"authorization_code": code, "code_verifier": verifier}
        # 200 con cuerpo de error (algunos servidores lo hacen asi)
        err = data.get("error")
        err = err.get("code") if isinstance(err, dict) else err
        if err == "deviceauth_authorization_pending":
            return "pending", {}
        if err == "slow_down":
            return "slow_down", {}
        return "failed", {"error": "poll_campos_invalidos"}
    if status_code in (403, 404):
        return "pending", {}
    try:
        err = json.loads(body_text).get("error")
        err = err.get("code") if isinstance(err, dict) else err
    except (ValueError, AttributeError):
        err = None
    if err == "deviceauth_authorization_pending":
        return "pending", {}
    if err == "slow_down":
        return "slow_down", {}
    return "failed", {"error": f"poll_http_{status_code}"}


def exchange_tokens(authorization_code, code_verifier, redirect_uri=DEVICE_REDIRECT_URI):
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "code": authorization_code,
            "code_verifier": code_verifier,
            "redirect_uri": redirect_uri,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=HTTP_TIMEOUT,
    )
    return _parse_token_response(resp, "exchange")


def refresh_tokens(refresh_token):
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=HTTP_TIMEOUT,
    )
    return _parse_token_response(resp, "refresh")


def _parse_token_response(resp, op):
    if resp.status_code != 200:
        _logger.warning("DOLAN_ai: token %s fallo HTTP %s", op, resp.status_code)
        return None
    try:
        data = resp.json()
    except ValueError:
        return None
    if not data.get("access_token") or not data.get("refresh_token") or not isinstance(data.get("expires_in"), (int, float)):
        _logger.warning("DOLAN_ai: token %s con campos invalidos", op)
        return None
    account = extract_account_id(data["access_token"])
    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": int(time.time() + data["expires_in"]),
        "account_id": account,
        "obtained_at": int(time.time()),
    }


def poll_once():
    """Una pasada de poll; en complete arma y guarda tokens."""
    state = _read_json(_device_path())
    if not state:
        return {"status": "failed", "error": "sin_estado_device"}
    if int(time.time()) - int(state.get("started_at", 0)) > DEVICE_TIMEOUT_SECONDS:
        try:
            os.unlink(_device_path())
        except OSError:
            pass
        return {"status": "failed", "error": "device_expirado"}
    resp = requests.post(
        DEVICE_TOKEN_URL,
        json={
            "device_auth_id": state["device_auth_id"],
            "user_code": state["user_code"],
        },
        timeout=HTTP_TIMEOUT,
    )
    status, payload = parse_device_poll(resp.status_code, resp.text)
    if status == "complete":
        tokens = exchange_tokens(payload["authorization_code"], payload["code_verifier"])
        if not tokens:
            return {"status": "failed", "error": "exchange_fallo"}
        _atomic_write_json(_token_path(), tokens)
        try:
            os.unlink(_device_path())
        except OSError:
            pass
        return {"status": "connected", "account_id": tokens.get("account_id")}
    if status == "failed":
        try:
            os.unlink(_device_path())
        except OSError:
            pass
    return {"status": status, **payload}


def get_valid_tokens():
    """Tokens vigentes; refresca si expiraron. None = sin conexion."""
    tokens = _read_json(_token_path())
    if not tokens:
        return None
    if int(time.time()) < int(tokens.get("expires_at", 0)) - 60:
        return tokens
    refreshed = refresh_tokens(tokens.get("refresh_token"))
    if not refreshed:
        return {**tokens, "needs_reconnect": True}
    if not refreshed.get("account_id"):
        refreshed["account_id"] = tokens.get("account_id")
    _atomic_write_json(_token_path(), refreshed)
    return refreshed


def status():
    tokens = _read_json(_token_path())
    device = _read_json(_device_path())
    if not tokens:
        return {"connected": False, "device_pending": bool(device)}
    expired = int(time.time()) >= int(tokens.get("expires_at", 0))
    return {
        "connected": not tokens.get("needs_reconnect"),
        "needs_reconnect": bool(tokens.get("needs_reconnect")),
        "expired": expired,
        "account_id": tokens.get("account_id"),
        "device_pending": bool(device),
    }


def disconnect():
    removed = False
    for path in (_token_path(), _device_path()):
        try:
            os.unlink(path)
            removed = True
        except OSError:
            pass
    return removed


def ask(prompt, model=None, max_output_tokens=256):
    """Llamada minima a backend-api/codex/responses con Bearer + ChatGPT-Account-Id."""
    tokens = get_valid_tokens()
    if not tokens:
        return {"ok": False, "error": "no_conectado"}
    if tokens.get("needs_reconnect"):
        return {"ok": False, "error": "token_vencido_reconectar"}
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    if tokens.get("account_id"):
        headers["ChatGPT-Account-Id"] = tokens["account_id"]
    body = {
        "model": model or os.environ.get("DOLAN_AI_MODEL") or DEFAULT_MODEL,
        "input": prompt,
        "max_output_tokens": max_output_tokens,
    }
    try:
        resp = requests.post(CODEX_API_ENDPOINT, json=body, headers=headers, timeout=HTTP_TIMEOUT)
    except requests.RequestException as exc:
        return {"ok": False, "error": f"http_{exc.__class__.__name__}"}
    if resp.status_code == 401:
        return {"ok": False, "error": "unauthorized"}
    if resp.status_code not in (200, 201):
        return {"ok": False, "error": f"http_{resp.status_code}"}
    try:
        data = resp.json()
    except ValueError:
        return {"ok": False, "error": "json_invalido"}
    text_parts = []
    for item in data.get("output") or []:
        if item.get("type") == "message":
            for part in item.get("content") or []:
                if part.get("type") == "output_text":
                    text_parts.append(part.get("text", ""))
    if not text_parts and isinstance(data.get("output_text"), str):
        text_parts.append(data["output_text"])
    return {"ok": True, "text": "\n".join(text_parts), "model": body["model"]}
