# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import config
config['limit_time_real'] = 1000000

class ProductCategory(models.Model):
    _inherit = "product.category"

    @api.model
    def default_get(self, fields):
        res = super(ProductCategory, self).default_get(fields)
        if self.env['shopify.instance']._context.get('shopify_instance_id'):
            res['shopify_instance_id'] = self.env['shopify.instance']._context.get('shopify_instance_id')
            res['is_shopify'] = True
        return res
    
    is_shopify = fields.Boolean(string='Is Shopify?')
    
    shopify_instance_id = fields.Many2one('shopify.instance', ondelete='cascade')    