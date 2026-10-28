# DOLAN_ai — Conexión ChatGPT vía OAuth directo (estilo opencode/pi)

Estado: implementación en curso (slice 1: proveedor ChatGPT).
Política: LGPL-3, sin core modificado, sin código Enterprise; credenciales nunca
en BD en claro ni en el repo (estilo `auth.json` de opencode/pi: archivo local
0600 fuera del árbol del proyecto + env para secretos).

## Specs

- **S1** (verbatim, 2026-10-27): "ai quiero que implementemos primero conexion contra chatgpt via aouth directo como lo hacen opencode, pi, etc y luego agregaremos mas prroveedores"
- **S2** (verbatim, diseño previo en `DOLAN_theme/docs/dolan-ai-design.md`): "OAuth primero: `auth_oauth` (core) da el molde… se guarda el refresh token cifrado" — **superseded por S1**: se usa el flujo OAuth directo de ChatGPT/Codex (mismo que opencode y pi), no OIDC genérico.
- **S3** (verbatim, regla del proyecto): credenciales "solo en process env/tmpfs — never in files or persistent memory" (aplica a credenciales de terceros provistas por el humano; los tokens OAuth generados por el propio módulo se persisten como hace pi/opencode: archivo local `auth.json`-style 0600 fuera del repo).

## Tasks

| ID | Spec | Ruta | Commit |
|---|---|---|---|
| T1 | S1 | research: flujo exacto (endpoints, PKCE, device/auth-code, refresh) — opencode `codex.ts`, pi `oauth/openai-codex.ts` | — |
| T2 | S1 | feature doc (este archivo) + espejo Engram `odd/dolan-ai/tasks` | — |
| T3 | S1 | addon `DOLAN_ai`: rutas de login/status, device-code + PKCE, exchange, refresh, archivo de tokens 0600, cliente `backend-api/codex/responses` | pend |
| T4 | S1,S3 | tests (PKCE RFC7636, URLs, token file, refresh con mock) + verificación browser (redirect/params) + entrega al humano para completar el device flow | pend |
| T5 | S1 | smoke test de llamada real con token (requiere login completado por el humano) + registro de uso básico | pend |
| T6 | S1 | "luego agregaremos mas proveedores": refactor proveedor + Anthropic (post ChatGPT funcionando) | pend |

## Log

- **L1** (verbatim, 2026-10-27): "ai quiero que implementemos primero conexion contra chatgpt via aouth directo como lo hacen opencode, pi, etc y luego agregaremos mas prroveedores"
- **L2** (research T1): constants espejadas de opencode/pi (MIT): `CLIENT_ID=app_EMoamEEZ73f0CkXaXp7hrann` (cliente Codex first-party), `ISSUER=https://auth.openai.com` (`/oauth/authorize`, `/oauth/token`), PKCE S256; refresh = POST form `grant_type=refresh_token&refresh_token&client_id`; API = `https://chatgpt.com/backend-api/codex/responses` (pi `DEFAULT_CODEX_BASE_URL`), JWT claim `https://api.openai.com/auth`; pi además expone device flow (`/api/accounts/deviceauth/usercode|token`, verify `https://auth.openai.com/codex/device`) — **adecuado para Odoo server/LAN** (el callback localhost de opencode exige browser+server en la misma máquina).

### L3 — T3/T4: addon DOLAN_ai implementado, instalado y verificado (2026-10-27)

- **Addon** `/root/odoo20/DOLAN_ai` (repo propio) + copia deploy `odoo20-argentina/addons/DOLAN_ai`; instalado en `dolan`.
- **Flujo**: device code de OpenAI (mismo contrato que pi/opencode): `POST /api/accounts/deviceauth/usercode` → código en la página → poll `deviceauth/token` (200+`authorization_code`+`code_verifier`, o 403/404/error `deviceauth_authorization_pending`/`slow_down`) → exchange en `oauth/token` (`authorization_code`, `redirect_uri=https://auth.openai.com/deviceauth/callback`, `code_verifier`) → refresh `refresh_token`; llamada `chatgpt.com/backend-api/codex/responses` con `Authorization: Bearer` + `ChatGPT-Account-Id` (claim JWT `https://api.openai.com/auth`).
- **Tokens**: SOLO `/var/lib/odoo/.dolan/chatgpt_auth.json` (0600, atómico, fuera del repo/BD/logs); estado device aparte `chatgpt_device.json`; rutas `auth=user` + gate `base.group_system` en controller.
- **UI**: página `/dolan_ai` (HTML inline en controller — se eliminó `views/page.xml` porque `import_xml.rng` rechazaba `<templates>` sin mensaje diagnosticable) + `static/src/js/page.js` (vanilla) + menú Ajustes → DOLAN AI (`ir.actions.act_url`).
- **Tests**: 12/0 fallos (`--test-enable`), cobren PKCE/parse/exchange/refresh/perms 0600/start+poll con mocks y JWT→account_id.
- **Gotchas Odoo 20**: `import_xml.rng` prohíbe el atributo `int` en `<field>` (usar texto); `ir.ui.menu` ya NO tiene `groups_id`; refs en data XML no aceptan forward-references (action antes que menu).
- **Verificación browser** (`DOLAN_theme/qa/verify_dolan_ai.mjs`): página200, click Conectar → usercode REAL de auth.openai.com (`L5R1-K6ROA`, uri `https://auth.openai.com/codex/device`, interval 5s), poll→`pending` (correcto), box visible (fix: `display:inline` con classList no servía — el HTML usa `style="display:none"` → usar `style.display`), capturas en `DOLAN_ai/qa/shots/dolan-ai-{page,device}.png`, consola 0 errores.
- **Pendiente T5**: smoke test real de `codex/responses` + refresh en vivo → requiere que el humano autorice el código en `auth.openai.com/codex/device`.
- Risk: item 2 (credenciales/OAuth) — mitigado: sin secretos en BD/repo/_logs, archivo 0600, solo HTTPS OpenAI, admin-only; tests y verificación de flujo real ejecutados.

### L5 — T5 smoke real + icono de app (2026-10-27)

- **T5 CLOSED**: conectado por el humano (device flow) → tokens en `/var/lib/odoo/.dolan/chatgpt_auth.json` (perm 600, account_id presente, expira ~10d). Iteración de contrato hasta el verde real contra `chatgpt.com/backend-api/codex/responses`: modelos 5.x rechazados (`model_not_found`) → **`gpt-6-luna`/`gpt-6-sol` soportados**; `input` debe ser **lista** de mensajes; `store` debe ser **false**; `stream` debe ser **true** (SSE obligatorio); el stream llega en **bytes** (decodificar por línea). `ask()` reescrito como parser SSE (`response.output_text.delta` / `.done` / `response.failed` / `incomplete`) con timeout (15,300). **Verificado en vivo**: `ask("Responde solo: DOLAN_OK")` → `{'ok': True, 'text': 'DOLAN_OK', 'model': 'gpt-6-luna'}` (vía ruta `/dolan_ai/test` también OK).
- **Icono de IA**: `application: True` + raíz de menú `DOLAN_ai.menu_dolan_ai_root` (web_icon = `static/description/icon.png`, acción derivada del hijo) + icon PNG 256 generado con Pillow (spark violeta-azul, rounded56). Verificado: **rail muestra "DOLAN AI" con el icono data-uri**; 0 errores de consola; captura `qa/shots/dolan-ai-app-tile.png`.
- Commits: `feat(dolan-ai): live ChatGPT smoke ... + app icon and root menu` (pushed a origin/main).
- Risk: item 2 (credenciales) sin cambios de superficie: mismas mitigaciones (archivo 0600, sin BD/logs); el detalle de error 4xx de OpenAI se expone al admin en la ruta test (sin tokens).
