# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class ShopifyStockInventory(models.Model):
    _name = 'shopify.stock.quant'
    _description = 'Shopify Stock Inventory'

    inventory_item_id = fields.Char('Shopify Inventory Item Id')
    inventory_quantity = fields.Char('Shopify inventory Quantity')
    location_id = fields.Char('Shopify Location ID')
    
    product_id = fields.Many2one('product.product', string='Product Id')
    shopify_instance_id = fields.Many2one('shopify.instance', string="Shopify Instance")    
    
    def inventory_adjustment_operation(self, p_inventory_data):
        if p_inventory_data:
            for p_id, inv_item_id, p_qty, inv_loc in p_inventory_data:
                val = {
                        'product_id': p_id,
                        'inventory_item_id': inv_item_id,
                        'location_id': inv_loc,                         
                        'inventory_quantity': p_qty
                        }
                old_inv = self.env['shopify.stock.quant'].sudo().search(
                [('inventory_item_id', '=', inv_item_id),('product_id', '=', p_id)], limit=1)
                if old_inv:
                    inv_item = old_inv.write(val)
                else:
                    inv_item = self.create(val)
                
                if inv_item:
                    product = self.env['product.product'].sudo().search(
                [('id', '=', p_id)], limit=1)
                    product.write({'qty_available' : float(p_qty)})
                
class ShopifyChangeQuantity(models.TransientModel):
    _inherit = "stock.change.product.qty"

    def change_product_qty(self):
        p_var = self.env['product.product'].sudo().search([('id', '=', self.product_id.id)])
        
        _logger.info("\n\n\n\n new_quantity: %s    qty_available Qty: %s \n\n\n\n" % (self.new_quantity,  p_var.qty_available))
        new_quant = int(p_var.shopify_product_free_qty) + (int(self.new_quantity) - int(p_var.qty_available))
        p_var.update({'shopify_product_free_qty' : new_quant})
        
        return super(ShopifyChangeQuantity,self).change_product_qty()
        