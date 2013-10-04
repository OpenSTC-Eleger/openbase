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

class product_category(osv.osv):
    _inherit = "product.category"
    _columns = {
        'is_vehicle':fields.boolean('Is vehicle'),
        'is_equipment': fields.boolean('Is equipment'),
        }
    _defaults = {
        'is_vehicle':False,
        'is_equipment': False,
        }

    #get original parent to inherit to its data 'is_vehicle' and 'is_equipment'
    def check_parent_vehicle_or_equipment(self, cr, uid, vals, context=None):
        parent_id = vals.get('parent_id', False)
        if parent_id:
            parent = self.browse(cr, uid, parent_id, context=context)
            iter_parent_id = parent_id
            #get original parent by recursion
            while parent.parent_id:
                parent = parent.parent_id
            vals['is_vehicle'] = parent.is_vehicle
            vals['is_equipment'] = parent.is_equipment

        return vals

    def create(self, cr, uid, vals, context=None):
        vals2 = self.check_parent_vehicle_or_equipment(cr, uid, vals.copy(), context=context)
        id = super(product_category, self).create(cr, uid, vals2, context=context)
        return id

    def write(self, cr, uid, ids, vals, context=None):
        vals2 = self.check_parent_vehicle_or_equipment(cr, uid, vals.copy(), context=context)
        return super(product_category, self).write(cr, uid, ids, vals2, context=context)

product_category()

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
        reads = self.read(cr, uid, ids, ['name','categ_id'], context=context)
        res = []
        for record in reads:
            #hack to avoid bugs on equipments stored without product_product_id
            if 'name' in record and record['name']:
                name = record['name']
                if record['categ_id']:
                    name =  name + ' / '+ record['categ_id'][1]
                res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)


    _fields_names = {'service_names':'service_ids',
                    'maintenance_service_names':'maintenance_service_ids'}

    #@TODO: move this feature to template model (in another git branch)
    def __init__(self, pool, cr):
        #method to retrieve many2many fields with custom format
        def _get_fields_names(self, cr, uid, ids, name, args, context=None):
            res = {}
            if not isinstance(name, list):
                name = [name]
            for obj in self.browse(cr, uid, ids, context=context):
                #for each field_names to read, retrieve their values
                res[obj.id] = {}
                for fname in name:
                    #many2many browse_record field to map
                    field_ids = obj[self._fields_names[fname]]
                    val = []
                    for item in field_ids:
                        val.append([item.id,item.name_get()[0][1]])
                    res[obj.id].update({fname:val})
            return res

        ret = super(equipment, self).__init__(pool,cr)
        #add _field_names to fields definition of the model
        for f in self._fields_names.keys():
            #force name of new field with '_names' suffix
            self._columns.update({f:fields.function(_get_fields_names, type='char',method=True, multi='field_names',store=False)})
        return ret


    _columns = {
            'immat': fields.char('Imatt', size=128),
            'complete_name': fields.function(_name_get_fnc, type="char", string='Name',method=True, store={'openstc.equipment':[lambda self,cr,uid,ids,ctx={}:ids, ['name','categ_id'], 10]}),
            'product_product_id': fields.many2one('product.product', 'Product', help="", ondelete="cascade"),
            #Service authorized to use equipment
            'service_ids':fields.many2many('openstc.service', 'openstc_equipment_services_rel', 'equipment_id', 'service_id', 'Services'),
            'internal_use':fields.boolean('Internal Use', help='Means that this equipment can be used in intervention, or be the target of intervention request.'),
            #Service owner
            'service':fields.many2one('openstc.service', 'Service'),
            'maintenance_service_ids': fields.many2many('openstc.service','openstc_equipement_maintenance_services_rel','equipment_id','service_id', 'Maintenance services'),

            'marque': fields.char('Marque', size=128),
            'type': fields.char('Type', size=128),
            'usage': fields.char('Usage', size=128),

            'technical_vehicle': fields.boolean('Technical vehicle'),
            'commercial_vehicle': fields.boolean('Commercial vehicle'),

            'small_material': fields.boolean('Small'),
            'fat_material': fields.boolean('Fat'),

            'cv': fields.integer('CV', select=1),
            'purchase_date':fields.date('Date of purchase'),
            'time': fields.integer('Time', select=1),
            'km': fields.integer('Km', select=1),

            'manager_id':fields.many2one('res.users','Responsable'),
            'energy_type':fields.char('Type d\'énergie',size=128),
            'length_amort':fields.integer('Durée d\'amortissement'),
            'purchase_price':fields.float('Prix d\'achat',digits=(6,2)),
            'hour_price':fields.float('Hour price', digits=(4,2)),
            'built_date':fields.date('Built Date'),
            'warranty_date':fields.date('End date of Warranty'),
            #'year': fields.integer('Year', select=1),
            #Calcul total price and liters
            #'oil_qtity': fields.integer('oil quantity', select=1),
            #'oil_price': fields.integer('oil price', select=1),
    }
    _defaults = {
         'type_prod':'materiel',
         'internal_use': False,
        }

    _sql_constraints = [
        ('code_uniq', 'unique (code)', '*code* / The code name must be unique !'),
    ]

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

    #return all services
    def _get_services(self, cr, uid, ids, fields, arg, context):
        res = []
        service_obj = self.pool.get('openstc.service')

        for id in ids:
            #get current team object
            site = self.browse(cr, uid, id, context=context)
            #get list of agents already belongs to team
            services = []
            for service_record in site.service_ids:
                 services.append((service_record.id, service_record.name))

            res.append((id, services))
        return dict(res)


    _actions = {
        'update': lambda self,cr,uid,record, groups_code: 'DIRE' in groups_code or 'MANA' in groups_code,
        'create': lambda self,cr,uid, record, groups_code: 'DIRE' in groups_code or 'MANA' in groups_code,
        'delete': lambda self,cr,uid, record, groups_code: 'DIRE' in groups_code,
    }


    def _get_actions(self, cr, uid, ids, myFields ,arg, context=None):
        #default value: empty string for each id
        ret = {}.fromkeys(ids,'')
        groups_code = []
        groups_code = [group.code for group in self.pool.get("res.users").browse(cr, uid, uid, context=context).groups_id if group.code]

        #evaluation of each _actions item, if test returns True, adds key to actions possible for this record
        for record in self.browse(cr, uid, ids, context=context):
            #ret.update({inter['id']:','.join([key for key,func in self._actions.items() if func(self,cr,uid,inter)])})
            ret.update({record.id:[key for key,func in self._actions.items() if func(self,cr,uid,record,groups_code)]})
        return ret

    _columns = {

            'name': fields.char('Name', size=128, required=True),
            'complete_name': fields.function(_name_get_fnc, type="char", string='Name', method=True, store={'openstc.site':[lambda self,cr,uid,ids,ctx={}:ids, ['name','type'], 10]}),
            'code': fields.char('Code', size=32),
            'type': fields.many2one('openstc.site.type', 'Type', required=True),
            'service_ids':fields.many2many('openstc.service', 'openstc_site_services_rel', 'site_id', 'service_id', 'Services'),
            'service_names' : fields.function(_get_services, method=True,type='many2one', store=False),
            'site_parent_id': fields.many2one('openstc.site', 'Site parent', help='Site parent', ondelete='set null'),
            'length': fields.integer('Lenght'),
            'width': fields.integer('Width'),
            'surface': fields.integer('Surface'),
            'long': fields.float('Longitude'),
            'lat': fields.float('Latitude'),
            'actions':fields.function(_get_actions, method=True, string="Actions possibles",type="char", store=False),

    }

site()




