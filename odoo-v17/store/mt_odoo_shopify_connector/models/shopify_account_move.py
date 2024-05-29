# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError
import shopify
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    shopify_id = fields.Char('Shopify ID')
    shopify_refund_id = fields.Char('Shopify Refund ID')
    
    shopify_instance_id = fields.Many2one('shopify.instance', ondelete='cascade')
    is_exported = fields.Boolean('Synced In Shopify', default=False)
    is_refund = fields.Boolean('Is refunded', default=False)
    
    def init_shopify_session(self, instance_id):
        try:
            session = shopify.Session(instance_id.shop_url, instance_id.api_version, instance_id.admin_api_key)
            return session
        except Exception as error:
            raise UserError(_("Please check your connection and try again"))   
            
    def action_fail_refund_button(self, message):
        return self.env['message.wizard'].fail(message)
    
    def action_generate_refund_account_move(self):
        action = self.env.ref("mt_odoo_shopify_connector.action_wizard_generate_refund").read()[0]
        action.update({
            'context': "{'shopify_instance_id': " + str(self.shopify_instance_id.id) + "}",
        })        
        return action    
    
    def credit_invoice_refund_create(self, instance_id):
        
        selected_ids = self.env.context.get('active_ids', [])
        order_ids = self.sudo().search([('id', 'in', selected_ids)])

        if not order_ids:
            raise UserError(_("Please select Orders!!!"))
        
        for order in order_ids: 
            self.shopify_refund(instance_id, order)
            
    def shopify_refund(self, instance_id, order):
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
        
        data = {}       
        refund = shopify.Refund()     

        data['shipping'] = { "full_refund": True }
        data['refund_line_items'] = []
        so_order = self.env['sale.order'].sudo().search([('name', '=', order.invoice_origin)])
        
        if not so_order.shopify_id:
            so_order = self.env['sale.order'].sudo().search([('invoice_ids', 'in', [order.id])])

        data.update( {'order_id' : so_order.shopify_id,
                'notify' : False, 
                'note' : "refund from odoo",
            })
        
        so_lines = self.env['sale.order.line'].sudo().search([('order_id', '=', so_order.id)])
        shipping_refund = False
        
        for line in so_lines:
            for id in order.invoice_line_ids:
                if line.product_id.id ==  id.product_id.id and id.quantity !=0 and not line.is_delivery:
                    line_items = {
                        "line_item_id": line.shopify_so_line_id,
                        "quantity": int(id.quantity),
                        "restock_type": "no_restock",
                        "location_id": None
                    }
                    
                    fo_line = self.env['shopify.order.fulfillment.line'].sudo().search([('f_line_item_id', '=', line.shopify_so_line_id)], limit=1)
                    if fo_line:
                        if fo_line.fulfillment_id.location_id:
                            line_items['restock_type'] = "return"
                            line_items['location_id'] = fo_line.fulfillment_id.location_id
                            
                    data['refund_line_items'].append(line_items)
                    
                if line.product_id.id ==  id.product_id.id and id.quantity !=0 and line.is_delivery:
                    shipping_refund = True
            
        if not shipping_refund:
            data['shipping'].update({'full_refund': False, "amount": float("0.00") })
            
        try:
            refund_data = refund.calculate(order_id = so_order.shopify_id, shipping = data['shipping'], refund_line_items = data['refund_line_items'])      
                    
            refund = shopify.Refund({'order_id' : so_order.shopify_id})   
            
            data['transactions'] = []
            if refund_data.attributes['transactions']:
                for tran in refund_data.attributes['transactions']:
                    tran.attributes['kind'] = "refund"
                    data['transactions'].append(tran.attributes)
            
            d_ref = refund.create(data)
            _logger.info('\n\n\n\n  shopify_refund result   =  %s \n\n\n\n' % (d_ref) )    
            
            order.update( {'shopify_refund_id' : d_ref.id,
                        'shopify_id' : d_ref.id,
                        'is_refund' : True,})
        
        except Exception as error:
            _logger.info('\n\n\n\n  Error   =  %s \n\n\n\n' % (error.response.__dict__) )
            raise UserError(_(error.response.body))
        
