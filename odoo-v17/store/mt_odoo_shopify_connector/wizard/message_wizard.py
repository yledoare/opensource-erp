# -*- coding: utf-8 -*-

from odoo import models, api, _, fields

class MessageWizard(models.TransientModel):
    _name = 'message.wizard'

    message = fields.Text('Message', required=True)

    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}
    
    def success(self, message):
        message_id = self.env['message.wizard'].create({'message': _(message)})
        return {
            'name': _('Successfull'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('mt_odoo_shopify_connector.message_wizard_form').id,
            'res_model': 'message.wizard',
            'res_id': message_id.id,
            'target': 'new'
        }
        
    def fail(self, message):
        message_id = self.env['message.wizard'].create({'message': _(message)})
        return {
            'name': _('Failed'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('mt_odoo_shopify_connector.message_wizard_fail_form').id,
            'res_model': 'message.wizard',
            'res_id': message_id.id,
            'target': 'new'
        }        