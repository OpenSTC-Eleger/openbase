# -*- coding: utf-8 -*-

##############################################################################
#
#    OpenBase module for OpenERP, module OpenBase
#    Copyright (C) 2013 SICLIC (<http://siclic.fr>) Bruno PLANCHER
#
#    This file is a part of module OpenBase
#
#    module OpenBase is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, ors_user
#    (at your option) any later version.
#
#    module OpenBase is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from osv import fields, osv
#Core abstract model to add SICLIC custom features, such as actions rights calculation (to be used in SICLIC custom GUI)
class OpenbaseCore(osv.Model):
    _auto = True
    _register = False # not visible in ORM registry, meant to be python-inherited only
    _transient = False # True in a TransientModel


    _actions_to_eval = {}
    _fields = {}
    _fields_names_to_eval = {}
    _actions = {}
    _fields_names = {}

    def _get_actions(self, cr, uid, ids, myFields ,arg, context=None):
        #default value: empty string for each id
        ret = {}.fromkeys(ids,'')
        groups_code = []
        groups_code = [group.code for group in self.pool.get("res.users").browse(cr, uid, uid, context=context).groups_id if group.code]

        for record in self.browse(cr, uid, ids, context=context):
            ret.update({record.id:[key for key,func in self._actions_to_eval[self._name].items() if func(self,cr,uid,record,groups_code)]})
        return ret

    _columns_to_add = {
        'actions':fields.function(_get_actions, method=True, string="Actions possibles",type="char", store=False),
        }

    """
    @param uid: user who whants the metadata
    @return: dict containing number of records (that user can see),
            model fields definition (another dict with field as key and list as definition),
            @todo: filters authorized for this user too ?
            in example : {'count':55, 'fields':{'name':{'string':'Kapweeee', type:'char', 'required':True}}, 'saved_filters': [TODO]}
    """
    def getModelMetadata(self, cr, uid, context=None):
        ret = {'count':0, 'fields':{}}
        #Comment count because special count from client (swif)
        #ret['count'] = self.search(cr, uid, [], count=True, context=context)
        #dict containing default keys to return, even if value is False (OpenERP does not return a key where the val is False)
        mandatory_vals = {'type':False,'required':False,'select':False,'readonly':False, 'help':False}
        #list containing key to return if set
        authorized_vals = ['selection','domain']
        vals_to_retrieve = authorized_vals + mandatory_vals.keys()

        #Get model id
        ret['model_id']  = self.pool.get('ir.model').search(cr, uid, [('model','=',self._name)])[0]


        #for each field, returns all mandatory fields, and return authorized fields if set
        for f, dict_vals in self.fields_get(cr, uid, context=context).items():
            final_val = mandatory_vals.copy()
            for key,val in dict_vals.items():
                if key in vals_to_retrieve:
                    final_val.update({key:val})
            ret['fields'].update({f:final_val})

        return ret

    def __init__(self, cr, pool):
        self._columns.update(self._columns_to_add)
        self._actions_to_eval.setdefault(self._name,{})
        self._fields_names_to_eval.setdefault(self._name,{})
        self._fields.setdefault(self._name,{})

        self._actions_to_eval[self._name].update(self._actions)
        self._fields_names_to_eval[self._name].update(self._fields_names)
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
                    field_ids = obj[self._fields_names_to_eval[self._name][fname]]
                    val = []
                    for item in field_ids:
                        val.append([item.id,item.name_get()[0][1]])
                    res[obj.id].update({fname:val})
            return res

        super(OpenbaseCore,self).__init__(cr,pool)
         #add _field_names to fields definition of the model
        for f in self._fields_names.keys():
            #force name of new field with '_names' suffix
            self._columns.update({f:fields.function(_get_fields_names, type='char',method=True, multi='field_names',store=False)})

    def fields_get(self, cr, uid, fields=None, context=None):
        if len(self._fields[self._name]) == 0 :
            self._fields[self._name] = super(OpenbaseCore, self).fields_get(cr, uid, fields, context)
        return self._fields[self._name]

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        for s in args :
            if 'name' in s :
                #Search with complete_name
                if 'complete_name' in self.fields_get(cr, uid, context=context):
                    args.remove(s)
                    s[0] = 'complete_name'
                    args.extend([s])
                    break
        return super(OpenbaseCore, self).search(cr, uid, args, offset, limit, order, context, count)
