# DOLAN_theme — Arquitectura implementada y evolutiva

**Principio**: un solo addon instalable `DOLAN_theme` (entry point), capas internas organizadas por paquete, extensiones reversibles, desacoplado de verticales y del futuro módulo LLM/IA. La arquitectura refleja el estado actual en Odoo 20 CE; las propuestas futuras quedan identificadas como tales.

## 1. Repositorio

```
DOLAN_theme/                     ← repo git independiente (ya inicializado)
├── README.md
├── DOLAN_theme/                 ← el addon (id exacto DOLAN_theme, nombre visible "DOLAN Theme")
│   ├── __manifest__.py          ← dependencias mínimas: ["base","web"] (nunca instala apps)
│   ├── __init__.py
│   ├── core/                    ← tokens SCSS/CSS (variables + custom properties), tipografía, iconos
│   ├── navigation/              ← app launcher (topbar + grilla Inicio), breadcrumbs (vistas+assets+JS mínimo)
│   ├── views/                   ← herencias de form/list (scoppeadas)
│   ├── dashboard/               ← home por rol y widgets (acción client propia, datos vía ORM autorizado)
│   ├── preferences/             ← densidad/tema por usuario (ir.default + res.users)
│   ├── compat/                  ← adaptadores por versión (puntos OWL/registries aislados)
│   └── static/{src,scss}/       ← assets registrados en el manifest
├── docs/                        ← research/architecture/compat/risks/inventory/coverage/policy
│   └── prototypes/              ← 3 prototipos HTML navegables
└── tests/                       ← tour tests + checks (Playwright fuera del addon, en QA)
```

## 2. Capas y puntos de extensión

| Paquete | Mecanismo (confirmado en Odoo 20) | Reversibilidad |
|---|---|---|
| `core` tokens | SCSS/CSS custom properties en `web.assets_backend` (scoppeado a `html/body` con prefijo `o_dolan_theme`) + herencia de assets en manifest | alta: desinstalar quita assets |
| `navigation` | extensión QWeb del navbar nativo, `ir.ui.menu.sequence` y acción URL interna `/dolan_apps` para la grilla | media: herencia QWeb reversible |
| `views` | `ir.ui.view` inherit **selectiva** por modelo (solo donde aporte; nunca ocultar validaciones/campos obligatorios) | alta |
| `dashboard` | client action OWL **propia** (checklist Owl3 de `odoo20-compatibility.md`); datos con `orm` → respeta ACL/record rules/multiempresa | alta |
| `preferences` | preferencias visuales por usuario (`res.users` fields no intrusivos o `ir.default`); densidades como clases en `html` | alta |
| `compat` | aislamiento de todo lo que cambió 19→20 (tabla del research); versión `20.0.x.y.z` en manifest | — |

**Regla de parches**: solo herencia de vistas/assets/registries oficiales; sin monkey-patching extenso de componentes OWL (el ejemplo `web_responsive` demostró el costo: pantalla blanca global). Si un componente necesita patch → preferir CSS/slots/overrides de vista; si no hay punto oficial → proponer addon complementario **antes** de crearlo.

## 3. Sistema de diseño (resumen; detalle en Fase 2)

- Tokens: colores semánticos (primary/accent/success/warning/danger + superficies), espaciado (escala 4/8/12/16/24), radios, sombras discretas, tipografía base ≥14px, iconografía (fontawesome del core).
- **Modos**: claro / oscuro / automático (custom properties en `<html>`). El modo del menú Configuración Dolan es el valor inicial del servidor; el toggle directo se recuerda por navegador con `localStorage` (`dolan_theme_mode`). Sin tocar POS.
- **Densidades**: cómoda / normal / compacta (clase de espaciado en listas/formularios; legibilidad intacta).
- Accesibilidad: contraste AA mínimo, foco visible, navegación por teclado, targets táctiles en POS.

## 4. Home por rol (dashboard)

- Widgets configurables por permisos (no por industria): compras pendientes, facturas por cobrar, recepciones, órdenes de producción, etc.
- Datos: solo vía ORM/RPC con el contexto del usuario (ACL + record rules + empresa activa). Distinguir preferencia individual vs configuración administrada (parámetro/`ir.default` de sistema).
- Sin lógica exclusiva de industria; verticales se agregan por extensión documentada.

## 5. Multiempresa, seguridad y límites

- Toda consulta de widgets: `company_ids` del usuario + empresa activa (nunca cross-company por accidente).
- El tema **no** modifica reglas de acceso ni oculta campos por seguridad (los campos sensibles se ocultan con permisos, no con CSS).
- Sin dependencias de servicios externos ni telemetría.

## 6. Estrategia multiversión

- Capas `compat/*` como único punto donde viven supuestos de versión; tokens/componentes no conocen versiones.
- Matriz de soporte en `version-support-policy.md`; ramas: `main` = 20.0 certificada; `19.0` nunca existió para este producto; `21.0` al aparecer (migrar adaptadores + CI).
- CI por versión soportada: lint (py/scss/js), tour tests, instalación/actualización/desinstalación, capturas Playwright de regresión.
- Sin checks de versión frágiles tipo `if version.startswith`: preferir puntos de extensión oficiales; si hace falta feature-detect, documentarlo en `compat`.

## 7. Extensibilidad para terceros

- Registro documentado de: hooks de preferencias (orden de widgets), slots del launcher (favoritos/recientes), grupos de vistas heredables (prefijos `o_dolan_theme_*`), parámetros `ir.config_parameter` (`dolan_theme.*`).
- Addons de terceros pueden agregar widgets al Home mediante un registry propio (`registry.category("dolan_theme.widgets")`) — propuesto; si el patrón registry no resulta viable en implementación, se documenta la alternativa (herencia de vista del Home).

## 8. POS y Website (compatibilidad por diseño)

- `point_of_sale`: assets del tema **excluyen** los bundles de POS; smoke test visual/funcional obligatorio en Fase 5; mejoras de estilo POS solo con pruebas dedicadas.
- `website` + editores visuales: sin estilos globales invasivos; scope `o_dolan_theme` solo en `web` client (backend), no en frontend público salvo decisión explícita aprobada.
