# Paridad: IA EE (Agentes) vs DOLAN_ai v1

Evidencia: `docs/evidence/ee-demo/full/ia.png` (pantalla "Agentes").

## EE observado
- Menús: IA | Agentes / Configuración. Tarjetas de agentes con **chips de
  capacidades**: 
  - **Odoo AI** (sidekick): Shape View, Search Database, Update Records,
    Create Records, Accounting Report Analysis, Accounting, Build Automation.
  - **Audit Reviewer**: revisa evidencia/conclusiones de auditoría (Search
    Database, Accounting Audit Evidence).
  - **Auditor**: investiga y devuelve hallazgos revisados.

## Nuestro v1 (`DOLAN_ai`)
- Conexión ChatGPT por **OAuth device flow** (probada: gpt-6-luna, SSE) +
  página de estado/test + icono de app. Sin framework de agentes.

## Gaps (roadmap)
1. **Registro de agentes** (tarjetas + capacidades) — capa de UI tipo EE.
2. **Loop de herramientas** (tool-calling) contra ORM: Search/Update/Create
   records con permisos acotados (ítem 2 de seguridad: requiere diseño de
   permisos por herramienta).
3. Agentes de auditoría (flujo multi-paso evidencia→revisión) = investigación
   larga; no en v1.
4. Motor: sobre nuestro ChatGPT OAuth (decisión del usuario: sólo ChatGPT) —
   sin IAP ni código EE.

Veredicto: **gap grande** — paridad de *producto* (agente chat) lejana;
conexión base lista como prerrequisito.
