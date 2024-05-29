# -*- coding: utf-8 -*-

from odoo.tools import html_keep_url
from odoo.exceptions import UserError
from odoo import api, fields, _, models
from odoo.tools import config
config['limit_time_real'] = 10000000
import logging

_logger = logging.getLogger(__name__)

class OrderFulfillment(models.Model):
    _name = 'shopify.order.fulfillment'
    _description = 'Shopify Order Fulfillment Details'

    shopify_id = fields.Char('Shopify ID')
    shopify_order_id = fields.Char('Shopify Order Id')
    shopify_order_no = fields.Char('Shopify Order No.')
    location_id = fields.Char('Shopify fulfillment location')
    shopify_service = fields.Char('service')
    shopify_status = fields.Char('Shopify fulfillment Status')
    tracking_company = fields.Char('Tracking company')
    tracking_number = fields.Char('Tracking number')
    tracking_url = fields.Char(string="Tracking url")
    
    is_exported = fields.Boolean('Synced In Shopify', default=False)
    
    so_id = fields.Many2one('sale.order', ondelete='cascade')
    fulfillment_line_id = fields.One2many('shopify.order.fulfillment.line', 'fulfillment_id')
    
class OrderFulfillmentLine(models.Model):
    _name = 'shopify.order.fulfillment.line'
    _description = 'Shopify Order Fulfillment line Details'

    f_line_item_id = fields.Char('Shopify Line ID')
    f_line_item_name = fields.Char('Shopify Line Item Name')
    f_service = fields.Char('Service')
    f_status = fields.Char('Status')
    price = fields.Float('Item price')
    shopify_product_id = fields.Char('Shopify Product ID')
    shopify_variant_id = fields.Char('Shopify variant ID')    
    quantity = fields.Char('Quantity')
    
    fulfillment_id = fields.Many2one('shopify.order.fulfillment', ondelete='cascade')