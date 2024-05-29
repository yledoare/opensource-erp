# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import models, _, api, fields


class ShopifyLocationsImport(models.Model):
    _name = 'shopify.locations.import'
    _description = 'Shopify Locations Import'

    shopify_instance_id = fields.Many2one('shopify.instance')

    def import_shopify_locations(self):
        self.env['shopify.location'].import_locations(self.shopify_instance_id)
        return self.env.ref("mt_odoo_shopify_connector.action_shopify_location_view").read()[0]

    def view_shopify_locations(self):
        return self.env.ref("mt_odoo_shopify_connector.action_shopify_location_view").read()[0]
    
    @api.model
    def default_get(self, fields):
        res = super(ShopifyLocationsImport, self).default_get(fields)
        try:
            instance = self.env['shopify.instance'].search([])[0]
        except Exception as error:
            raise UserError(_("Please create and configure Shopify Instance"))

        if instance:
            res['shopify_instance_id'] = instance.id

        return res
