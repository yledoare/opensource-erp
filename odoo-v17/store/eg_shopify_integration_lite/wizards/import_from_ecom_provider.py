from odoo import models, fields
import ssl

ssl._create_default_https_context = ssl._create_unverified_context


class ImportFromEComProvider(models.TransientModel):
    _inherit = "import.from.ecom.provider"

    spf_product = fields.Boolean(string="Product", help="Import Product from shopify to odoo and middle layer")
    spf_product_export = fields.Boolean(string="Product", help="Export product middle layer to shopify")
    spf_stock_from_date = fields.Datetime(string="From Date",
                                          help="Stcok update if any changes in stock after this date")
    spf_import_customer = fields.Boolean(string="Customer", help="Import Customer from shopify to odoo")
    spf_import_sale_order = fields.Boolean(string="Sale Order", help="Import Sale Order from shopify to odoo")
    spf_product_create_default_import = fields.Boolean(string="Default Product Create",
                                                       help="When field is true so when import sale order and product is not in odoo so check true so create product either product is not create and sale order is delete")

    def import_from_ecom_provider(self):
        if not self.ecom_instance_id:
            # raise Warning("Please select the Instance")
            return {"warning": {"message": "Please select the Instance"}}
        if not self.ecom_instance_id.provider == "eg_shopify":
            return super(ImportFromEComProvider, self).import_from_ecom_provider()
        if self.spf_product:
            self.env["product.template"].import_product_from_shopify(self.ecom_instance_id)
        if self.spf_product_export:
            self.env["product.template"].export_product_in_shopify(instance_id=self.ecom_instance_id)
        if self.spf_import_customer:
            self.env["res.partner"].import_customer_from_shopify(instance_id=self.ecom_instance_id)
        if self.spf_import_sale_order:
            self.env["sale.order"].import_sale_order_from_shopify(instance_id=self.ecom_instance_id,
                                                                  product_create=self.spf_product_create_default_import)  # Add Pro Version product_image=self.spf_product_image_sale
