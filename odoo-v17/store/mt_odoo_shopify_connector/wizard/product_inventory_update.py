# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import models, api, _, fields


class ShopifyInventoryInstanceImp(models.Model):
    _name = 'shopify.inventory.instance.imp'
    _description = 'Inventory Import Instance'

    shopify_instance_id = fields.Many2one('shopify.instance')

    def import_shopify_inventory(self):
        self.env['product.template'].import_inventory(self.shopify_instance_id)

    @api.model
    def default_get(self, fields):
        res = super(ShopifyInventoryInstanceImp, self).default_get(fields)
        try:
            instance = self.env['shopify.instance'].search([])[0]
        except Exception as error:
            raise UserError(_("Please create and configure Shopify Instance"))

        if instance:
            res['shopify_instance_id'] = instance.id

        return res
