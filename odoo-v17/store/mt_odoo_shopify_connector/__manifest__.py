# -*- coding: utf-8 -*-
# ############################################################################
#
#     Metclouds Technologies Pvt Ltd
#
#     Copyright (C) 2022-TODAY Metclouds Technologies(<https://metclouds.com>)
#     Author: Metclouds Technologies(<https://metclouds.com>)
#
#     You can modify it under the terms of the GNU LESSER
#     GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#     You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#     (LGPL v3) along with this program.
#     If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################

{
    'name': 'Odoo Shopify Connector',
    'summary': 'Odoo Shopify Connector',
    'version': '1.0.0',
    'sequence': 6,
    'description': """Odoo Shopify Connector""",    
    'author': 'Metclouds Technologies Pvt Ltd',
    'category': 'Sales',
    'maintainer': 'Metclouds Technologies Pvt Ltd',
    'website': 'https://www.metclouds.com',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'sale_management', 'purchase', 'stock', 'contacts', 'delivery', 'hr_expense'],
    'external_dependencies': {
        'python': ['ShopifyAPI'],
    },
    'data': [ 
        'security/ir.model.access.csv',
        'wizard/sale_order_instance.xml',        
        'wizard/customer_import.xml',        
        'wizard/product_instance.xml',        
        'wizard/product_inventory_update.xml',        
        'wizard/locations_import.xml',        
        'wizard/inventory_update.xml',        
        'wizard/generate_invoice.xml',   
        'wizard/generate_refund.xml',   
        'wizard/shopify_order_actions.xml',   
        'wizard/message_wizard.xml',                     
        'views/shopify_product.xml',
        'views/shopify_images.xml',
        'views/shopify_instance.xml',
        'views/shopify_sale_order.xml',
        'views/shopify_customer.xml',
        'views/shopify_tax.xml',
        'views/shopify_account_move.xml',
        'views/shopify_product_category.xml',
        'views/shopify_locations.xml',
        'views/menu.xml',
        'views/cron.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'assets': {
        'web.assets_backend': [
            'mt_odoo_shopify_connector/static/src/scss/shopify_graph_widget.scss',
            'mt_odoo_shopify_connector/static/src/**/*.js',
            'mt_odoo_shopify_connector/static/src/**/*.xml',             
        ],
    },    
}
