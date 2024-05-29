# -*- coding: utf-8 -*-
import logging
import shopify

from odoo.exceptions import UserError, MissingError
from odoo import models, api, fields, _
from odoo.tools import config
from bs4 import BeautifulSoup
config['limit_time_real'] = 10000000
config['limit_time_cpu'] = 150


_logger = logging.getLogger(__name__)

class ShopifyProductImage(models.Model):
    _name = 'shopify.product.image'
    _description = 'Shopify Product Images'
    _order = 's_image_pos'

    name = fields.Char(string="Shopify Image Name")
    image_shopify_id = fields.Char(string="Shopify Image ID", store=True)
    url = fields.Char(string="Image URL")
    s_image_pos = fields.Char(string="Shopify Image Position")    
    image = fields.Image(string="Add New Image")    
    shopify_variant_image = fields.Binary(string="Shopify Variant Image", related = "image_variant_id.image_variant_1920" )
    shopify_image = fields.Binary(string="Shopify Image")    
    
    is_auto_create = fields.Boolean(default = False, help="If creating from Export Product")
    is_main_image = fields.Boolean(default = False, string="Set as Main Image")

    product_template_id = fields.Many2one('product.template', string='Product template', ondelete='cascade')    
    image_variant_id = fields.Many2one('product.product', domain="[('product_tmpl_id', '=', product_template_id)]")
    shopify_image_variant_ids = fields.One2many("product.product", "shopify_product_image_id", domain="[('product_tmpl_id', '=', product_template_id)]")#new
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            attachment = ""
            if vals['shopify_image']:
                attachment = vals['shopify_image']
            if vals['is_main_image']:
                vals.update({'s_image_pos' : "1"})
            
            if not attachment and not vals.__contains__('is_auto_create'):
                raise UserError(_("Please attach a image!!!"))
            
            new_vals = super(ShopifyProductImage,self).create(vals)
            
            if not new_vals.is_auto_create:
                ids_list = []
                for variant in new_vals.shopify_image_variant_ids:
                    ids_list.append(int(variant.shopify_variant_id)) 
                    
                self.create_shopify_image(new_vals, attachment, ids_list)
      
    def write(self, vals):
        existing_ids = self.shopify_image_variant_ids.ids
        img_add = False
        super(ShopifyProductImage, self).write(vals)
        if vals.__contains__('shopify_image') or vals.__contains__('shopify_image_variant_ids'):
            if vals.__contains__('shopify_image'):
                img_add = True
            elif vals.__contains__('shopify_image_variant_ids'):
                for id in vals['shopify_image_variant_ids']:
                    if id[0] == 3 or id[0] == 4:
                        img_add = True
                    if id[0] == 6:
                        img_add = False if set(existing_ids).issubset(set(id[2])) else True
            
            result  = self.update_shopify_image(self.product_template_id.shopify_id, self.image_shopify_id, self.product_template_id.shopify_instance_id, add_img = img_add)

            if result:
                self.image_shopify_id = self.image_shopify_id if isinstance(result, bool) else result.id
            return

    def unlink(self):
        for img_rec in self:
            main_image = False
            if img_rec.image_shopify_id:
                self.delete_shopify_image(img_rec.product_template_id.shopify_id, img_rec.image_shopify_id, img_rec.product_template_id.shopify_instance_id)
                
                if img_rec.is_main_image:
                    main_image = True
                    s_product_id = img_rec.product_template_id.id

            super(ShopifyProductImage,img_rec).unlink() 
            
            #reset main image position, if main image deleted 
            if main_image:
                images_data = self.update_or_get_image_position(s_product_id, image_shopify_id=False)
                if images_data:
                    img_id, img_pos = next(iter( images_data.items() ))
                    product_images = self.env['shopify.product.image'].sudo().search([('image_shopify_id', '=', img_id)])
                    product_images.write({'is_main_image': True, 's_image_pos': img_pos})
        return      
                
    @api.constrains("is_main_image")
    def _constrains_is_main_image(self):
        if self.is_main_image:
            product_images = self.env['shopify.product.image'].sudo().search(
                    [('product_template_id', '=', self.product_template_id.id)])
            try:
                images_data = self.update_or_get_image_position(self.product_template_id.id, self.image_shopify_id)
                if images_data:
                    for image in product_images:
                        if image.image_shopify_id and images_data.__contains__(image.image_shopify_id):
                            new_image_pos = images_data[image.image_shopify_id]
                            if image.s_image_pos != str(new_image_pos):
                                image.update({'s_image_pos': new_image_pos })
                            if image.is_main_image and image.id != self.id:
                                image.update({'is_main_image':False})
                                
            except Exception as error:
                _logger.info('\n\n\n\n Image Error !!!! %s\n\n\n ', error)
                raise UserError(_("Error in setting main image!!!"))
                        
    def init_shopify_session(self, instance_id):
        try:
            session = shopify.Session(instance_id.shop_url, instance_id.api_version, instance_id.admin_api_key)
            return session
        except Exception as error:
            raise UserError(_("Please check your connection and try again"))
       
    def create_shopify_image(self, create_vals, attachment, ids_list):
        p_id = create_vals.product_template_id.shopify_id
        instance_id = create_vals.product_template_id.shopify_instance_id  
                 
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
        
        data = {'product_id': p_id,
                'attachment' : attachment,
                'variant_ids' : ids_list}
        
        if create_vals.s_image_pos == "1":
            data.update({'position': 1})
            
        try:
            new_img = shopify.Image.create(data)
            if new_img:
                create_vals.image_shopify_id = new_img.id
                create_vals.url = new_img.src
                create_vals.s_image_pos = new_img.position
                if new_img.position == 1:
                    create_vals.is_main_image = True
            return True
        except Exception as error:
            return False
    
    def update_or_get_image_position(self,p_id, image_shopify_id = False):
        product = self.env['product.template'].sudo().search([('id', '=', p_id)])
        p_id = product.shopify_id
        instance_id = product.shopify_instance_id
                 
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
        
        try:
            if image_shopify_id:
                save_img = shopify.Image()       
                save_img.product_id = p_id
                save_img.id = image_shopify_id
                save_img.position = 1
                save_img.save()
            
            s_image_lists = shopify.Image.find(product_id = p_id)
            s_image_id_lists = {}
            for img_id in s_image_lists:
                s_image_id_lists.update({str(img_id.id) : str(img_id.position)})
            
            return s_image_id_lists
        except Exception as error:
            return False
         
    def update_shopify_image(self, p_id, s_img_id, instance_id, add_img = False):
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
        
        save_img = shopify.Image()
        ids_list = []
        for variant in self.shopify_image_variant_ids:
            ids_list.append(int(variant.shopify_variant_id))
        
        save_img.product_id = p_id
        save_img.id = s_img_id
        save_img.variant_ids = ids_list
        if add_img:
            self.delete_shopify_image(p_id, s_img_id, instance_id)
            save_img.id =""
            
        attachment = ""
        if self.shopify_image:
            attachment = self.shopify_image
        elif self.image_variant_id.image_variant_1920:
            attachment = self.image_variant_id.image_variant_1920
                
        if self.is_image_exist(p_id, s_img_id, instance_id):
            save_img.save()
            return True
        elif attachment:
            self.create_shopify_image( self, attachment, ids_list)
   
    def delete_shopify_image(self, p_id, s_img_id, instance_id):
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
        if self.is_image_exist(p_id, s_img_id, instance_id):    
            del_img = shopify.Image.delete(s_img_id, product_id=p_id)
        return True
            
    def is_image_exist(self, p_id, s_img_id, instance_id):
        session = self.init_shopify_session(instance_id)
        shopify.ShopifyResource.activate_session(session)
        try:
            shopify.Image.find(s_img_id, product_id = p_id)
            return True
        except Exception as error:
            return False
            