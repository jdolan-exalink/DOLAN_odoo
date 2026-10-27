# Port l10n_ar_fiscal_ws 19.0 → 20.0 (finish WIP)

User decision (Log L1): port propio del módulo de facturación electrónica
AFIP/ARCA para Odoo 20, mientras la migración oficial de ingadhoc no se publique.

Base: la branch 20.0 de `ingadhoc/odoo-argentina-ce` ya contiene un port
sustancial de ADHOC (v20.0.1.0.0, ~4.048 líneas, manifest con `contacts` como
dependencia nueva, security renombrada). Está con `installable: False` porque
el repo entero está en WIP. Trabajo: terminar el WIP en un módulo propio,
validado contra nuestro stack `odoo20-argentina`.

Licencia: AGPL-3 (port legal; mantener atribución ADHOC/OCA).

## Specs

S1: Instalación headless exitosa de `l10n_ar_fiscal_ws` en Odoo 20 CE sobre la
base `argentina_test` de nuestro stack, sin errores de registro, vistas ni
datos.

S2: La suite de tests del módulo (`tests/test_*.py`) pasa con `--test-enable`
sobre la misma base, o cada fallo restante queda documentado con causa.

S3: El flujo funcional básico queda verificable: configuración de conexión
fiscal (WSAA), carga de certificado, tipos de comprobante ARCA en diarios y
moves, y el QR/informe de factura sin errores de carga de vistas.

S4: `crear_odoo20.sh` y `docs/ce-vs-enterprise.md` quedan actualizados con el
estado final (módulo disponible en nuestro stack; atribución y procedimiento).

## Tasks

- T1 [S1] Baseline: copiar el módulo 20.0 de ADHOC al stack, flip
  installable:True, intentar instalación headless, catalogar errores.
  Route: inline.
- T2 [S1] Fix iterativo de errores de instalación (core API/views 19→20).
  Route: inline (worker solo si emerge unidad independiente grande).
- T3 [S2] Suite de tests en verde o fallos documentados. Route: inline.
- T4 [S3] Verificación funcional de vistas/menús/wizards (carga HTTP + queries
  de modelos clave). Route: inline.
- T5 [S4] Docs y script actualizados. Route: inline.

## Log

- L1 (user, verbatim): "vamos por ahi, arranca" + seleccion de opcion
  "Port propio del fiscal_ws" (portear l10n_ar_fiscal_ws de 19.0 a 20.0
  nosotros, feature branch ODD).
- L2 (evidencia de exploracion): diff 19.0 vs 20.0 de odoo-argentina-ce:
  port de ADHOC ya realizado en 20.0 (version 20.0.1.0.0, dependencia
  contacts agregada, ir.model.access.csv -> ir.access.csv, 18 archivos py/xml
  diferidos). installable: False marca el repo WIP. 4048 lineas py en 20.0.
- L3 (T1-T2, 2026-10-26): flip installable:True + instalacion headless limpia
  en argentina_test (solo warnings cosmeticos: labels duplicados, markdown2).
  Modelos registrados: l10n_ar.fiscal.ws(+connection/mapping/recover),
  certificates, aliases; 28 mappings de datos cargados.
- L4 (T3 diagnostico): suite 38 tests, 0 failed, 2 error(s) —
  test_local_validation_without_certificates + cascada tearDownClass
  (savepoint colgado). Causa: el test asume homologacion por defecto pero
  _get_environment_type() cae a config['server_mode'] (no seteable en Odoo
  stock 19/20: no registrado en config.py) -> production -> UserError de
  certificado. El test es identico al de 19.0 y el compute identico; el
  modulo documenta que server_mode != production significa homologacion.
  Solucion: setear parametro de sistema l10n_ar_fiscal_ws.env_type=
  homologation en la base (default seguro para stack nuevo: nadie golpea
  produccion ARCA sin certificados). Artefacto de suite a vigilar: los
  tests de CAE hacen cr.commit() dentro de _l10n_ar_post_batch, lo que puede
  persistir env_type=production entre corridas (higiene de test upstream).
- L5 (T3 cierre): suite completa con env_type=homologation: **0 failed,
  0 error(s) of 38 tests** (52 ejecuciones, 32.75s, 79.4k queries). El param
  sobrevivio la corrida en homologation.
- L6 (T4): smoke funcional via odoo shell: entorno resuelve homologation,
  28 mappings, 6 webservices (LoginCms, wsfex, wsfecred, wsbfe, wsfe,
  ws_sr_padron_a5), wizard y certificados como modelos registrados; HTTP 200
  en la UI; vistas validadas en el registry load de la instalacion.
- L7 (T5): crear_odoo20.sh ahora habilita installable en
  l10n_ar_fiscal_ws tras clonar (commentado, solo ese modulo) y documenta el
  default de homologacion; docs/ce-vs-enterprise.md actualizado (fila ET-EDI
  en verde con port validado + 2.1 con la evidencia y artefacto upstream).
