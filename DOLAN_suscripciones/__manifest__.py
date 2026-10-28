{
    'name': 'DOLAN Suscripciones',
    'summary': 'Planes y suscripciones recurrentes: cron diario que genera facturas en borrador',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'author': 'Dolan',
    'license': 'LGPL-3',
    'depends': ['account', 'product'],
    'data': ['security/ir.access.csv', 'views/views.xml', 'data/cron.xml'],
    'installable': True,
    'application': True,
}
