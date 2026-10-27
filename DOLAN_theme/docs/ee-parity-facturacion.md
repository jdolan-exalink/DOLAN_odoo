# EE Demo vs CE + DOLAN_theme — Paridad en Facturación

**Fuente**: capturas de la demo Enterprise autorizada (exalink.odoo.com) en
`docs/evidence/ee-demo/` (00-home, 01-dashboard-facturacion, 02-lista-facturas,
03-formulario). **Solo patrones UX observados**: ningún código, template ni
asset OPL-1 fue extraído (política del mandato). Método complementario:
Playwright propio (la suite REA quedó para binarios/páginas WebMCP — ver
`research.md` §6).

## 1. Panel EE de Facturación (01-dashboard) → qué hay y estado en CE

| Elemento EE | Qué hace | CE + DOLAN_theme | Estado |
|---|---|---|---|
| Tira de KPIs (Facturas, Gastos, Efectivo, **Por cobrar**, **Por pagar**) con montos y paginador 1-5/5 | resumen operativo al entrar | Nuestro Tablero KPI: facturas, compras por pagar, **por cobrar**, NC, remitos, recepciones (montos AR, vencidas) | ✅ replicado (falta **Efectivo** = saldo bancario/efectivo y **Gastos** = hr_expense, ambos CE) → ver plan P1 |
| Panel "Ventas Preimpreso" (configurar datos + **activar facturación electrónica**) | onboarding AR | Nuestra config ARCA ya completada (certs, WSAA, PV) — sin onboarding porque la config es por fuera | ✅ funcional (diferente UI, misma meta) |
| Panel "Compras": **escaneo con IA** de facturas (arrastrar y soltar) | EE + IAP OCR | CE no tiene OCR; alternativa CE: import manual/CSV + nuestra migración ya probada | 🔴 EE-only (IAP) — no replicar; cubrir con flujo de carga manual (ver P3) |
| Panel "Banco": **conexión a 26.000 bancos** (agregación) | EE + IAP | CE: conciliación bancaria manual / import extractos (core `account`) | 🔴 EE-only (servicio externo) — documentar |
| **Cheques de Terceros** (+ Rechazados) con gráficos | EE (suite AR) | CE no lo trae; en Dolibarr tampoco se usaba (0 cheques) | 🟠 Decisión: fuera del MVP; si operan con cheques → módulo propio (ver plan P3) |
| Onboarding "diseño de tu factura" | EE designer | CE: plantillas QWeb heredables | 🟡 futuro (baja prioridad) |

## 2. Lista EE de facturas (02) → paridad de columnas

| Columna/UX EE | CE + DOLAN_theme |
|---|---|
| Número / Cliente / Fecha factura / Vencimiento | ✅ nativo |
| **Estado como badges** (Borrador, Enviado, Pagado, Parcial, Cancelado, Bloqueado...) | ✅ **ya agregado por DOLAN_theme** (herencia `status_in_payment` widget badge — 206 badges verificados) |
| Impuestos no incluidos / Total / Cantidad por pagar | ✅ nativo (moneda local) |
| Último recobro (última conciliación) | 🟡 columna EE; CE muestra conciliación por apuntes — posible columna custom futura |
| Conmutadores de vista (lista/pivot/gráfico/calendario) | ✅ nativo CE |
| Nuevo / Subir (subir factura EE) | ⚠️ "Subir" = scan EE → en CE: import (`base_import`) |
| Filtro guardado "Facturas o Recibos" | ✅ filtros guardados nativos |

## 3. Formulario EE de factura (03) → paridad

| Elemento EE | CE + DOLAN_theme |
|---|---|
| Statusbar Borrador→Registrado + **Confirmar** primario | ✅ nativo; estilo primario DOLAN ya aplicado (views.scss) |
| Diario, **Tipo de Documento**, **Número de Documento**, **Resultado** (latam/fiscales) | ✅ **nativo CE con l10n_ar** (migración: los 189 usaron exactamente esos campos; herencia AR del core) |
| Alerta "encabezados y pies… diario preimpreso vs electrónico" | ✅ nativa (l10n_ar) |
| Líneas: secciones, notas, catálogo, toggle Impuestos excl/incl | ✅ nativo CE (sections/notes = `account` lines; catálogo = product catalog CE) |
| Subtotal/Total/**Cantidad por pagar** | ✅ nativo |
| Chatter + Actividad | ✅ nativo (estilo ya refinado por el tema) |
| Botón "Apuntes contables" | ✅ nativo |
| Adjuntos/nube + impresión | ✅ nativo |

**Conclusión de forma**: el formulario EE es en esencia el mismo formulario latam de CE (los campos AR son del core `l10n_ar`) — la capa EE aporta onboarding/IA/bancos. Nuestro estilo ya aplica.

## 4. Home EE (00) → home CE

EE = grid a pantalla completa de apps. Nuestra adopción CE = rail persistente con íconos + home KPI (decidido y aprobado en la Propuesta 1). Diferencia documentada: EE oculta el resto del UI al home; nosotros mantenemos rail+chips (contexto siempre visible).

## 5. Brechas de negocio (funciones, no UI)

| Función | Estado |
|---|---|
| Facturación electrónica ARCA con CAE | ✅ **más allá de EE**: certs propios + WSAA directo (ya funcionando; EE usa infraestructura Odoo/IAP) |
| Compras con "IA que escanea" | 🔴 requiere IAP/EE o integración externa (decisión de producto) |
| Conciliación bancaria automática (26k bancos) | 🔴 EE/IAP — CE: conciliación manual (flujos CE listos) |
| Cheques de terceros | ✅ **cerrado por datos**: `llv_arca_check` en Dolibarr = 0 filas (origen jamás usó cheques) → fuera de alcance hasta que entre en operación; si entra, módulo propio |
| Sincronización "sistema de facturación anterior" | 🔴 EE — irrelevante (ya migramos) |

## 6. Plan propuesto (para aprobación)

- **P1 (UI/paridad)** ✅ `dolan_dash`: KPIs **Efectivo** + **Gastos** (8 widgets, orden EE) — verificado en browser (L16).
- **P2 (lista)** ✅ columna **Último recobro**: `dolan_last_reconcile` compute sobre pagos/conciliaciones en `dolan_dash` + columna `optional="show"` en `account.view_move_tree` (L16, verificado: 4 facturas pagadas con fecha, vista la contiene).
- **P3 (operación)** ✅ plantilla `migration/compras_plantilla.csv` (14 rutas canónicas) + flujo documentado en `migration/README.md` — dry-run SIN ERRORES, import real 6→7 `ids:[754]`, rollback restauró 6 (sin persistir) — L17.
- **P4 (decisión)** ✅ cerrado por datos (ver §5): 0 cheques en origen → módulo propio solo si entra en operación.
- **IA (OCR/asistente)**: diseño del módulo futuro **`dolan_ai`** en [`dolan-ai-design.md`](dolan-ai-design.md) (OAuth ChatGPT/Claude + Ollama local) — pendiente de decisión de proveedor/presupuesto.
- **Fuera de alcance (EE-only)**: OCR con IA, agregación bancaria — se documentan como brecha, se implementarían solo con proveedor externo aprobado.
- **QA**: Playwright suite por lote (capturas + regresiones) al estilo de lo ya hecho.
