from odoo import models, fields, api
import json


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    tax_add_by = fields.Selection([("odoo", "By Odoo"), ("shopify", "By Shopify")], string="Add Tax")

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        icpSudo = self.env['ir.config_parameter'].sudo()  # it is given all access
        res.update(
            tax_add_by=icpSudo.get_param('eg_shopify_integration_lite.tax_add_by', default=None),
        )

        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        icpSudo = self.env['ir.config_parameter'].sudo()
        icpSudo.set_param("eg_shopify_integration_lite.tax_add_by", self.tax_add_by)
        return res
