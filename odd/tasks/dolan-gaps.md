# DOLAN gaps finales — Taller, Declaración fiscal, OCR, IA-agentes

Estado: en construcción (orden L27). Specs verbatim en ## Log; decisions L27a-d.

## Specs

- **S1** (verbatim L27a): construir DOLAN_taller, Declaración fiscal AR, OCR compras (F4), IA-agentes v1.
- **S2** (verbatim L27b): OCR = motor ChatGPT (cloud) con el token ya conectado.
- **S3** (verbatim L27c): IA-agentes v1 con tool-loop, permisos por herramienta (ítem 2 de seguridad: sin secretos en BD/repo, allowlist de modelos, sin borrado masivo).
- **S4** (verbatim L27d): F5 hito 2 después de los gaps.

## Tasks

| ID | Spec | Módulo | Alcance v1 | Estado |
|---|---|---|---|---|
| T1 | S2 | DOLAN_ai | OCR compra: adjuntar imagen → ChatGPT vision (input_image) → JSON → factura borrador `in_invoice` con líneas; page + ruta /dolan_ai/ocr_scan; tests con mocks (json extract, mapeo partner/tax por defecto, fallo OCR) | en curso |
| T2 | S1 | DOLAN_declaracion | períodos fiscales (mes/año) + checklist cierre (IVA digital, ventas, compras, CAE pendientes) con estados; KPI page; tests | pend |
| T3 | S1 | DOLAN_taller | centros de trabajo tablet: OP activa, operador, registrar consumo, timer por operación, punto de control QC (usa DOLAN_calidad); tests | pend |
| T4 | S3 | DOLAN_ai | agentes v1: registro (nombre+chips), tool-loop JSON con allowlist (search_read/create), máx iteraciones, sin unlink, log de uso | pend |

## Log

- **L1** (verbatim): "haceme las preguntas para destrabar y podedr terminar todos los modulos" + respuestas L27a-d del plan (S1-S4).
