from odoo import models, fields


class ExportProductShopifyWizard(models.TransientModel):
    _name = "export.product.shopify.wizard"

    instance_id = fields.Many2one(comodel_name="eg.ecom.instance", string="Instance", required=True)
    product_detail = fields.Boolean(string="Details",
                                    help="Import product odoo to middle layer if product is mapped so update either create mapping")

    def export_product_middle_layer(self):
        if self.product_detail:
            self.env["product.template"].export_product_in_middle_layer(instance_id=self.instance_id,
                                                                        product_detail=self.product_detail)
