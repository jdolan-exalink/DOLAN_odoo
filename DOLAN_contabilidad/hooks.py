import json

_NOMBRES = json.loads("""[
        [
                "DOLAN_contabilidad.menu_reports_contact",
                "Contact Reports",
                "Reportes del contacto"
        ],
        [
                "DOLAN_contabilidad.menu_statement_activity",
                "Customer Account Statement",
                "Estado de la cuenta del cliente"
        ],
        [
                "DOLAN_contabilidad.menu_statement_outstanding",
                "Customer Outstanding Statement",
                "Estado de los pendientes de la cuenta"
        ],
        [
                "DOLAN_contabilidad.menu_statement_detailed",
                "Detailed Partner Activity",
                "Actividad detallada del contacto"
        ],
        [
                "DOLAN_contabilidad.menu_arca_recover",
                "Query invoice in ARCA",
                "Consultar factura en ARCA"
        ],
        [
                "l10n_ar_fiscal_ws_reports.menu_account_sale_vat_ledger",
                "Sales VAT Ledger",
                "Libro de IVA - Ventas"
        ],
        [
                "l10n_ar_fiscal_ws_reports.menu_account_purchase_vat_ledger",
                "Purchases VAT Ledger",
                "Libro de IVA - Compras"
        ],
        [
                "l10n_ar_fiscal_ws_reports.menu_current_account",
                "VAT Analysis",
                "Análisis de IVA"
        ],
        [
                "DOLAN_contabilidad.menu_financial_statements",
                "Financial Statements",
                "Estados financieros"
        ],
        [
                "DOLAN_contabilidad.menu_financial_balance",
                "Balance Sheet",
                "Balance general"
        ],
        [
                "DOLAN_contabilidad.menu_financial_results",
                "Profit and Loss",
                "Estado de resultados"
        ],
        [
                "DOLAN_contabilidad.menu_financial_cash",
                "Cash Flow",
                "Flujo de efectivo"
        ],
        [
                "DOLAN_contabilidad.menu_dolan_journal_audit",
                "Journal Audit",
                "Auditoría de diario"
        ]
]""")


def post_init_hook(env):
    """Nombres bilingües de los menús DOLAN.

    Se hacen en hook y no en XML porque en una base nueva todavia no hay
    idiomas activos al cargar datos y el eval del jsonb falla
    ("Some of the languages are not active").
    """
    for xid, en, es in _NOMBRES:
        env.cr.execute(
            """
            UPDATE ir_ui_menu
               SET name = jsonb_set(name, '{en_US}', %s::jsonb, true)
             WHERE id = (SELECT res_id FROM ir_model_data
                          WHERE module || '.' || name = %s)
            """,
            [json.dumps(en, ensure_ascii=False), xid],
        )
        env.cr.execute(
            """
            UPDATE ir_ui_menu
               SET name = jsonb_set(name, '{es_AR}', %s::jsonb, true)
             WHERE id = (SELECT res_id FROM ir_model_data
                          WHERE module || '.' || name = %s)
            """,
            [json.dumps(es, ensure_ascii=False), xid],
        )
    # la app contable pasa a llamarse Contabilidad en todos los idiomas
    env.cr.execute("""
        UPDATE ir_ui_menu
           SET name = jsonb_set(jsonb_set(name, '{en_US}', '"Contabilidad"', true),
                                '{es_AR}', '"Contabilidad"', true)
         WHERE id = (SELECT res_id FROM ir_model_data
                      WHERE module = 'account' AND name = 'menu_finance')
    """)
