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
class openbaseCore(osv.Model):
    _auto = True
    _register = False # not visible in ORM registry, meant to be python-inherited only
    _transient = False # True in a TransientModel
    
    
    _actions_to_eval = {}
    _fields_names_to_eval = {}
    _actions = {}
    _fields_names = {}
    
    def _get_actions(self, cr, uid, ids, myFields ,arg, context=None):
        #default value: empty string for each id
        ret = {}.fromkeys(ids,'')
        #evaluation of each _actions item, if test returns True, adds key to actions possible for this record
        for record in self.browse(cr, uid, ids, context=context):
            ret.update({record.id:','.join([key for key,func in self._actions_to_eval[self._name].items() if func(self,cr,uid,record)])})
        return ret
    
    _columns_to_add = {
        'actions':fields.function(_get_actions, method=True, string="Actions possibles",type="char", store=False),
        }
    def __init__(self, cr, pool):
        self._columns.update(self._columns_to_add)
        self._actions_to_eval.setdefault(self._name,{})
        self._fields_names_to_eval.setdefault(self._name,{})
        
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
        
        super(openbaseCore,self).__init__(cr,pool)
         #add _field_names to fields definition of the model
        for f in self._fields_names.keys():
            #force name of new field with '_names' suffix
            self._columns.update({f:fields.function(_get_fields_names, type='char',method=True, multi='field_names',store=False)})


class opentest(openbaseCore):
    _name= "openbase.test"
    _columns = {
        'name':fields.char('Name',size=128),
        }
    _actions = {
        'print':lambda self,cr,uid,record: record.name <> 'test',
        'read':lambda self,cr,uid,record:record.name <> 'test'
        }
opentest()

class opentest2(openbaseCore):
    
    _name = "openbase.test2"
    _columns = {
        'name':fields.char('Name2',size=128),
        'state':fields.selection([('draft','Draft'),('done','Done')], string="State"),
        'test_ids':fields.many2many('openbase.test','openbase_test2_test_rel','test_id2','test_id','Tests')
        }
    
    _fields_names = {'test_names':'test_ids'}
    _actions = {
        'delete':lambda self,cr,uid,record: record.state == 'draft',
        }

opentest2()

class opentest_inherit(openbaseCore):
    _inherit = "openbase.test2"
    _actions = {
        'create':lambda self,cr,uid,record: record.state == 'done',
        'read':lambda self,cr,uid,record:True
        }
opentest_inherit()