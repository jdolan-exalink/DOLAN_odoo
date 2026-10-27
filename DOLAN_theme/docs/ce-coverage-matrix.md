# Matriz de cobertura CE — DOLAN_theme

Estado: **esqueleto inicial** generado en Fase 0 desde el inventario real (34 apps CE + familia event).
Leyenda de estado: `NE` no evaluado · `C` compatible · `RA` requiere adaptación · `FX` corregido y validado · `—` no aplica (sin esa vista).

| Módulo | form | list | kanban | search | pivot/graph | calendar | chatter | Posición actual |
|---|---|---|---|---|---|---|---|---|
| account | NE | NE | — | NE | NE | — | NE | prioridad MVP (lotes 1) |
| contacts | NE | NE | NE | NE | — | — | NE | prioridad MVP (lote 1) |
| purchase | NE | NE | NE | NE | NE | — | NE | prioridad MVP (lote 1) |
| sale_management | NE | NE | NE | NE | NE | — | NE | prioridad MVP (lote 1) |
| stock | NE | NE | NE | NE | — | — | NE | prioridad MVP (lote 2) |
| point_of_sale | NE | NE | NE | NE | — | — | NE | aislado (R5) — smoke test obligatorio |
| crm | NE | NE | NE | NE | NE | — | NE | lote 3 |
| mrp | NE | NE | NE | NE | — | — | NE | lote 3 |
| project / project_todo | NE | NE | NE | NE | — | — | NE | lote 3 |
| hr familia (6 apps) | NE | NE | NE | NE | — | — | NE | lote 4 |
| website familia (5) + event* | NE | NE | NE | NE | — | — | — | lote 5 (scope backend; front: decisión aparte) |
| restantes (calendar, survey, mail, im_livechat, mass_mailing*, maintenance, repair, fleet, lunch, data_recycle, marketing_card, pos_restaurant…) | NE | NE | NE | NE | NE | NE | NE | lotes 5–6 |

Reglas de la matriz:
1. Una fila por módulo oficial; columnas por familia de vista que el módulo realmente usa (verificado por XML del propio módulo, no por supuesto).
2. Cada `C/FX` exige: prueba en navegador (Playwright o manual con captura), en claro y oscuro, y al menos un rol no-admin.
3. Cubrir el lote = poder declarar ese lote; **la cobertura total solo se declara con todas las filas fuera de `NE`**.
4. POS: además de la matriz, suite táctil dedicada.
5. Evidencia: capturas en `docs/evidence/<fecha>/<modulo>/` (se creará en Fase 5).
