# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    shopify_id = fields.Char('Shopify ID')
    shopify_handle = fields.Char('Shopify Handle')
    shopify_carrier_identifier = fields.Char('Shopify Hash Handle')
    
    is_shopify = fields.Boolean('Synced In Shopify', default=False)
    
    shopify_instance_id = fields.Many2one('shopify.instance', ondelete='cascade')
    
    
    