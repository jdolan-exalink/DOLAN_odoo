{
    'name': 'DOLAN Contabilidad',
    'summary': 'Tablero contable, estados financieros propios (XLSX) y accesos a la app Contabilidad',
    'version': '20.0.2.0.0',
    'category': 'Accounting',
    'author': 'Dolan',
    'license': 'LGPL-3',
    'depends': ['account', 'web', 'report_xlsx', 'l10n_ar_fiscal_ws', 'l10n_ar_fiscal_ws_reports', 'partner_statement'],
    'data': [
        'security/ir.access.csv',
        'views/menu.xml',
        'views/financial_report.xml',
        'views/journal_audit.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
