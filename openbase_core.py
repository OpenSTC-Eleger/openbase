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
        self._actions_to_eval.setdefault(self._name,{'':lambda self,cr,uid,record: False})
        self._actions_to_eval[self._name].update(self._actions)
        super(openbaseCore,self).__init__(cr,pool)

class opentest(openbaseCore):
    _name= "openbase.test"
    _columns = {
        'name':fields.char('Name',size=128),
        }
    
    _actions = {
        'print':lambda self,cr,uid,record: record.name <> 'test'
        }

class opentest2(openbaseCore):
    _name = "openbase.test2"
    _columns = {
        'name':fields.char('Name2',size=128),
        'state':fields.selection([('draft','Draft'),('done','Done')], string="State"),
        }

    _actions = {
        'delete':lambda self,cr,uid,record: record.state == 'draft',
        }

opentest2()

class opentest_inherit(openbaseCore):
    _inherit = "openbase.test2"
    _actions = {
        'create':lambda self,cr,uidd,record: record.state == 'done'
        }
opentest_inherit()