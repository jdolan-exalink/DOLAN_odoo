{
    'name': 'DOLAN Contabilidad',
    'summary': 'Tablero contable, estados financieros propios (XLSX) y accesos a la app Contabilidad',
    'version': '20.0.2.0.0',
    'category': 'Accounting',
    'author': 'Dolan',
    'license': 'LGPL-3',
    'depends': ['account', 'web', 'report_xlsx'],
    'data': [
        'security/ir.access.csv',
        'views/menu.xml',
        'views/financial_report.xml',
    ],
    'installable': True,
    'application': False,
}
