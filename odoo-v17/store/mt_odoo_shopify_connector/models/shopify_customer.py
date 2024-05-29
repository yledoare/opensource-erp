# -*- coding: utf-8 -*-

import logging
import shopify
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class Customer(models.Model):
    _inherit = 'res.partner'
    
    @api.model
    def default_get(self, fields):
        res = super(Customer, self).default_get(fields)
        if self.env['shopify.instance']._context.get('shopify_instance_id'):
            res['shopify_instance_id'] = self.env['shopify.instance']._context.get('shopify_instance_id')
        return res

    shopify_user_id = fields.Char('Shopify User ID')
    shopify_address_id = fields.Char('Shopify Address ID')
    shopify_order_count = fields.Integer('Order Count From Shopify')
    shopify_customer_note = fields.Text('Shopify User Note')

    is_exported = fields.Boolean('Synced In shopify', default=False)
    is_shopify_customer = fields.Boolean('Is Shopify Customer', default=False)

    shopify_instance_id = fields.Many2one('shopify.instance', ondelete='cascade')
    
    def init_shopify_session(self, instance_id):
        try:
            session = shopify.Session(instance_id.shop_url, instance_id.api_version, instance_id.admin_api_key)
            return session
        except Exception as error:
            raise UserError(_("Please check your connection and try again"))
    
    
    def cron_export_shopify_customers(self):
        all_instances = self.env['shopify.instance'].sudo().search([])
        for rec in all_instances:
            if rec:
                self.env['res.partner'].export_customers(rec)

    def export_customers(self, instance_id):
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
        
        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['res.partner'].sudo().browse(selected_ids)
        all_records = self.env['res.partner'].sudo().search([])
        if selected_records:
            records = selected_records
        else:
            records = all_records

        export_list = []

        for rec in records:
                          
            billing_addr = {}
            dict_contacts = {}

            contacts_billing = self.env['res.partner'].sudo().search([('parent_id', '=', rec.id), ('type', '=', 'invoice')],limit=1)
            
            if rec:
                dict_contacts['email'] = getattr(rec, 'email') or ''
                if rec.name:
                    dict_contacts['first_name']= rec.name.split()[0]
                    dict_contacts['last_name']= rec.name.split()[1] if len(rec.name.split()) == 2 else ""
                if hasattr(rec, 'phone'):
                    dict_contacts['phone']= getattr(rec, 'phone') or ''
            
            if contacts_billing:
                billing_addr = self.set_address(contacts_billing)
            else:     
                billing_addr = self.set_address(rec)   
               
            export_list.append({
                        "customer": {
                            "id": rec.shopify_user_id,
                            "first_name": dict_contacts['first_name'],
                            "last_name": dict_contacts['last_name'],
                            "email": dict_contacts['email'],
                            "phone": dict_contacts['phone'],
                            "verified_email": True,
                            "addresses": [billing_addr]
                        }
                    })
            _logger.info('\n\n\n\n Export records data %s \n\n\n\n\n' % export_list)
        if export_list:
            for data in export_list:
                if data['customer'].__contains__('id'):
                    if data['customer']['id']:
                        try:
                            customers = shopify.Customer(data['customer'])                        
                            customers.save()
                        except Exception as error:
                            _logger.info('\n\n\n\n Error ------ %s \n\n\n\n\n' % error)
                            raise UserError(_("Please check your connection and try again"))
                    else:
                        try:
                            data['customer'].pop('id')                       
                            data['customer'].pop('phone')
                            
                            result = shopify.Customer.create(data['customer'])
                        except Exception as error:
                            _logger.info('\n\n\n\n Error new customer ------ %s \n\n\n\n\n' % error)
                            raise UserError(_("Please check your connection and try again"))
        self.import_customer(instance_id)


    def cron_import_shopify_customers(self):
        all_instances = self.env['shopify.instance'].sudo().search([])
        for rec in all_instances:
            if rec:
                self.env['res.partner'].import_customer(rec)
    
    def get_all_customers(self, instance_id, limit=100):
        
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
        
        get_next_page = True
        since_id = 0
        while get_next_page:
            customers = shopify.Customer.find(since_id=since_id, limit=limit)

            for customer in customers:
                yield customer
                since_id = customer.id

            if len(customers) < limit:
                get_next_page = False
    
    def import_customer(self, instance_id):
        for customer in self.get_all_customers(instance_id):
            self.create_customer(customer, instance_id)
            
        return
    
    def create_customer(self, customer, instance_id):
        existing_customer = self.env['res.partner'].sudo().search([('shopify_user_id', '=', customer.id)], limit=1)
        ''' 
            This is used to update shopify_user_id of a customer, this
            will avoid duplication of customer while syncing customers.
        '''
        customer_without_shopify_user_id = self.env['res.partner'].sudo().search(
            [('shopify_user_id', '=', False), ('email', '=', customer.email), ('type', '=', 'contact')], limit=1)

        contact_details = {}
        first = getattr(customer,'first_name') or ''
        last = getattr(customer,'last_name') or ''         
            
        contact_details['shopify_user_id'] = getattr(customer,'id') or ''
        contact_details['email'] = getattr(customer,'email') or ''
        contact_details['phone'] = getattr(customer,'phone') or ''
        contact_details['name'] = contact_details['email'] if (not first.strip() and not last.strip()) else first.strip() + " " + last.strip()

        dict_p = {}
        
        dict_p['shopify_instance_id'] = instance_id.id
        dict_p['company_id'] = instance_id.shopify_company_id.id
        dict_p['is_exported'] = True
        dict_p['is_shopify_customer'] = True
        dict_p['customer_rank'] = 1
        dict_p.update(contact_details)
        
        # _logger.info('\n\n\n\n import records data %s \n\n\n\n\n' % dict_p)
        
        if not existing_customer and customer_without_shopify_user_id:
            customer_without_shopify_user_id.sudo().write(dict_p)
            
        #pass default address
        address = {}
        if hasattr(customer,'default_address'):
            address= self.address_array(customer.default_address)
        address['email'] = contact_details['email']
        
        if not existing_customer and not customer_without_shopify_user_id:
            ''' If customer is not present we create it '''
            new_customer = self.env['res.partner'].sudo().create(dict_p)
            if new_customer:              
                # to add address id to contact type entry in res.partner 
                new_customer.sudo().write({'shopify_address_id' : address['shopify_address_id']})
    
                if hasattr(customer,'default_address'):
                    #billing
                    self.create_address(address, new_customer.id, 'invoice', 'Invoice create import ')
                    #shipping
                    self.create_address(address, new_customer.id, 'delivery', 'Delivery create import ')
                
                self.env.cr.commit()
        else:
            update_customer = existing_customer.sudo().write(dict_p)
            if update_customer:
                ''' Search for updated customer '''
                customer_record = self.env['res.partner'].sudo().search([('shopify_user_id', '=', customer.id)],limit=1)
                if customer_record and hasattr(customer,'default_address'):
                    '''Invoice Address Update/Create'''
                    self.update_or_create_address(customer_record.id, address, 'invoice')
                    
                    '''Delivery Address Update/Create'''
                    self.update_or_create_address(customer_record.id, address, 'delivery')
                    
                self.env.cr.commit()
            
        return  
     
    def update_or_create_address(self, record_id, address, addr_type='invoice'):
        '''Search for customer id'''
        customer_id = self.env['res.partner'].sudo().search(
            [('parent_id', '=', record_id), ('type', '=', addr_type)],limit=1)
        if customer_id:
            #update
            self.update_existing_address(address, customer_id, addr_type, 'address Updated')
        else:
            #create
            self.create_address(address, record_id, addr_type, 'create address import EXISTING CUSTOMER')

    def create_address(self, address, parent_id, addr_type='invoice', log_str=''):
        dict_a = {}
        dict_a.update(address)
        dict_a['is_company'] = False
        dict_a['parent_id'] = parent_id
        dict_a['type'] = addr_type   

        if dict_a['name'] and dict_a['email']:
            if log_str !='':
                _logger.info('\n\n\n\n %s  %s \n\n\n\n\n' % (log_str, dict_a))
            address_create = self.env['res.partner'].sudo().create(dict_a)
    
    def update_existing_address(self, address, customer_data, addr_type='invoice', log_str=''):
        if log_str !='':
                _logger.info('\n\n\n\n %s  %s \n\n\n\n\n' % (log_str, address))
        if hasattr(address,'country_id'):
            if address['state_id'] and address['state_id'] != '':
                customer_data.sudo().write({'state_id': address['state_id']})
            addr_arr = {
                'shopify_address_id' : address['shopify_address_id'],
                'name': address['name'],
                'zip': address['zip'],
                'city': address['city'],
                'street': address['street'],
                'street2': address['street2'],
                'country_id': address.get('country_id', ''),
                'phone': address['phone'],
                'parent_id': customer_data.parent_id,
                'type': addr_type
            }
            address_update_data = customer_data.sudo().write(addr_arr)
    
    def address_array(self, address_data ):
        address= {}
        address['shopify_address_id'] = getattr(address_data,'id') or ''
        address['name'] = getattr(address_data,'name') or ''
        address['phone'] = getattr(address_data,'phone') or ''
        address['zip'] = getattr(address_data,'zip') or ''
        address['street'] = getattr(address_data,'address1') or ''
        address['street2'] = getattr(address_data,'address2') or ''
        address['city'] = getattr(address_data,'city') or ''

        if address_data.country:
            country_id = self.env['res.country'].sudo().search(
                [('code', '=', address_data.country_code)],limit=1)
            address['country_id'] = country_id.id
            if address_data.province_code:
                state_id = self.env['res.country.state'].sudo().search(
                    ['&', ('code', '=', address_data.province_code),
                        ('country_id', '=', country_id.id)],limit=1)
                
                address['state_id'] = state_id.id if state_id else ''

        return address
    
    def set_address(self, addr_rec):
        addr = {}
        if addr_rec.shopify_address_id and addr_rec.shopify_user_id:
            addr['id'] = addr_rec.shopify_address_id
        if addr_rec.name:
            addr['first_name']= addr_rec.name.split()[0]
            addr['last_name']= addr_rec.name.split()[1] if len(addr_rec.name.split()) == 2 else ''
        addr['address1'] = getattr(addr_rec, 'street') or ''
        addr['address2'] = getattr(addr_rec, 'street2') or ''
        addr['city'] = getattr(addr_rec, 'city') or ''
        addr['province'] = getattr(addr_rec, 'state_id').code if getattr(addr_rec, 'state_id').code else ''
        addr['zip'] = getattr(addr_rec, 'zip') or ''
        addr['country'] = getattr(addr_rec, 'country_id').code if getattr(addr_rec, 'country_id').code else ''
        addr['phone'] = getattr(addr_rec, 'phone') or ''
        return addr
