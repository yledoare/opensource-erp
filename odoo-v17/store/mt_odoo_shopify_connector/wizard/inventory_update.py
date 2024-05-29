# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import models, _, api, fields


class ShopifyUpdateInventory(models.Model):
    _name = 'shopify.inventory.update'
    _description = 'Shopify inventory update'

    shopify_instance_id = fields.Many2one('shopify.instance')

    def import_shopify_inventory(self):
        return self.env['product.template'].update_stock(self.shopify_instance_id)

    
    @api.model
    def default_get(self, fields):
        res = super(ShopifyUpdateInventory, self).default_get(fields)
        try:
            instance = self.env['shopify.instance'].search([])[0]
        except Exception as error:
            raise UserError(_("Please create and configure Shopify Instance"))

        if instance:
            res['shopify_instance_id'] = instance.id

        return res
