# Cómo implementa IA el demo EE (análisis con capturas) vs DOLAN_ai

Evidencia: `evidence/ee-demo/full/ia.png`, `ia-agentes-grid.png`, `ia-agente-form.png`.

## Arquitectura EE observada
1. **App IA → Agentes** (kanban de agentes con chips de capacidades:
   Shape View, Search Database, Update Records, Create Records, Accounting
   Report Analysis, Accounting, Build Automation).
2. **Chat por agente**: vista tipo Discuss (sidebar de conversaciones + hilo +
   composer "Mensaje Odoo AI"), con **historial de conversaciones** por agente.
3. **Agente = registro con 4 pestañas**: **Instrucciones** (system-prompt
   editable: "You are the main Odoo AI Assistant…", Working Style,
   Collaboration — acciones vía *available tools*), **Habilidades** (tools),
   **Artículos** (contexto/documentos), **Activadores** (triggers).
4. Tool-loop implícito: las instrucciones dicen "proceed through the available
   tools or loaded workflows once the target… is clear" y si no puede,
   "explain the limitation and offer the closest useful next step".

## DOLAN_ai hoy (equivalencias)
| EE | Nuestro v1 | Estado |
|---|---|---|
| Registro de agentes con instrucciones | `dolan.ai.agente` con `proposito` (entra al prompt) | ✔ base; falta pestañas |
| Habilidades/tools con chips | allowlist `search_read`/`create` por agente (modelos_ids) | ✔ (2 tools; EE tiene 7) |
| Chat con historial | chat simple en `/dolan_ai` sin persistencia | ✗ → v2 |
| Activadores | — | ✗ (post) |
| Artículos (contexto) | — | ✗ (post) |

## Plan v2 (paridad gradual, sin IAP/EE)
1. **Chat con historial**: modelo `dolan.ai.conversacion` (agente, user,
   mensajes) + vista tipo chatter/composer; el loop arma el prompt con el
   historial (multi-turno real).
2. **Instrucciones completas**: campo `instrucciones` (text) editable por
   agente, inyectado como system-style prefix (ya tenemos proposito → renombrar
   y expandir).
3. **Más herramientas**: `write` (con allowlist de campos), `search_count`,
   `read` — siempre cap + sin unlink (ítem 2).
4. **Activadores**: post-v3 (base_automation integration).

## Conclusión
Nuestro tool-loop ya replica el mecanismo central de EE (agente + herramientas
ORM con permisos); la brecha es de **producto**: historial de chat, pestaña de
instrucciones y más herramientas. Viabilidad sin código EE: alta (todo es
modelos propios + nuestro OAuth ChatGPT).
