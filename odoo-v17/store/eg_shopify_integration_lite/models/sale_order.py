import logging
from datetime import datetime

import shopify

from odoo import models, fields

_logger = logging.getLogger("==== Sale Order ====")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    eg_account_journal_id = fields.Many2one(comodel_name="eg.account.journal", string="Payment Gateway")

    def import_sale_order_from_shopify(self, instance_id=None, product_create=None, product_image=None, cron=None):
        if cron == "yes":  # New Changes by akash
            instance_ids = self.env["eg.ecom.instance"].search([])
        else:
            instance_ids = [instance_id]
        for instance_id in instance_ids:
            status = "no"
            text = ""
            partial = False
            history_id_list = []
            line_partial_list = []

            shop_connection = self.get_connection_from_shopify(instance_id=instance_id)
            if shop_connection:
                next_page_url = None
                count = 1
                while count > 0:
                    try:
                        if next_page_url:
                            response = shopify.Order.find(from_=next_page_url)
                        elif cron == "yes" and instance_id.spf_last_order_date:
                            response = shopify.Order.find(limit=2,
                                                          created_at_min=instance_id.spf_last_order_date.strftime(
                                                              "%Y-%m-%dT%H:%M:%S"))
                        else:
                            response = shopify.draft_order.DraftOrder.find(limit=2)
                    except Exception as e:
                        # raise Warning("{}".format(e))
                        return {"warning": {"message": (
                            "{}".format(e))}}
                    if response:
                        tax_add_by = instance_id.tax_add_by
                        if cron == "yes":  # TODO : New Changes by akash
                            last_date_order = datetime.strptime(response[0].created_at[0:19], "%Y-%m-%dT%H:%M:%S")
                            instance_id.write({"spf_last_order_date": last_date_order})
                        for order in response:
                            order = order.to_dict()
                            line_partial = False
                            sale_order_id = None
                            status = "no"
                            text = ""
                            if order.get("customer") and order.get("customer").get("default_address"):
                                eg_order_id = self.env["eg.sale.order"].search(
                                    [("inst_order_id", "=", str(order.get("id"))),
                                     ("instance_id", "=", instance_id.id)])
                                if not eg_order_id:  # TODO New Change
                                    order_id = self.search([("name", "=", order.get("name"))])
                                    eg_journal_id = None
                                    if order.get("gateway"):
                                        gateway = order.get("gateway").capitalize()
                                        if gateway:
                                            eg_journal_id = self.find_journal_account_id(gateway=gateway,
                                                                                         instance_id=instance_id)
                                    if order_id:
                                        eg_order_id = self.env["eg.sale.order"].create(
                                            {"odoo_order_id": order_id.id,
                                             "instance_id": instance_id.id,
                                             "eg_account_journal_id": eg_journal_id and eg_journal_id.id or None,
                                             "inst_order_id": str(
                                                 order.get("id")),
                                             "update_required": False})
                                        status = "yes"
                                        sale_order_id = order_id
                                    else:
                                        billing_partner_id = None
                                        shipping_partner_id = None
                                        partner_id = None
                                        if order.get("billing_address"):
                                            billing_partner_id = self.env[
                                                "res.partner"].import_customer_from_shopify(
                                                billing_partner=True, instance_id=instance_id, order=order)
                                        if order.get("shipping_address"):
                                            shipping_partner_id = self.env[
                                                "res.partner"].import_customer_from_shopify(
                                                shipping_partner=True, instance_id=instance_id, order=order)
                                        if billing_partner_id and shipping_partner_id:
                                            partner_id = billing_partner_id.parent_id or billing_partner_id or ""
                                        if partner_id:
                                            create_date = order.get("created_at")
                                            create_date = create_date.replace("T", " ")
                                            create_date = create_date[0:19]
                                            create_date = datetime.strptime(create_date,
                                                                            "%Y-%m-%d %H:%M:%S")
                                            order_dict = {"partner_id": partner_id.id,
                                                          "date_order": create_date,
                                                          "partner_invoice_id": billing_partner_id.id,
                                                          "partner_shipping_id": shipping_partner_id.id,
                                                          "eg_account_journal_id": eg_journal_id and eg_journal_id.id or None}
                                            if instance_id.spf_order_name == "shopify":
                                                order_dict.update({"name": order.get("name")})
                                            order_id = self.create([order_dict])
                                            product_list = []
                                            for line_item in order.get("line_items"):
                                                eg_product_id = self.env["eg.product.product"].search(
                                                    [("inst_product_id", "=", str(line_item.get("variant_id"))),
                                                     ("instance_id", "=", instance_id.id)])
                                                if not eg_product_id:
                                                    if not product_create:
                                                        order_id.unlink()
                                                        order_id = None  # TODO New Change
                                                        sale_order_id = None
                                                        line_partial = True
                                                        line_partial_list.append(line_partial)
                                                        text = "This product {} is not mapping so not create order".format(
                                                            line_item.get("name"))
                                                        _logger.info(
                                                            "This product {} is not mapping so not create order".format(
                                                                 line_item.get("name")))
                                                        break
                                                    else:
                                                        if line_item.get("product_id"):
                                                            product_id = self.env[
                                                                "product.template"].import_product_from_shopify(
                                                                instance_id=instance_id,
                                                                product_image=product_image,
                                                                default_product_id=line_item.get("product_id"))
                                                            eg_product_id = self.env["eg.product.product"].search(
                                                                [("inst_product_id", "=",
                                                                  str(line_item.get("variant_id"))),
                                                                 ("instance_id", "=", instance_id.id)])
                                                if eg_product_id:
                                                    order_line_id = self.env["sale.order.line"].create(
                                                        {"product_id": eg_product_id.odoo_product_id.id,
                                                         "name": line_item.get("name"),
                                                         "product_uom_qty": line_item.get("quantity"),
                                                         "price_unit": line_item.get("price"),
                                                         "order_id": order_id.id, })
                                                    if tax_add_by and tax_add_by == "shopify":
                                                        tax_list = self.find_tax_for_product(line_item=line_item)
                                                        if tax_list:
                                                            order_line_id.write({"tax_id": [(6, 0, tax_list)]})
                                                    status = "yes"
                                                    sale_order_id = order_id
                                                else:
                                                    product_list.append(line_item.get("name"))
                                                    text = "This Sale order is create but this products {} is not" \
                                                           "mapping so not add in sale order line".format \
                                                        (product_list)
                                                    sale_order_id = order_id
                                                    line_partial = True
                                                    line_partial_list.append(line_partial)
                                            if order_id:
                                                eg_order_id = self.env["eg.sale.order"].create(
                                                    {"odoo_order_id": order_id.id,
                                                     "instance_id": instance_id.id,
                                                     "eg_account_journal_id": eg_journal_id and eg_journal_id.id
                                                                              or None,
                                                     "inst_order_id": str(
                                                         order.get("id")),
                                                     "update_required": False})
                                        else:
                                            text = "This sale order {} is not create because customer is not mapping".format(
                                                order.get("name"))
                                            partial = True
                                            status = "no"
                                            _logger.info(
                                                "This sale order {} is not create because customer is not mapping".format(
                                                    order.get("name")))
                                else:
                                    status = "yes"
                                    continue  # TODO New Change
                            else:
                                text = "This Sale order {} is not create because customer is guest".format(
                                    order.get("name"))
                                partial = True
                                status = "no"
                                _logger.info("This Sale order {} is not create because customer is guest")
                            if line_partial:
                                status = "partial"
                            elif not line_partial and status == "yes":
                                text = "This order is created"
                            eg_history_id = self.env["eg.sync.history"].create({"error_message": text,
                                                                                "status": status,
                                                                                "process_on": "order",
                                                                                "process": "a",
                                                                                "instance_id": instance_id.id,
                                                                                "order_id": sale_order_id and sale_order_id.id or None,
                                                                                "child_id": True})
                            history_id_list.append(eg_history_id.id)
                        next_page_url = response.next_page_url
                        if not next_page_url:
                            break
                    else:
                        text = "Not get response from shopify"
                        break
            else:
                text = "Not Connect to store !!!"
            partial_value = True
            if partial or partial_value in line_partial_list:
                text = "Some order was created and some order is not create"
                status = "partial"
            if status == "yes" and not partial and partial_value not in line_partial_list:
                text = "All Order was successfully created"
            if not history_id_list:  # TODO New Change
                status = "yes"
                text = "All order was already mapped"
            eg_history_id = self.env["eg.sync.history"].create({"error_message": text,
                                                                "status": status,
                                                                "process_on": "order",
                                                                "process": "a",
                                                                "instance_id": instance_id.id,
                                                                "parent_id": True,
                                                                "eg_history_ids": [(6, 0, history_id_list)]})

    def get_connection_from_shopify(self, instance_id=None):
        shop_url = "https://{}:{}@{}.myshopify.com/admin/api/{}".format(instance_id.shopify_api_key,
                                                                        instance_id.shopify_password,
                                                                        instance_id.shopify_shop,
                                                                        instance_id.shopify_version)
        try:
            shopify.ShopifyResource.set_site(shop_url)
            connection = True
        except Exception as e:
            _logger.info("{}".format(e))
            connection = False
        return connection

    def find_journal_account_id(self, gateway=None, instance_id=None):
        eg_journal_id = None
        if gateway and instance_id:
            eg_journal_id = self.env["eg.account.journal"].search(
                [("name", "=", gateway), ("instance_id", "=", instance_id.id)])
            if not eg_journal_id:
                odoo_journal_id = self.env["account.journal"].search(
                    [("name", "=", gateway)])
                if not odoo_journal_id:
                    odoo_journal_id = self.env["account.journal"].create({"name": gateway,
                                                                          "type": "bank",
                                                                          "code": gateway[
                                                                                  0:3].upper()})
                if odoo_journal_id:
                    eg_journal_id = self.env["eg.account.journal"].create(
                        {"odoo_account_journal_id": odoo_journal_id.id,
                         "instance_id": instance_id.id})
        return eg_journal_id

    def find_tax_for_product(self, line_item=None):
        tax_list = []
        if line_item:
            for tax_line in line_item.get("tax_lines"):
                rate = tax_line.get("rate") * 100
                name = "{} {}%".format(tax_line.get("title"), int(rate))
                tax_id = self.env["account.tax"].search(
                    [("name", "=", name), ("amount", "=", rate), ("amount_type", "=", "percent"),
                     ("type_tax_use", "=", "sale")], limit=1)
                if not tax_id:
                    tax_group_id = self.env["account.tax.group"].search([("name", "=", tax_line.get("title"))], limit=1)
                    if not tax_group_id:
                        tax_group_id = self.env["account.tax.group"].create({"name": tax_line.get("title")})
                    tax_id = self.env["account.tax"].create({"name": name,
                                                             "amount": rate,
                                                             "amount_type": "percent",
                                                             "type_tax_use": "sale",
                                                             "tax_group_id": tax_group_id.id,
                                                             "description": name
                                                             })
                tax_list.append(tax_id.id)
        return tax_list
