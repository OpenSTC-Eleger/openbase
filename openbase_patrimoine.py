# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenBase module for OpenERP, Description
#    Copyright (C) 200X Company (<http://website>) author
#
#    This file is a part of ModuleName
#
#    OpenBase is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    OpenBase is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields

class product_product(osv.osv):
    _name = "product.product"
    _inherit = "product.product"
    _description = "Produit"

    _columns = {
        'type_prod':fields.selection([('materiel','Matériel'),('fourniture','Fourniture Achetable'),('site','Site')], 'Type de Produit'),
        'openstc_reservable':fields.boolean('Reservable', help='Indicates if this ressource can be reserved or not by tiers'),
        'openstc_maintenance':fields.boolean('Maintenance ?', help='Indicates if this ressource can be associated to contracts for maintenance'),
         }
    _defaults = {
        'openstc_reservable':lambda *a: False,
        'openstc_maintenance':lambda *a: False,
    }
 
product_product()
#----------------------------------------------------------
# Equipments
#----------------------------------------------------------

class equipment(osv.osv):
    _name = "openstc.equipment"
    _description = "openstc.equipment"
    #_inherit = 'product.product'
    _inherits = {'product.product': "product_product_id"}

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','type'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['type']:
                name =  name + ' / '+ record['type']
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _columns = {
            'immat': fields.char('Imatt', size=128),
            'complete_name': fields.function(_name_get_fnc, type="char", string='Name'),
            'product_product_id': fields.many2one('product.product', 'Product', help="", ondelete="cascade"),
            #Service authorized for use equipment
            'service_ids':fields.many2many('openstc.service', 'openstc_equipment_services_rel', 'equipment_id', 'service_id', 'Services'),
            #Service owner
            'service':fields.many2one('openstc.service', 'Service'),

            'marque': fields.char('Marque', size=128),
            'type': fields.char('Type', size=128),
            'usage': fields.char('Usage', size=128),

            'technical_vehicle': fields.boolean('Technical vehicle'),
            'commercial_vehicle': fields.boolean('Commercial vehicle'),

            'small_material': fields.boolean('Small'),
            'fat_material': fields.boolean('Fat'),

            'cv': fields.integer('CV', select=1),
            'year': fields.integer('Year', select=1),
            'time': fields.integer('Time', select=1),
            'km': fields.integer('Km', select=1),
                        
            'manager_id':fields.many2one('res.users','Responsable'),
            'energy_type':fields.char('Type d\'énergie',size=128),
            'length_amort':fields.integer('Durée d\'amortissement'),
            'purchase_price':fields.float('Prix d\'achat',digits=(6,2)),


            #Calcul total price and liters
            #'oil_qtity': fields.integer('oil quantity', select=1),
            #'oil_price': fields.integer('oil price', select=1),
    }
    _defaults = {
         'type_prod':'materiel',

        }

equipment()

#----------------------------------------------------------
# Sites
#----------------------------------------------------------

class site_type(osv.osv):
    _name = "openstc.site.type"
    _description = "openstc.site.type"

    _columns = {
            'name': fields.char('Name', size=128, required=True),
            'code': fields.char('Code', size=32, required=True),
    }
site_type()

class site(osv.osv):
    _name = "openstc.site"
    _description = "openstc.site"

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','type'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['type']:
                name =  name + ' / '+ record['type'][1]
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _columns = {

            'name': fields.char('Name', size=128, required=True),
            'complete_name': fields.function(_name_get_fnc, type="char", string='Name'),
            'code': fields.char('Code', size=32),
            'type': fields.many2one('openstc.site.type', 'Type', required=True),
            'service_ids':fields.many2many('openstc.service', 'openstc_site_services_rel', 'site_id', 'service_id', 'Services'),
            'site_parent_id': fields.many2one('openstc.site', 'Site parent', help='Site parent', ondelete='set null'),
            'lenght': fields.integer('Lenght'),
            'width': fields.integer('Width'),
            'surface': fields.integer('Surface'),
            'long': fields.float('Longitude'),
            'lat': fields.float('Latitude'),
    }

site()




