from odoo import models, fields, api
from requests import request
import json
import base64
import logging
import shopify

_logger = logging.getLogger("==== CUSTOMER ====")


class ResPartner(models.Model):
    _inherit = "res.partner"

    def import_customer_from_shopify(self, instance_id=None, shipping_partner=None, billing_partner=None, order=None):
        status = "no"
        text = ""
        partial = False
        history_id_list = []
        if instance_id:
            if not shipping_partner and not billing_partner:
                shop_connection = self.get_connection_from_shopify(instance_id=instance_id)
                if shop_connection:
                    next_page_url = None
                    count = 1
                    while count > 0:
                        try:
                            if next_page_url:
                                response = shopify.Customer.find(from_=next_page_url)
                            else:
                                response = shopify.Customer.find(limit=250)
                        except Exception as e:
                            # raise Warning("{}".format(e))
                            return {"warning": {"message": (
                                "{}".format(e))}}
                        if response:
                            for customer in response:
                                customer = customer.to_dict()
                                res_partner_id = None
                                if customer.get("addresses"):
                                    partner_id = self.create_partner_at_import_from_shopify(customer=customer,
                                                                                            instance_id=instance_id)
                                    if partner_id != "Customer Is Mapped":
                                        status = "yes"
                                        text = "This Customer was created"
                                        res_partner_id = partner_id
                                    elif partner_id == "Customer Is Mapped":
                                        eg_partner_id = self.env["eg.res.partner"].search(
                                            [("inst_partner_id", "=", str(customer.get("id"))),
                                             ("instance_id", "=", instance_id.id)])
                                        status = "yes"
                                        text = "This Customer is already mapped"
                                        res_partner_id = eg_partner_id.odoo_partner_id

                                else:
                                    text = "This Customer {} {} is not create because this is guest customer".format(
                                        customer.get("first_name"), customer.get("last_name"))
                                    partial = True
                                    status = "no"
                                eg_history_id = self.env["eg.sync.history"].create({"error_message": text,
                                                                                    "status": status,
                                                                                    "process_on": "customer",
                                                                                    "process": "a",
                                                                                    "instance_id": instance_id.id,
                                                                                    "partner_id": res_partner_id and res_partner_id.id or None,
                                                                                    "child_id": True})
                                history_id_list.append(eg_history_id.id)
                            next_page_url = response.next_page_url
                            if not next_page_url:
                                break

                        else:
                            text = "Not get response from shopify"

                    if partial:
                        status = "partial"
                        text = "Some customer was created and some customer is not create"
                    if status == "yes" and not partial:
                        text = "All customer was successfully created"
                    eg_history_id = self.env["eg.sync.history"].create({"error_message": text,
                                                                        "status": status,
                                                                        "process_on": "customer",
                                                                        "process": "a",
                                                                        "instance_id": instance_id and instance_id.id or None,
                                                                        "parent_id": True,
                                                                        "eg_history_ids": [(6, 0, history_id_list)]})
            if billing_partner:
                billing_partner_id = self.create_partner_at_import_from_shopify(billing_partner=billing_partner,
                                                                                shipping_partner=shipping_partner,
                                                                                instance_id=instance_id, order=order)
                return billing_partner_id
            if shipping_partner:
                shipping_partner_id = self.create_partner_at_import_from_shopify(billing_partner=billing_partner,
                                                                                 shipping_partner=shipping_partner,
                                                                                 instance_id=instance_id, order=order)
                return shipping_partner_id

    def create_partner_at_import_from_shopify(self, customer=None, instance_id=None, shipping_partner=None,
                                              billing_partner=None, order=None):
        create_partner = "Customer Is Mapped"
        if billing_partner or shipping_partner:
            customer = order.get("customer")
        eg_partner_id = self.env["eg.res.partner"].search(
            [("inst_partner_id", "=", str(customer.get("id"))), ("instance_id", "=", instance_id.id)])
        default_address = customer.get("default_address")
        if not eg_partner_id:
            partner_id = self.search([("email", "=", customer.get("email"))])
            if not partner_id:
                name = "{} {}".format(customer.get("first_name"),
                                      customer.get("last_name"))
                country_id = self.env["res.country"].search(
                    [("code", "=", default_address.get("country_code"))])
                if not country_id:
                    country_id = self.env["res.country"].create(
                        {"name": default_address.get("country_name"),
                         "code": default_address.get("country_code")})
                state_id = self.env["res.country.state"].search(
                    [("code", "=", default_address.get("province_code")), ("country_id", "=", country_id.id)])
                if not state_id:
                    state_id = self.env["res.country.state"].create(
                        {"name": default_address.get("province"),
                         "code": default_address.get("province_code"),
                         "country_id": country_id.id})
                partner_id = self.create([{"name": name,
                                           "street": default_address.get("address1") or "",
                                           "street2": default_address.get("address2") or "",
                                           "city": default_address.get("city") or "",
                                           "zip": default_address.get("zip") or "",
                                           "country_id": country_id and country_id.id or None,
                                           "phone": customer.get("phone") or "",
                                           "email": customer.get("email"),
                                           "company_type": "person",
                                           "state_id": state_id and state_id.id or None
                                           }])
                eg_partner_id = self.env["eg.res.partner"].create({"odoo_partner_id": partner_id.id,
                                                                   "instance_id": instance_id.id,
                                                                   "inst_partner_id": str(
                                                                       customer.get("id")),
                                                                   "update_required": False})

            else:
                partner_id = self.verify_default_address_import_customer_shopify(partner_id=partner_id,
                                                                                 default_address=default_address,
                                                                                 eg_partner_id=False,
                                                                                 instance_id=instance_id,
                                                                                 customer=customer)

        else:
            partner_id = eg_partner_id.odoo_partner_id
            partner_id = self.verify_default_address_import_customer_shopify(partner_id=partner_id,
                                                                             default_address=default_address,
                                                                             eg_partner_id=True,
                                                                             instance_id=instance_id,
                                                                             customer=customer)
        if not billing_partner and not shipping_partner:
            return partner_id
        if billing_partner:
            default_address = order.get("billing_address")
            partner_id = partner_id.parent_id or partner_id
            billing_partner_id = self.verify_default_address_import_customer_shopify(partner_id=partner_id,
                                                                                     default_address=default_address,
                                                                                     eg_partner_id=True,
                                                                                     instance_id=instance_id,
                                                                                     customer=customer)
            return billing_partner_id
        if shipping_partner:
            default_address = order.get("shipping_address")
            partner_id = partner_id.parent_id or partner_id
            shipping_partner_id = self.verify_default_address_import_customer_shopify(partner_id=partner_id,
                                                                                      default_address=default_address,
                                                                                      eg_partner_id=True,
                                                                                      instance_id=instance_id,
                                                                                      customer=customer)
            return shipping_partner_id
        if eg_partner_id:
            return create_partner

    def verify_default_address_import_customer_shopify(self, partner_id=None, default_address=None, eg_partner_id=None,
                                                       instance_id=None, customer=None):
        if partner_id and default_address:
            partner_information = {"name": partner_id.name or "",
                                   "phone": partner_id.phone or "",
                                   "street1": partner_id.street or "",
                                   "street2": partner_id.street2 or "",
                                   "city": partner_id.city or "",
                                   "zip": partner_id.zip or "",
                                   "country_id": partner_id.country_id and partner_id.country_id.code or "",
                                   "state_id": partner_id.state_id and partner_id.state_id.code or ""}
            eg_partner_information = {"name": default_address.get("name") or "",
                                      "phone": default_address.get("phone") or "",
                                      "street1": default_address.get("address1") or "",
                                      "street2": default_address.get("address2") or "",
                                      "city": default_address.get("city") or "",
                                      "zip": default_address.get("zip") or "",
                                      "country_id": default_address.get("country_code") or "",
                                      "state_id": default_address.get("province_code") or ""}
            if not partner_information == eg_partner_information:
                create_child = True
                if partner_id.child_ids:
                    for child_id in partner_id.child_ids:
                        partner_information = {"name": child_id.name or "",
                                               "phone": child_id.phone or "",
                                               "street1": child_id.street or "",
                                               "street2": child_id.street2 or "",
                                               "city": child_id.city or "",
                                               "zip": child_id.zip or "",
                                               "country_id": child_id.country_id and child_id.country_id.code or "",
                                               "state_id": child_id.state_id and child_id.state_id.code or ""}
                        if partner_information == eg_partner_information:
                            if not eg_partner_id:
                                eg_partner_id = self.env["eg.res.partner"].create({"odoo_partner_id": partner_id.id,
                                                                                   "instance_id": instance_id.id,
                                                                                   "inst_partner_id": str(
                                                                                       customer.get("id")),
                                                                                   "update_required": False})
                            return child_id

                if not partner_id.child_ids or create_child:
                    country_id = self.env["res.country"].search(
                        [("code", "=", default_address.get("country_code"))])
                    if not country_id:
                        country_id = self.env["res.country"].create(
                            {"name": default_address.get("country_name"),
                             "code": default_address.get("country_code")})
                    state_id = self.env["res.country.state"].search(
                        [("code", "=", default_address.get("province_code")), ("country_id", "=", country_id.id)])
                    if not state_id:
                        state_id = self.env["res.country.state"].create(
                            {"name": default_address.get("province"),
                             "code": default_address.get("province_code"),
                             "country_id": country_id.id})
                    child_partner_id = self.create([{"name": default_address.get("name"),
                                                     "street": default_address.get("address1") or "",
                                                     "street2": default_address.get("address2") or "",
                                                     "city": default_address.get("city") or "",
                                                     "zip": default_address.get("zip") or "",
                                                     "country_id": country_id and country_id.id or None,
                                                     "phone": default_address.get("phone") or "",
                                                     "state_id": state_id and state_id.id or None,
                                                     "type": "other",
                                                     "parent_id": partner_id.id
                                                     }])
                    if not eg_partner_id:
                        eg_partner_id = self.env["eg.res.partner"].create({"odoo_partner_id": partner_id.id,
                                                                           "instance_id": instance_id.id,
                                                                           "inst_partner_id": str(customer.get("id")),
                                                                           "update_required": False})
                    return child_partner_id

            if not eg_partner_id:
                eg_partner_id = self.env["eg.res.partner"].create({"odoo_partner_id": partner_id.id,
                                                                   "instance_id": instance_id.id,
                                                                   "inst_partner_id": str(customer.get("id")),
                                                                   "update_required": False})
            return partner_id

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
