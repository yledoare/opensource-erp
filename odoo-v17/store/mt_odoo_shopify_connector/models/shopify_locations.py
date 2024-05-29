from odoo import api, fields, models, _
import logging
import shopify
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ShopifyLocations(models.Model):
    _name = 'shopify.location'
    _description = 'Shopify Locations'

    name = fields.Char('Name', required=True)
    shopify_location_id = fields.Char('Shopify Location ID')
    
    is_shopify = fields.Boolean(default=False,string="Is shopify")    
    is_active = fields.Boolean(default=True)
    is_legacy = fields.Boolean('Is Legacy Location')
    
    shopify_instance_id = fields.Many2one('shopify.instance', string="Shopify Instance")    
    import_stock_to_warehouse = fields.Many2one('stock.warehouse', string='Warehouse to Import Stock')

    def init_shopify_session(self, instance_id):
        try:
            session = shopify.Session(instance_id.shop_url, instance_id.api_version, instance_id.admin_api_key)
            return session
        except Exception as error:
            raise UserError(_("Please check your connection and try again"))
        
    def get_all_locations(self, instance_id, limit=100):
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
        
        get_next_page = True
        since_id = 0
        while get_next_page:
            locations = shopify.Location.find(since_id=since_id, limit=limit)

            for location in locations:
                yield location
                since_id = location.id

            if len(locations) < limit:
                get_next_page = False    
    
    def import_locations(self, instance_id):
        for shopify_location in self.get_all_locations(instance_id, limit=100):
            
            location_vals = {
                'shopify_instance_id': instance_id.id,                
                'shopify_location_id': shopify_location.id,
                'name': shopify_location.name,
                'is_shopify':True,
                'is_active':shopify_location.active,
                'is_legacy':shopify_location.legacy,
            }          
            # check if location is present
            location = self.env['shopify.location'].sudo().search(
                [('shopify_instance_id','=',instance_id.id), ('shopify_location_id', '=', shopify_location.id)],limit=1)
            if not location:
                # create location in odoo
                # _logger.info('\n\n\n\n import location data %s \n\n\n\n\n' % location_vals)
                location = self.env['shopify.location'].sudo().create(location_vals)
                self.env.cr.commit()
        