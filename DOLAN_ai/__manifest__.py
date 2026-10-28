{
    'name': 'DOLAN AI',
    'summary': 'Conexion ChatGPT via OAuth directo (device flow estilo opencode/pi), primer proveedor del modulo DOLAN_ai',
    'version': '20.0.1.0.0',
    'category': 'Productivity/AI',
    'author': 'Dolan',
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
    'depends': ['base', 'web', 'mail'],
    'data': ['security/ir.access.csv', 'views/menu.xml'],
    'assets': {
        'web.assets_backend': [
            'DOLAN_ai/static/src/systray/systray_button.xml',
            'DOLAN_ai/static/src/systray/dolan_ai_systray.js',
            'DOLAN_ai/static/src/systray/chat_window.js',
        ],
    },
    'installable': True,
    'application': True,
}
