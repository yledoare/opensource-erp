# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import models, api, _, fields
import logging

_logger = logging.getLogger(__name__)
class ShopifyOrderAction(models.TransientModel):
    _name = 'shopify.order.actions.wizard'
    _description = 'Shopify Order Actions'
    
   
    @api.model
    def default_get(self, fields):
     
        res = super(ShopifyOrderAction, self).default_get(fields)      
      
        try:
            instance = self.env['shopify.instance'].search([])[0]
        except Exception as error:
            raise UserError(_("Please create and configure Shopify Instance"))

        if instance:
            res['shopify_instance_id'] = instance.id

        if self.env['shopify.instance']._context.get('shopify_instance_id'):
            res['shopify_instance_id'] = self.env['shopify.instance']._context.get('shopify_instance_id')
       
        selected_ids = self.env['sale.order']._context.get('active_ids', [])
        
        res['order_action_status'] = self._compute_order_action_status(selected_ids)
        
        return res    
    
    

    def _get_selection_normal(self):
        return [('cancel', "Cancel Order"),('refund', "Full Refund Order"),('fulfill', "Fulfill Order"),('info_update', "Order Info Import"),]
        
    def _get_selection_draft(self):
        return [('draft_order', "Create Draft Order"),]
    
    def _get_selection_new_order(self):
        return [('draft_order_invoice', "Send Payment Link"), ('draft_order_info_update', "Update Draft Order Info")]
    
    def _get_selection_info_update(self):
        return [('info_update', "Order Info Import")]
    
    def _get_selection_no_fulfill(self):
        return [('refund', "Full Refund Order"),('fulfill', "Fulfill Order"),('cancel', "Cancel Order"),('info_update', "Order Info Import")]
    
    def _get_selection_payment_complete(self):
        return [('cancel', "Cancel Order"),('info_update', "Order Info Import")]
    
    def _get_selection_fulfill_complete(self):
        return [('refund', "Full Refund Order"),('info_update', "Order Info Import")]
    
    
    shopify_instance_id = fields.Many2one('shopify.instance')
    current_order_id = fields.Char(compute='_compute_current_order_id', store=True, precompute=True)
    order_action_status = fields.Char()
    
    order_actions = fields.Selection(_get_selection_normal, string="Order Actions") 
    order_actions_draft_order = fields.Selection(_get_selection_draft, string="Order Actions") 
    order_actions_new_order = fields.Selection(_get_selection_new_order, string="Order Actions") 
    order_actions_info_update = fields.Selection(_get_selection_info_update, string="Order Actions") 
    order_actions_no_fulfill = fields.Selection(_get_selection_no_fulfill, string="Order Actions") 
    order_actions_payment_complete = fields.Selection(_get_selection_payment_complete, string="Order Actions") 
    order_actions_fulfill_complete = fields.Selection(_get_selection_fulfill_complete, string="Order Actions") 
         
        
        
    @api.depends("shopify_instance_id")
    def _compute_current_order_id(self):
        for rec in self:
            rec.current_order_id = self.env.context.get('order_actions')
            
    def _compute_order_action_status(self, selected_ids):      
       
        order_id = self.env['sale.order'].sudo().search([('id', 'in', selected_ids)])
        # _logger.info('\n\n\n\n  _compute_order_action_status  =  %s\n\n\n\n' % (order_id) )
        if order_id:      
            if not order_id.shopify_id:
                return "draft_order"
            
            if order_id.is_shopify_draft_order:
                return "new_order"

            if order_id.shopify_id and not order_id.is_shopify_draft_order:
                
                if not order_id.shopify_status  and not order_id.shopify_fulfillment_status:
                    return "info_update"    
                              
                if order_id.shopify_fulfillment_status:
                    if order_id.shopify_status in ['pending', 'refunded'] and order_id.shopify_fulfillment_status in ['fulfilled']:
                        return "info_update"    
                    
                if not order_id.shopify_fulfillment_status:   
                    if order_id.shopify_status in ['paid', 'partially_refunded']:
                        return "no_fulfill"  
                    
                if order_id.shopify_status in ['pending', 'refunded']:
                    return "payment_complete"
                
                if order_id.shopify_fulfillment_status in ['fulfilled']:
                    return "fulfill_complete"            
            
        return "default"
                
    
    def shopify_action(self):
        order_actions = ""

        if self.order_actions:
            order_actions = self.order_actions
        if self.order_actions_draft_order:
            order_actions = self.order_actions_draft_order
        if self.order_actions_new_order:
            order_actions = self.order_actions_new_order
        if self.order_actions_info_update:
            order_actions = self.order_actions_info_update
        if self.order_actions_no_fulfill:
            order_actions = self.order_actions_no_fulfill
        if self.order_actions_payment_complete:
            order_actions = self.order_actions_payment_complete
        if self.order_actions_fulfill_complete:
            order_actions = self.order_actions_fulfill_complete
        
        instance_id = self.shopify_instance_id
        if order_actions == "export":
            self.env['sale.order'].shopify_export_order(instance_id)
        if order_actions == "draft_order":
            self.env['sale.order'].shopify_draft_order_create(instance_id)   
        if order_actions == "draft_order_invoice":
            self.env['sale.order'].shopify_draft_order_send_invoice(instance_id)     
        if order_actions == "draft_order_info_update":
            self.env['sale.order'].shopify_draft_orders_update(instance_id)                              
        if order_actions == "cancel":         
            self.env['sale.order'].shopify_order_cancel(instance_id)
        if order_actions == "fulfill":            
            self.env['sale.order'].order_fulfillment_create(instance_id)
        if order_actions == "refund":             
            self.env['sale.order'].order_refund_create(instance_id)
        if order_actions == "info_update":             
            self.env['sale.order'].shopify_force_info_update(instance_id)
                    
        return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                }


