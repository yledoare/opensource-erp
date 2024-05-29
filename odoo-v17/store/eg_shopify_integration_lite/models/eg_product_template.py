from odoo import models, fields, api


class EgProductTemplate(models.Model):
    _inherit = "eg.product.template"

    def export_product_shopify_server(self):
        self.env["product.template"].export_product_in_shopify()
