{
    'name': 'DOLAN WhatsApp (WAHA)',
    'summary': 'Enviar y recibir WhatsApp por WAHA: log, envio desde contacto y webhook.',
    'version': '20.0.1.0.0',
    'category': 'Social Network',
    'author': 'Dolan',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.access.csv',
        'views/whatsapp_message.xml',
        'views/res_partner.xml',
    ],
    'installable': True,
    'application': False,
}
