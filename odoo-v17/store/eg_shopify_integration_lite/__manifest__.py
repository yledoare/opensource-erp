{
    "name": "Odoo Shopify Integration Lite",

    "summary": "Odoo Shopify Integration Lite",

    "category": "Integration",

    "version": "17.0",

    "author": "INKERP",

    "website": "http://www.inkerp.com",

    "depends": ["eg_ecommerce_base", "product"],

    "data": [
        'security/ir.model.access.csv',
        'data/ir_sequence_view.xml',
        'data/action_servers_view.xml',
        'data/ir_cron_view.xml',
        'wizards/export_product_shopify_wizard_view.xml',
        'wizards/import_from_ecom_provider_view.xml',
        'views/res_config_settings_view.xml',
        'views/account_move_view.xml',
        'views/eg_ecom_instance_view.xml',
        'views/sale_order_view.xml',
    ],
    
    'images': ['static/description/banner.png'],
    'license': "OPL-1",
    'installable': True,
    'application': True,
    'auto_install': False,
    'pre_init_hook': 'pre_init_hook',
    'uninstall_hook': "uninstall_hook",
}
