# -*- coding: utf-8 -*-
import logging
from odoo.exceptions import UserError
from odoo import models, api, _, fields

_logger = logging.getLogger(__name__)
class ResPartnerInstance(models.TransientModel):
    _name = 'res.partner.instance.exp'
    _description = 'Customer Export'

    shopify_instance_id = fields.Many2one('shopify.instance')

    def customer_instance_for_exp(self):
        instance_id = self.shopify_instance_id
        self.env['res.partner'].export_customers(instance_id)
        
    @api.model
    def default_get(self, fields):
        res = super(ResPartnerInstance, self).default_get(fields)
        try:
            instance = self.env['shopify.instance'].search([])[0]
        except Exception as error:
            raise UserError(_("Please create and configure Shopify Instance"))

        if instance:
            res['shopify_instance_id'] = instance.id

        if self.env['shopify.instance']._context.get('shopify_instance_id'):
            res['shopify_instance_id'] = self.env['shopify.instance']._context.get('shopify_instance_id')

        return res


class ResPartnerInstanceImp(models.TransientModel):
    _name = 'res.partner.instance.imp'
    _description = 'Customer Import'

    shopify_instance_id = fields.Many2one('shopify.instance')

    def customer_instance_for_imp(self):
        instance_id = self.shopify_instance_id
        self.env['res.partner'].import_customer(instance_id)

        
        current_instance = self.env['shopify.instance'].sudo().search([('id','=',self.shopify_instance_id.id)],limit=1)
        customer_action = current_instance.get_customers()
        customer_action['customer_action'].update({'target': "main",})
        return customer_action['customer_action']
  
          
    @api.model
    def default_get(self, fields):
        res = super(ResPartnerInstanceImp, self).default_get(fields)
        try:
            instance = self.env['shopify.instance'].search([])[0]
        except Exception as error:
            raise UserError(_("\n\n\nPlease create and configure Shopify Instance\n\n"))
        
        if instance:
            res['shopify_instance_id'] = instance.id

        return res

