# -*- coding: utf-8 -*-
{
    'name': "cloudalia_module_misc",

    'summary': """
        Modulo Cloudalia.""",

    'description': """Cloudalia Educación odoo module.
    """,

    'author': "Cloudalia Educacion",

    'website': "http://www.cloudaliaeducacion.com",

    'category': 'Technical Settings',

    'version': '11.0.0.6',

    'depends': ['base', 'stock', 'cloudedu_mods', 'auth_signup', 'website', 'account', 'mail'],

    'data': [
        'views/auth_signup_views.xml',
        'views/auth_signup_assets.xml',
        'views/res_partner_views.xml',
        'views/account_invoice_views.xml',
        'views/account.xml',
        'views/stock_views.xml',
        'views/mrp_repair_views.xml',
        'views/mail_views.xml'
    ],
    'qweb': [
        'static/src/xml/account_payment.xml',
    ],
    'installable': True,
    'auto_install': True,
}