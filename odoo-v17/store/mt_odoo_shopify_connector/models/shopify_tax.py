# -*- coding: utf-8 -*-

import shopify
from odoo import fields, models, _
from odoo.exceptions import UserError

class Taxes(models.Model):
    _inherit = 'account.tax'

    shopify_id = fields.Char('shopify Tax ID')
    is_exported = fields.Boolean('Synced In Shopify', default=False)
    is_shopify_tax = fields.Boolean('Is Shopify Tax', default=False)
    
    shopify_instance_id = fields.Many2one('shopify.instance', ondelete='cascade')    