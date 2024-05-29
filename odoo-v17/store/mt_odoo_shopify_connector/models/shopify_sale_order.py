# -*- coding: utf-8 -*-

import shopify
import logging

from odoo.tools import html_keep_url
from odoo.exceptions import UserError
from odoo import api, fields, _, models
from odoo.tools import config
config['limit_time_real'] = 10000000
config['limit_time_cpu'] = 150

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    @api.model
    def default_get(self, fields):
        res = super(SaleOrder, self).default_get(fields)
        if self.env['shopify.instance']._context.get('shopify_instance_id'):
            res['shopify_instance_id'] = self.env['shopify.instance']._context.get('shopify_instance_id')
            
        return res

    shopify_id = fields.Char('Shopify ID')
    shopify_order_no = fields.Char('Shopify Order No.')
    shopify_processing_method = fields.Char("Shopify Processing Method")
    shopify_status = fields.Char('Shopify Order Status')
    shopify_fulfillment_status = fields.Char('Shopify Fulfillment Status')
    shopify_fulfillment_location = fields.Char('Shopify Fulfillment location')
    shopify_order_url = fields.Char(string="Order URL")
    shopify_order_date = fields.Date(string="Shopify Order Date")
    shopify_order_subtotal = fields.Float('Shopify Order Subtotal')
    shopify_order_total_tax = fields.Float('Shopify Order Total Tax')
    shopify_order_total = fields.Float('Shopify Order Total Price')
    shopify_order_note = fields.Char('Shopify Order Note from Customer')
    
    is_exported = fields.Boolean('Synced In Shopify', default=False)
    is_shopify_order = fields.Boolean('Is Shopify Order', default=False)
    is_shopify_draft_order = fields.Boolean('Shopify Draft Order', default=False)
    
    shopify_instance_id = fields.Many2one('shopify.instance', ondelete='cascade')
    fulfillment_id = fields.One2many('shopify.order.fulfillment', 'so_id')

    @api.onchange("invoice_count")
    def update_invoice_instance_id(self):
        for id in self.invoice_ids:
            id.shopify_instance_id = self.shopify_instance_id
            
    @api.depends('invoice_count')
    def _set_invoice_instance_id(self):
        for order in self:
            invoices = order.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
        for invoice in invoices:
            invoice.shopify_instance_id = self.shopify_instance_id
            
   
    def init_shopify_session(self, instance_id):
        try:
            session = shopify.Session(instance_id.shop_url, instance_id.api_version, instance_id.admin_api_key)
            return session
        except Exception as error:
            raise UserError(_("Please check your connection and try again"))
        
    def cron_import_shopify_orders(self):
        all_instances = self.env['shopify.instance'].sudo().search([])
        for rec in all_instances:
            if rec:
                self.env['sale.order'].import_sale_order(rec)
                
    def get_all_orders(self, instance_id, limit=100):
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
        
        get_next_page = True
        since_id = 0
        while get_next_page:
            orders = shopify.Order.find(since_id=since_id, limit=limit, status="any")

            for order in orders:
                yield order
                since_id = order.id

            if len(orders) < limit:
                get_next_page = False
                  
    def import_sale_order(self, instance_id):
        
        for order in self.get_all_orders(instance_id):
            self.create_sale_order(order, instance_id)
        return

    def create_sale_order(self, order, instance_id):
        _logger.info('\n\n\n\n  create_sale_order  =  %s \n\n\n\n' % (order.id) )

        res_partner = ''
        res_partner = self.is_customer_exist(order,  instance_id)
        
        if not res_partner:
            self.env['res.partner'].create_customer(order.customer, instance_id)
            res_partner = self.is_customer_exist(order,  instance_id)
        
        if res_partner:
            
            dict_so = {}
            dict_so['shopify_id'] = order.id
            dict_so['partner_id'] = res_partner.id                
            dict_so['name'] = order.name
            dict_so['shopify_instance_id'] = instance_id.id
            dict_so['shopify_order_no'] = order.order_number if hasattr(order, 'order_number') else ''
            dict_so['company_id'] = instance_id.shopify_company_id.id
            dict_so['state'] = 'draft' #'sale'
            dict_so['shopify_order_subtotal'] = float(order.subtotal_price)
            dict_so['shopify_order_total_tax'] = float(order.total_tax)
            dict_so['shopify_order_total'] = float(order.total_price)
            dict_so['shopify_order_date'] = order.created_at
            dict_so['shopify_order_url'] = order.order_status_url if hasattr(order, 'order_status_url') else ''
            dict_so['amount_total'] = float(order.total_price)
            dict_so['shopify_processing_method'] = order.processing_method if hasattr(order, 'processing_method') else ''
            dict_so['shopify_status'] = order.financial_status if hasattr(order, 'financial_status') else ''
            dict_so['shopify_fulfillment_status'] = order.fulfillment_status if hasattr(order, 'fulfillment_status') else ''
            dict_so['shopify_order_note'] = order.note
            dict_so['is_exported'] = True                

            dict_so['payment_term_id'] = self.create_payment_terms(order)                  

            sale_order = self.env['sale.order'].sudo().search([('shopify_id', '=', order.id)], limit=1)
            if not sale_order:
                dict_so['is_shopify_order'] = True
                so_obj = self.env['sale.order'].sudo().create(dict_so)

                create_invoice = self.create_shopify_sale_order_lines(so_obj.id, instance_id, order)
                
                self.create_shopify_shipping_lines(so_obj.id, instance_id, order)
                                    
                
                if order.processed_at:
                    so_obj.action_confirm()
                    if create_invoice == True:
                        so_obj._create_invoices()
                    
                # To cancel the cancelled orders from shopify
                if hasattr(order, 'cancel_reason'):
                    if order.cancel_reason:
                        soc = self.env['sale.order.cancel'].sudo().create({'order_id' : so_obj.id})
                        soc.action_cancel()
                    
                self.env.cr.commit()  
            else:
                if sale_order.state != 'done':       
                    if sale_order.state != 'draft':
                        dict_so['state'] = sale_order.state
                    sale_order.sudo().write(dict_so)
                    
                    for sol_item in order.line_items:
                        res_product = self.env['product.product'].sudo().search(
                            ['|', ('shopify_variant_id', '=', sol_item.product_id), ('shopify_variant_id', '=', sol_item.variant_id)],
                            limit=1)

                        if res_product:
                            s_order_line = self.env['sale.order.line'].sudo().search(
                                [('product_id', '=', res_product.id),
                                    (('order_id', '=', sale_order.id))], limit=1)

                            if s_order_line:
                                tax_id_list= self.add_tax_lines( instance_id, sol_item.tax_lines)
                        
                                so_line = self.env['sale.order.line'].sudo().search(
                                    ['&', ('product_id', '=', res_product.id),
                                        (('order_id', '=', sale_order.id))], limit=1)
                                if so_line:
                                    so_line_data = {
                                        'name': res_product.name,                                        
                                        'product_id': res_product.id,
                                        'shopify_so_line_id': sol_item.id,
                                        'tax_id': [(6, 0, tax_id_list)],
                                        'product_uom_qty': sol_item.quantity,                                        
                                        'price_unit': float(sol_item.price) if sol_item.price != '0.00' else 0.00,                                        
                                        'shopify_vendor_name': sol_item.vendor
                                    }
                                    sol_update = so_line.update(so_line_data)
                            else:
                                so_line = self.create_sale_order_line(sale_order.id, instance_id, sol_item)
                        self.env.cr.commit()
                        
                    if hasattr(order, "shipping_lines"):
                                              
                        if order.shipping_lines:
                            for sh_line in order.shipping_lines:
                                shipping = self.env['delivery.carrier'].sudo().search(['&', ('shopify_id', '=', sh_line.code), ('shopify_instance_id', '=', instance_id.id)], limit=1)    
                                
                                so_line = self.env['sale.order.line'].sudo().search(['&', ('is_delivery', '=', True),(('order_id', '=', sale_order.id))], limit=1)
                                if shipping and shipping.product_id:
                                    if shipping.product_id.id != so_line.product_id.id:
                                        shipping_vals = {
                                            'product_id': shipping.product_id.id,
                                            'name':shipping.product_id.name,
                                            'price_unit': float(sh_line.price),
                                            'is_delivery' : True,
                                            'tax_id': [(6, 0, [])]
                                        }
                                        shipping_update = so_line.update(shipping_vals)
                        else:
                            #To remove shipping price, if the shipping not selected in the shopify site due shipping conditions.
                            so_line = self.env['sale.order.line'].sudo().search(['&', ('is_delivery', '=', True),(('order_id', '=', sale_order.id))], limit=1)
                            
                            if so_line:
                                so_line.unlink()
                            
                    # To cancel the cancelled orders from shopify
                    if hasattr(order, 'cancel_reason'):
                        if order.cancel_reason:
                            soc = self.env['sale.order.cancel'].sudo().create({'order_id' : sale_order.id})
                            soc.action_cancel()
                        
        return
    
    def create_shopify_sale_order_lines(self, so_id, instance_id, order):

        create_invoice = False
        for sol_item in order.line_items:
            
            so_line = self.create_sale_order_line(so_id, instance_id, order, sol_item)
            if so_line:
                if so_line.qty_to_invoice > 0:
                    create_invoice = True
            
        return create_invoice
    
    def create_sale_order_line(self, so_id, instance_id, order, line_item):
        
        res_product = ''     
        if line_item.product_id or line_item.variant_id:
            res_product = self.env['product.product'].sudo().search(
                ['|', ('shopify_variant_id', '=', line_item.product_id), ('shopify_variant_id', '=', line_item.variant_id)],
                limit=1)
            
            if not res_product:
                _logger.info('\n\n\n\n  Product not exist to create Order  =  %s \n\n\n\n' % (order.id) )
                # need to check about creating product using existing function
                
            if res_product:
                dict_l = {}
                dict_l['shopify_so_line_id'] = line_item.id
                dict_l['order_id'] = so_id
                dict_l['product_id'] = res_product.id
                dict_l['name'] = res_product.name
                dict_l['product_uom_qty'] = line_item.quantity
                dict_l['shopify_vendor_name'] = line_item.vendor
                dict_l['price_unit'] = float(line_item.price) if line_item.price != '0.00' else 0.00
                dict_l['discount'] = float(order.discount_applications[0].value) if order.discount_applications else 0                                       

                tax_id_list= self.add_tax_lines(instance_id, line_item.tax_lines)

                dict_l['tax_id'] = [(6, 0, tax_id_list)]
                    
                if line_item.price_set.shop_money.currency_code:
                    cur_id = self.env['res.currency'].sudo().search([('name', '=', line_item.price_set.shop_money.currency_code)], limit=1)
                    dict_l['currency_id'] = cur_id.id

                return self.env['sale.order.line'].sudo().create(dict_l)
            
            return False
                    
    def create_shopify_shipping_lines(self, so_id, instance_id, order):
        for sh_line in order.shipping_lines:
            shipping = self.env['delivery.carrier'].sudo().search(['&', ('shopify_id', '=', sh_line.code), ('shopify_instance_id', '=', instance_id.id)], limit=1)
            custom_shipping = self.env['delivery.carrier'].sudo().search(['&', ('name', '=', sh_line.title), ('shopify_instance_id', '=', instance_id.id)], limit=1)

            if not shipping and not custom_shipping and sh_line.code != 'custom':               
                delivery_product = self.env['product.product'].sudo().create({
                    'name': sh_line.title,
                    'detailed_type': 'service',
                    'taxes_id': [(6, 0, [])]
                })
                               
                vals = {
                    'shopify_id': sh_line.code,
                    'is_shopify': True,
                    'shopify_instance_id': instance_id.id,
                    'name': sh_line.title,
                    'product_id': delivery_product.id,
                    'fixed_price': float(sh_line.price),
                    'shopify_handle' : sh_line.source +"-"+ sh_line.title +"-"+ sh_line.price,
                    'shopify_carrier_identifier' : sh_line.carrier_identifier 
                }
                shipping = self.env['delivery.carrier'].sudo().create(vals)
                
            if custom_shipping and sh_line.code != 'custom':
                custom_shipping.sudo().write({'shopify_id': sh_line.code,
                                        'fixed_price': float(sh_line.price),
                                        'shopify_handle' : sh_line.source +"-"+ sh_line.title +"-"+ sh_line.price,})
                
            if not shipping and sh_line.code == 'custom':
                if not custom_shipping:
                    delivery_product = self.env['product.product'].sudo().create({
                        'name': sh_line.title,
                        'detailed_type': 'service',
                        'taxes_id': [(6, 0, [])]
                    })
                               
                    vals = {
                        'shopify_id': "",
                        'is_shopify': True,
                        'shopify_instance_id': instance_id.id,
                        'name': sh_line.title,
                        'product_id': delivery_product.id,
                        'fixed_price': float("0.00"),
                        'shopify_handle' : "",
                        'shopify_carrier_identifier' : sh_line.carrier_identifier 
                    }
                    shipping = self.env['delivery.carrier'].sudo().create(vals)
                elif custom_shipping:
                    shipping = custom_shipping

            tax_id_list = self.add_tax_lines(instance_id, sh_line.tax_lines)
            if shipping and shipping.product_id:
                shipping_vals = {
                    'product_id': shipping.product_id.id,
                    'name':shipping.product_id.name,
                    'price_unit': float(sh_line.price),
                    'order_id': so_id,
                    'is_delivery' : True,
                    'tax_id': [(6, 0, tax_id_list)]
                }
                shipping_so_line = self.env['sale.order.line'].sudo().create(shipping_vals)

    def is_customer_exist(self, order, instance_id):
        
        first = getattr(order.customer,'first_name') or ''
        last = getattr(order.customer,'last_name') or ''         
            
        dict_res_p = {}
        dict_res_p['email'] = getattr(order.customer,'email') or ''
        dict_res_p['phone'] = getattr(order.customer,'phone') or ''
        dict_res_p['name'] = dict_res_p['email'] if (not first.strip() and not last.strip()) else first.strip() + " " + last.strip()
        dict_res_p['shopify_user_id'] = getattr(order.customer,'id') or ''
        dict_res_p['shopify_instance_id'] = instance_id.id
        dict_res_p['company_id'] = instance_id.shopify_company_id.id
        dict_res_p['is_exported'] = True
        dict_res_p['is_shopify_customer'] = True
        dict_res_p['customer_rank'] = 1
        
        res_partner = self.env['res.partner'].sudo().search(
                    [('shopify_user_id', '=', order.customer.id)], limit=1)
                   
        if not res_partner and dict_res_p['email']:
            res_partner = self.env['res.partner'].sudo().search(
                    [('email', '=', dict_res_p['email'])], limit=1)
            if not res_partner:
                if dict_res_p['name'] or dict_res_p['email'] or dict_res_p['phone']:
                    res_partner = self.env['res.partner'].sudo().create(dict_res_p)
                            
        return res_partner

    def add_tax_lines(self, instance_id, tax_lines):
        
        tax_id_list = []
        if tax_lines:
            for tax_line in tax_lines:
                dict_tax = {}
                dict_tax['amount'] = float(tax_line.rate * 100)
                shopify_tax_name = tax_line.title + ' ' + str(float(tax_line.rate * 100)) + '%'
                
                custom_tax_id = instance_id.name + "_" + tax_line.title
                acc_tax = self.env['account.tax'].sudo().search(
                    [('shopify_id', '=', custom_tax_id),
                        ('company_id', '=', instance_id.shopify_company_id.id)], limit=1)
                acc_tax_group_id = self.env['account.tax.group'].sudo().search(
                                [('name', '=', shopify_tax_name)], limit=1)
                if not acc_tax_group_id :
                    acc_tax_group_id = self.env['account.tax.group'].sudo().create({
                                                                'name': shopify_tax_name
                                                            })
                    
                if acc_tax:
                    acc_tax.sudo().write(dict_tax)
                else:
                    dict_tax['shopify_id'] = custom_tax_id
                    dict_tax['shopify_instance_id'] = instance_id.id
                    dict_tax['name'] = tax_line.title
                    dict_tax['description'] = shopify_tax_name
                    dict_tax['company_id'] = instance_id.shopify_company_id.id
                    dict_tax['country_id'] = instance_id.shopify_company_id.country_id.id                                
                    dict_tax['tax_group_id'] = acc_tax_group_id.id,
                    dict_tax['is_exported'] = True
                    dict_tax['is_shopify_tax'] = True
                    
                    acc_tax = self.env['account.tax'].sudo().create(dict_tax)
                    
                if tax_line.price != '0.00':
                    tax_id_list.append(acc_tax.id)
            
        return tax_id_list
                             
    def create_payment_terms(self, order):
        #need to check payment
        if hasattr(order,'payment_details'):
            if order.payment_details.credit_card_company:
                pay_id = self.env['account.payment.term']
                payment = pay_id.sudo().search(
                    [('name', '=', order.payment_details.credit_card_company)], limit=1)
                if not payment:
                    create_payment = payment.sudo().create({
                        'name': order.payment_details.credit_card_company
                    })
                    if create_payment:
                        return create_payment.id
                else:
                    return payment.id
        return False

    def shopify_order_update_button(self):
        
        session = self.init_shopify_session(self.shopify_instance_id)
        shopify.ShopifyResource.activate_session(session)
        data = {}
        data['order'] = {
                    "id": self.shopify_id,
                    "note": self.shopify_order_note,
                }
        result = shopify.Order(data['order'])                        
        r_data = result.save()


    def get_current_order(self):
        selected_ids = self.env.context.get('active_ids', [])
        order_id = self.sudo().search([('id', 'in', selected_ids)])

        if not order_id:
            raise UserError(_("Please select Order!!!"))
        else:
            return order_id
 
    def is_cancelled(self):
        if self.state == "cancel":
            raise UserError(_("This action cann't perform in a cancelled order."))       

    def action_shopify_order_wizard(self):
        
        self.is_cancelled()
        
        action = self.env.ref("mt_odoo_shopify_connector.action_shopify_order_actions_wizard").read()[0]
        action.update({
            'context': "{'shopify_instance_id': " + str(self.shopify_instance_id.id) + ", 'order_actions': " + str(self.get_current_order().id) + "}",
        })        

        # _logger.info('\n\n\n\n  action_shopify_order_wizard  =  %s \n\n\n\n' % (action) )
        return action
    

    def action_generate_invoice(self):
        
        self.is_cancelled()
        
        action = self.env.ref("mt_odoo_shopify_connector.action_wizard_generate_invoice").read()[0]
        action.update({
            'context': "{'shopify_instance_id': " + str(self.shopify_instance_id.id) + "}",
        })         
        return action

    def order_generate_invoice(self, instance_id):
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
               
        order_ids = self.get_current_order()
        
        for order in order_ids:
            for order_invoice in  order.invoice_ids:
                if order_invoice.state == "draft":
                    order_invoice.action_post() #to confirm invoice 
                if order_invoice.state == "posted" and order_invoice.payment_state == "not_paid":
                    order_invoice.action_register_payment() #to register payment 


    # Shopify Refund Code
    def order_refund_create(self, instance_id):
        
        order_ids = self.get_current_order()
        
        for order in order_ids: 
            self.shopify_refund(instance_id, order)
            
    def shopify_refund(self, instance_id, order):
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
        
        data = {}       
        refund = shopify.Refund()     
        data.update( {'order_id' : order.shopify_id,
                      'notify' : False, 
                    #   'note' : "wrong size",
                    #   'currency' : "INR"
                    })
        data['shipping'] = { "full_refund": True }
        data['refund_line_items'] = []
        so_lines = self.env['sale.order.line'].sudo().search([('order_id', '=', order.id)])
        for line in so_lines:
            if line.shopify_so_line_id and int(line.product_uom_qty) > 0:
                line_items = {
                    "line_item_id": line.shopify_so_line_id,
                    "quantity": int(line.product_uom_qty),
                    "restock_type": "no_restock",
                    "location_id": None
                }
                
                fo_line = self.env['shopify.order.fulfillment.line'].sudo().search([('f_line_item_id', '=', line.shopify_so_line_id)], limit=1)
                if fo_line:
                    if fo_line.fulfillment_id.location_id:
                        line_items['restock_type'] = "return"
                        line_items['location_id'] = fo_line.fulfillment_id.location_id
                    
                data['refund_line_items'].append(line_items)
            
        try:   
            refund_data = refund.calculate(order_id = order.shopify_id, shipping = data['shipping'], refund_line_items = data['refund_line_items'])      
            
            refund = shopify.Refund({'order_id' : order.shopify_id})     
            
            data['transactions'] = []
            
            if refund_data.attributes['transactions']:
                for tran in refund_data.attributes['transactions']:
                    tran.attributes['kind'] = "refund"
                    data['transactions'].append(tran.attributes)
            
            d_ref = refund.create(data)
            _logger.info('\n\n\n\n  shopify_refund result   =  %s \n\n\n\n' % (d_ref) )    
            
        except Exception as error:
            _logger.info('\n\n\n\n  Error   =  %s \n\n\n\n' % (error.response.__dict__) )
            raise UserError(_(error.response.body))

    # Shopify Fulfillment Code
    def order_fulfillment_create(self, instance_id):
               
        order_ids = self.get_current_order()
        
        for order in order_ids: 
            self.shopify_fulfillment(instance_id, order)
        
    def shopify_fulfillment(self, instance_id, order):
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)

        if not order.shopify_id:
            raise UserError(_("Shopify Id Not Found!!!"))
        
        fulfillment_orders = shopify.FulfillmentOrders.find(order_id = order.shopify_id)  
        fo_id_list = [] 
        for f_order in fulfillment_orders:
            if f_order.status == 'open':
                fo_id_list.append({"fulfillment_order_id": f_order.id})
                        
        #temporary fix for the url issue.
        shopify.Fulfillment._prefix_source = ''
        data = {}       

        fulfillment = shopify.Fulfillment()  
        data['line_items_by_fulfillment_order']  = fo_id_list
        data['tracking_info'] = {"number": "", "url": "" }

        fulfillment.line_items_by_fulfillment_order = fo_id_list
        fulfillment.notify_customer = False
        fulfillment.tracking_info = {"number": "", "url": "" }
        
        # res = fulfillment.create(data) #return fulfillment object
        res = fulfillment.save() #return true/false
                  
        #revert the temporary fix for normal working.
        shopify.Fulfillment._prefix_source = "/orders/$order_id/"
  

    def shopify_order_cancel(self, instance_id):
        
        order_id = self.get_current_order()
        
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
        
        order = shopify.Order()    
        order.id =  order_id.shopify_id
        order.reason =  "declined"
        order.restock = True
        d_ref = order.cancel()   
        
        order_data = order.find(order_id.shopify_id)
        # To cancel the cancelled orders from shopify
        if order_data.cancel_reason:
            soc = self.env['sale.order.cancel'].sudo().create({'order_id' : order_id.id})
            soc.action_cancel()
                
                
    def shopify_force_info_update(self, instance_id):
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
               
        order_id = self.get_current_order()
        
        try:
            order = shopify.Order.find(order_id.shopify_id)
            self.create_sale_order(order, instance_id)
        
        except Exception as error:
            raise UserError(_(error.response.body))

    def shopify_draft_order_send_invoice(self, instance_id):
        
        order_id = self.get_current_order()
        
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
        try:
            draft_order = shopify.DraftOrder()
            draft_order.id = order_id.shopify_id
            
            # mail_from = {"from" : "mail@mail.com"} 
            # draft_order.send_invoice(draft_order_invoice = shopify.DraftOrderInvoice(mail_from))
            draft_order.send_invoice()
        
        except Exception as error:
            _logger.info('\n\n\n\n  shopify_order_send_invoice   =  %s \n\n\n\n' % (error) )
            raise UserError(_(error.response.body))        

# Update Draft Orders
    def cron_shopify_draft_orders_update(self):
        all_instances = self.env['shopify.instance'].sudo().search([])
        for instance_rec in all_instances:
            if instance_rec:
                draft_orders = self.sudo().search([('is_shopify_draft_order', '=', True),('shopify_instance_id.id', '=', instance_rec.id)])
                for d_order in draft_orders:
                    self.env['sale.order'].update_draft_orders(instance_rec, d_order)
               
    def shopify_draft_orders_update(self, instance_id): 
        order_id = self.get_current_order()

        try:
            self.update_draft_orders(instance_id, order_id)
        
        except Exception as error:
            raise UserError(_(error))              

    def update_draft_orders(self, instance_id, d_order):
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
        
        try :
            draft_order = shopify.DraftOrder.find(d_order.shopify_id)
            if draft_order:
                if draft_order.order_id:
                    d_order.update({'shopify_id' : draft_order.order_id, 'is_shopify_draft_order': False})

        except Exception as error:
            order = shopify.Order.exists(d_order.shopify_id)
            if order:
                d_order.update({'is_shopify_draft_order': False})
                self.env.cr.commit()  
            else:
                d_order.update({'shopify_id' : '', 'is_shopify_draft_order': False})
                self.env.cr.commit()  
            raise UserError(_(error.response.body))
 
# Create draft orders
    def shopify_draft_order_create(self, instance_id):
               
        order_ids = self.get_current_order()
        
        for order in order_ids: 
            self.create_draft_order(instance_id, order)
     
    def create_draft_order(self, instance_id, order):
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
        
        data = {}       
        new_order = shopify.DraftOrder()     
        data.update( {'use_customer_default_address' : True,})
        data['customer'] = { "id": order.partner_id.shopify_user_id }
        data['line_items'] = []
        so_lines = self.env['sale.order.line'].sudo().search([('order_id', '=', order.id)])
        for line in so_lines:
            if line.product_id.shopify_variant_id and int(line.product_uom_qty) > 0:
                line_items = {
                    "variant_id": line.product_id.shopify_variant_id,
                    "quantity": int(line.product_uom_qty),
                }
                data['line_items'].append(line_items)
                
            if line.is_delivery:
                shipping_line = self.env['delivery.carrier'].sudo().search([('product_id', '=', line.product_id.id)], limit=1)
                
                data_shipping_line = {}

                data_shipping_line.update({"title": shipping_line.name})

                    
                if float(line.price_unit) != float(shipping_line.fixed_price):
                    data_shipping_line.update({"price": line.price_unit})
                    data_shipping_line.update({"custom": True})
                else:
                    data_shipping_line.update({"price": shipping_line.fixed_price})
                    
                    if shipping_line.shopify_handle:
                        data_shipping_line.update({"handle": shipping_line.shopify_handle})
                    else :
                        data_shipping_line.update({"custom": True})
                data['shipping_line'] = data_shipping_line
                
        order_data = new_order.create(data)
        if order_data.id:
            order.update({'shopify_id' : order_data.id, 'is_shopify_draft_order':True, 'is_exported':True, 'name' : order_data.name })
            # To create Order data in db after exporting.
            self.create_sale_order(order_data, instance_id)
            
            order.update({'is_shopify_order' : False })
            
                

    def shopify_export_order(self, instance_id):
               
        order_ids = self.get_current_order()
        
        for order in order_ids: 
            self.shopify_order_create(instance_id, order)
            
    def shopify_order_create(self, instance_id, order):
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
        
        data = {}       
        new_order = shopify.Order()     
        data.update( {'financial_status' : "pending",})
        data['customer'] = { "id": order.partner_id.shopify_user_id }
        data['line_items'] = []
        so_lines = self.env['sale.order.line'].sudo().search([('order_id', '=', order.id)])
        for line in so_lines:
            line_items = {
                "variant_id": line.product_id.shopify_variant_id,
                "quantity": int(line.product_uom_qty),
            }
            data['line_items'].append(line_items)
           
        order_data = new_order.create(data)
        if order_data.id:
            order.update({'shopify_id' : order_data.id, 'is_exported':True, 'name' : order_data.name })
            # To create Order data in db after exporting.
            self.create_sale_order(order_data, instance_id)
            
            order.update({'is_shopify_order' : False })
            
            if order_data.processed_at:
                order.action_confirm()
                order._create_invoices()
                 
        
                
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    shopify_so_line_id = fields.Char('Shopify Line ID')
    shopify_vendor_name = fields.Char('Shopify Vendor Name')
    
    shopify_vendor = fields.Many2one('res.partner', 'Shopify Vendor')
