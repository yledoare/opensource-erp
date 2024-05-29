# -*- coding: utf-8 -*-

import io
import json
from odoo import http
from odoo.http import Controller, route, request
from odoo.tools import html_escape
from base64 import b64decode
from odoo.tools.image import image_data_uri, base64_to_image
import logging

_logger = logging.getLogger(__name__)

class WebhookController(http.Controller):
       
    @http.route('/shopify_api/orders/paid', type='json', auth='public', methods=['POST'], csrf=False)
    def get_shopify_orders_paid(self,  **kw):
        
        data = {}
        data = json.loads(http.request.httprequest.data)

        sale_order = http.request.env['sale.order'].sudo().search([('shopify_id', '=', data['id'])], limit=1)
        sale_order.sudo().write({'shopify_status' : data['financial_status']})
        return ('', 200)
                  
    @http.route('/shopify_api/orders/updated', type='json', auth='public', methods=['POST'], csrf=False)
    def get_shopify_orders_updated(self,  **kw):
        
        data = {}
        data = json.loads(http.request.httprequest.data)
        _logger.info('\n\n\n orders/updated WebhookController JSON %s \n\n\n\n' % data) 
        
        sale_order = http.request.env['sale.order'].sudo().search([('shopify_id', '=', data['id'])], limit=1)
        sale_order.sudo().write({'shopify_status' : data['financial_status']})
        return ('', 200)

    @http.route('/shopify_api/orders/fulfilled', type='json', auth='public', methods=['POST'], csrf=False)
    def get_shopify_orders_fulfilled(self,  **kw):
        
        data = {}
        data = json.loads(http.request.httprequest.data)
        _logger.info('\n\n\n orders/fulfilled WebhookController JSON %s \n\n\n\n' % data) 
        
        sale_order = http.request.env['sale.order'].sudo().search([('shopify_id', '=', data['id'])], limit=1)
        sale_order.sudo().write({'shopify_fulfillment_status' : data['fulfillment_status']})
        
        for fulfillment in data['fulfillments']:
            dict_fo = {}
            dict_fo['shopify_id'] = fulfillment['id']
            dict_fo['shopify_order_id'] = fulfillment['order_id']
            dict_fo['shopify_order_no'] = fulfillment['name']
            dict_fo['location_id'] = fulfillment['location_id']
            dict_fo['shopify_service'] = fulfillment['service']
            dict_fo['shopify_status'] = fulfillment['status']
            dict_fo['tracking_company'] = fulfillment['tracking_company']
            dict_fo['tracking_number'] = fulfillment['tracking_number']
            dict_fo['tracking_url'] = fulfillment['tracking_url']
            dict_fo['is_exported'] = True
            dict_fo['so_id'] = sale_order.id
            fulfillment_order = http.request.env['shopify.order.fulfillment'].sudo().search([('shopify_id', '=', fulfillment['id'])], limit=1)            
            if not fulfillment_order:
                fo_obj = http.request.env['shopify.order.fulfillment'].sudo().create(dict_fo)
                if fo_obj :
                    for line_item in fulfillment['line_items']:
                        dict_fo_li = {}
                        dict_fo_li['f_line_item_id'] = line_item['id']
                        dict_fo_li['f_line_item_name'] = line_item['name']
                        dict_fo_li['f_service'] = line_item['fulfillment_service']
                        dict_fo_li['f_status'] = line_item['fulfillment_status']
                        dict_fo_li['price'] = float(line_item['price'])
                        dict_fo_li['shopify_product_id'] = line_item['product_id']
                        dict_fo_li['shopify_variant_id'] = line_item['variant_id']
                        dict_fo_li['quantity'] = line_item['quantity']
                        dict_fo_li['fulfillment_id'] = fo_obj.id
                        
                        fo_line = http.request.env['shopify.order.fulfillment.line'].sudo().search([('f_line_item_id', '=', line_item['id'])], limit=1)
                        if not fo_line:
                            http.request.env['shopify.order.fulfillment.line'].sudo().create(dict_fo_li)
                        else:
                            fo_line.write(dict_fo_li)
            else:
                fulfillment_order.write(dict_fo)

        return ('', 200)
               
    @http.route('/shopify_api/draft_orders/update', type='json', auth='public', methods=['POST'], csrf=False)
    def get_shopify_draft_orders_updated(self,  **kw):
        
        data = {}
        data = json.loads(http.request.httprequest.data)
        _logger.info('\n\n\n draft_orders/update WebhookController JSON %s \n\n\n\n' % data) 
        
        sale_order = http.request.env['sale.order'].sudo().search([('shopify_id', '=', data['id'])], limit=1)
        if data['order_id']:
            sale_order.sudo().write({'shopify_id' : data['order_id'], 'is_shopify_draft_order': False})
    
        return ('', 200)
                                                           
class ImageController(http.Controller):        
    @http.route('/shopify/images/<int:id>/<name>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_shopify_data(self, id, name):
        
        image = http.request.env['product.product'].sudo().search([('id', '=', id)], limit=1)
        raw_image = base64_to_image(image.image_1920)
        
        return http.Response(response = b64decode(image.image_1920.decode("utf-8")), 
                             status=200,
                             content_type=self.get_image_type(raw_image.format)
                             )
     
    def get_image_type(self, img_type):
        
        image_type = {
                    "JPEG"  : "image/jpeg",
                    "PNG"   : "image/png",
                    "WEBP"   : "image/webp",
                    }
        if(image_type.__contains__(img_type)):
            return image_type[img_type]
        else:
            return "image/png"