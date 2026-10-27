# DOLAN AI — Diseño del módulo (estado: diseño / backlog)

Documento de diseño (sin implementación) del módulo futuro **`dolan_ai`**, que
cubre las brechas de IA documentadas en `ee-parity-facturacion.md` (OCR de
compras, asistente) sin código Enterprise y sin tocar el core.

## 1. Objetivo

- **OCR de comprobantes de compra**: adjunto/foto → extraer campos → factura
  borrador (equivalente al "Subir/escanea con IA" de EE, resuelto con
  proveedor propio: es el candidato a cerrar la brecha "Compras con IA que
  escanea").
- **Asistente**: búsqueda semántica y respuesta en el chatter/buscador
  ("¿cuánto le debemos a X?").
- **Clasificación y conciliación asistida** (etiquetas de gasto, reglas).

## 2. Proveedores soportados (diseño a dos niveles)

| Nivel | Proveedor | Mecanismo | Configuración |
|---|---|---|---|
| Local | **Ollama** (modelos locales: llama3, qwen, etc.) | HTTP tipo OpenAI-compatible: `GET /api/tags`, `POST /api/chat` | `dolan.ai.provider` tipo `local`, endpoint `http://…:11434` |
| Cloud | **ChatGPT (OpenAI)** | OAuth authorization-code (con PKCE) para cuenta; fallback API key | proveedor `openai` |
| Cloud | **Claude (Anthropic)** | OAuth authorization-code; fallback API key (`x-api-key`) | proveedor `anthropic` |

Notas de diseño:

- **OAuth primero**: `auth_oauth` (core) da el molde de proveedor + redirección;
  se registra el flujo authorization-code con `state`/`nonce` propio y se guarda
  el *refresh token* cifrado. Los endpoints exactos se verifican al momento de
  implementar (son estables pero cambiaron entre versiones) — bloqueo de
  diseño, no de arquitectura.
- **Fallback API key** para quien prefiera llaves directas (OpenAI/Anthropic
  exponen API keys clásicas).
- **Abstracción `dolan.ai.provider`**: una sola interfaz (`generate`,
  `extract_json`, `health_check`) con adaptadores `ollama | openai | anthropic`
  → cambiar de proveedor o mezclar (OCR en cloud + asistente local) es dato,
  no código.

## 3. Modelo de datos (propuesto)

- `dolan.ai.provider` — nombre, tipo (`local|openai|anthropic`), endpoint base,
  modelo por defecto, estado OAuth, flags de uso permitido.
- `dolan.ai.credential` — credenciales **solo por referencia**: la clave vive
  en variable de entorno / secreto del contenedor (misma regla del proyecto:
  **nunca en archivos ni en BD en claro**); el modelo guarda `env_name`,
  alcance y rotación.
- `dolan.ai.usage` — log de llamadas (fecha, compañía, tokens in/out, costo
  estimado, caso de uso) → cuotas por compañía y trazabilidad.
- Parámetros de servicio vía `ir.config_parameter` **no sensibles**
  (modelos, límites, features flags) — sensibles solo por entorno.

## 4. Casos de uso por fase

| Fase | Caso | Dónde entra |
|---|---|---|
| F1 | OCR compra → borrador | adjunto en Facturas de compra → botón "Escanear (IA)" → prellene de `line_ids` (validable con la plantilla P3 y el dry-run antes de confirmar) |
| F2 | Asistente | comando de acción `>` en el buscador + chatter |
| F3 | Reglas asistidas | `base_automation` + proveedor (etiquetas de gasto, partners) |

## 5. Seguridad y riesgos (ítem 2 de la lista de riesgos)

- Sin credenciales en repo/BD: **solo env/secrets** (igual que certs y WSAA en
  esta instalación).
- ACLs finas: solo contadores/admin usan `dolan_ai`; log `usage` inmutable.
- Red: el proveedor cloud solo si el usuario lo habilita; por defecto **local
  (Ollama)** para datos de clientes (privacidad AR).
- Costo: cuotas por compañía + visibilidad en `dolan.ai.usage`.

## 6. Fueras de alcance

- Copiar código OCR/IA de Enterprise (OPL-1) — prohibido por política del
  proyecto.
- Modificar core de Odoo.
- Prometer calidad de OCR sin validar con comprobantes reales (el criterio de
  aceptación será: accuracy medida sobre un lote AR real del propio cliente).

## 7. Criterios de inicio

Requiere decisión del dueño de producto: proveedor cloud aprobado sí/no,
presupuesto de tokens y si F1 usa cloud o local. Hasta entonces queda en
backlog (`odd/tasks/dolan-theme.md`).
