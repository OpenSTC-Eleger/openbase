# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (C) 2012 SICLIC http://siclic.fr
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
#############################################################################
from openbase_core import OpenbaseCore
from osv import osv, fields
import netsvc

## This object define a "relative validator"
## Linked with an openstc.service and a selection field, it permits to retrieve a user according to the services records
## It's mainly used in purchases wkf, budgets or interventions to setup the validators of a specific wkf
## it provides method to automatically compute its data (using existing openstc.service's) and to retrieve the corresponding user
## in order to use it in wkf, another object (openbase.validation) is available to provide a sub-wkf fully usable without re-implementing it
class OpenbaseValidationItem(OpenbaseCore):
    _name = 'openbase.validation.item'
    
    ## @return: list of 2-items tuples, name pattern is : "service_name - role" 
    def name_get(self, cr, uid, ids, context=None):
        ret = []
        roles = dict(self.get_role_values(cr, uid, context=context))
        for validation in self.browse(cr, uid, ids, context=context):
            ret.append((validation.id, u'%s - %s' % (validation.service_id.name, roles.get(validation.role, u''))))
        return ret
    
    ## @return: list of tuples defing available selection of the field 'role'
    ## can be override to add more roles
    def get_role_values(self, cr, uid, context=None):
        return [('manager', 'Responsable'), ('elu', 'Elu')]
    
    def _get_role_values(self, cr, uid, context=None):
        return self.get_role_values(cr, uid, context=context)
    
    def _get_name(self, cr, uid, ids, name, args, context=None):
        return dict(self.name_get(cr, uid, ids, context=context))
    
    def _get_user(self, cr, uid, ids, name, args, context=None):
        ret = {}.fromkeys(ids, False)
        switch = {'manager': 'manager_id', 'elu': 'elu_id'}
        for validation in self.browse(cr, uid, ids, context=context):
            #retrieve which field of the service to read
            field = switch.get(validation.role, False)
            #retrieve the user set in the service
            user = validation.service_id[field] if field else False
            ret[validation.id] = user.id if user else False
        return ret
    
    _columns = {
        'name': fields.function(_get_name, type='char', string='Name', method=True, store=True),
        'service_id':fields.many2one('openstc.service', 'Service Validator', required=True),
        'role': fields.selection(_get_role_values, 'role of the validator (as defined in the service)', required=True),
        'user_id':fields.function(_get_user, type='many2one', relation='res.users', string='Current Validator', method=True),
    }
    
    ## create all the available validation items (check if some are already created to avoid duplicates)
    def compute_data(self, cr, uid, context=None):
        to_create = []
        service_obj = self.pool.get('openstc.service')
        services = service_obj.search(cr, uid, [], context=context)
        roles = dict(self.get_role_values(cr, uid, context=context)).keys()
        #check existing validation-items
        validations = self.browse(cr, uid, self.search(cr, uid, [], context=context), context=context)
        existing_validations = [(v.service_id.id, v.role) for v in validations]
        #retrieve only non-existing validation-items
        for r in roles:
            for s in services:
                key = (s,r)
                if key not in existing_validations:
                    self.create(cr, uid, {'service_id':key[0], 'role':key[1]},context=context)
        return True
    
OpenbaseValidationItem()

## This object is used to manage validation wkf
## it can be linked to an object to add a validation system (by adding a subflow in the default wkf) 
class OpenbaseValidation(OpenbaseCore):
    
    ## @return: validation.item if uid corresponds to a waiting_validation_item, else return False
    def _get_current_user_item(self, cr, uid, ids, name, args, context=None):
        ret = {}.fromkeys(ids, False)
        for v in self.browse(cr, uid, ids, context=context):
            for item in v.waiting_validation_item_ids:
                user = item.user_id
                if user and user.id == uid:
                    ret[v.id] = item.id
        return ret
    
    _name = 'openbase.validation'
    _columns = {
        'name': fields.char('Origin', size=64, required=True),
        'validation_type': fields.selection([('and', 'ET'), ('or', 'OU'), ('next', 'Ensuite')], 'Validation type'),
        
        'validation_item_ids':fields.many2many('openbase.validation.item', 'validation_validation_item_rel', 'validation_id', 'item_id', 'Validations'),
        'waiting_validation_item_ids': fields.many2many('openbase.validation.item', 'validation_waiting_validation_item_rel', 'validation_id', 'item_id', 'Waiting Validations'),
        'validation_log_ids': fields.one2many('openbase.validation.log', 'validation_id', 'Validations History'),
        
        'confirm_note': fields.text('Confirm note'),
        'refuse_note': fields.text('Refuse note'),
        
        'current_user_item_id':fields.function(_get_current_user_item, method=True, type='many2one', relation='openbase.validation.item', string="Current user Role"),
        'state': fields.selection([('wait','Wait a validation'), ('refused', 'Refused'), ('done', 'Validated')]),
    }

    _defaults = {
        'validation_type': lambda *a: 'next',
        'state': lambda *a: 'wait',
        'name': lambda *a: '/' 
    }

    ## Notify user(s) form which we are waiting a validation
    ## @param mail_template: the email.template used to send mail to the waiting validators wanted to be mailed
    def notify_validators(self, cr, uid, ids, mail_template='wait', context=None):
        #TODO
        return True

    ## if the uid is authorized to validate, pop the corresponding validation_item from the waiting validation, and create a log
    def apply_decision(self, cr, uid, ids, action):
        for v in self.browse(cr, uid, ids):
            #check if uid is authorized to validate
            item = v.current_user_item_id
            if item:
                #the fields 'confirm_note', 'refuse_note' are used to supply the note written by the user
                #we use it because wkf do not use 'context', and the validation.log is not created at the same time the *_note is written
                note = ''
                key_note = action + '_note' #even us can have keynotes ! ;)
                if hasattr(v,key_note):
                    note = v[key_note]
                    v.write({key_note: ''})
                #user authorized, create a log, and remove him from the waiting validations
                v.write({'waiting_validation_item_ids': [(3,item.id)],
                         'validation_item_ids': [(3,item.id)],
                         'validation_log_ids': [(0,0,{'note':note,
                                                     'validation_item_id':item.id,
                                                     'user_id': uid,
                                                     'state': action})]
                         })
            else:
                raise osv.except_osv('401', 'This user is not authorized to confirm this validation')
        return True
    
    ## write the first value of "waiting_validation_item_ids" according to validation_type.
    ## If type is 'next', write only the first validation.item, else, write all the validation.item
    def wkf_draft(self, cr, uid, ids):
        for v in self.browse(cr, uid, ids):
            item_ids = []
            if v.validation_item_ids:
                if v.validation_type == 'next':
                    item_ids.append((4,v.validation_item_ids[0].id))
                else:
                    item_ids.extend([(4,x.id) for x in v.validation_item_ids])
                v.write({'waiting_validation_item_ids': item_ids})
        return True
    
    def wkf_wait(self, cr, uid, ids):
        #BE CAREFUL: do not send more than once a mail to user
        for v in self.browse(cr, uid, ids):
            #if validation_type is not 'next', users have already been notified when a log exists (not the better way to know if a this is the first time we pass in this activity)
            if v.validation_type == 'next' or not v.validation_log_ids:
                self.notify_validators(cr, uid, ids)
        self.write(cr, uid, ids, {'state':'wait'})
        return True
    
    def wkf_confirm(self, cr, uid, ids):
        self.apply_decision(cr, uid, ids, 'confirm')
        return True
    
    ## Remove other waiting validations to make the wkf done
    def wkf_do_or(self, cr, uid, ids):
        for v in self.browse(cr, uid, ids):
            v.write({'validation_item_ids':[(5,)],
                    'waiting_validation_item_ids':[(5,)]})
        return True
    
    ## Set the next validator (if there is other waiting validations)
    def wkf_do_next(self, cr, uid, ids):
        for v in self.browse(cr, uid, ids):
            if v.validation_item_ids:
                v.write({'waiting_validation_item_ids': [(4,v.validation_item_ids[0].id)]})
        return True
    
    ## Remove other waiting validations and perform refusal of the validation process (send mail to all others waiting validations)
    def wkf_refused(self, cr, uid, ids):
        self.apply_decision(cr, uid, ids, 'refuse')
        self.notify_validators(cr, uid, ids, mail_template='refused')
        self.write(cr, uid, ids, {'state':'refused',
                                  'validation_item_ids':[(5,)],
                                  'waiting_validation_item_ids':[(5,)]})
        return True
    
    ## Send mail to all other waiting validations (to tell them they don't have to check anymore)
    def wkf_done(self, cr, uid, ids):
        self.notify_validators(cr, uid, ids, mail_template='done')
        self.write(cr, uid, ids, {'state':'done'})
        return True
    
    def write(self, cr, uid, ids, vals, context=None):
        state = False
        if 'wkf_evolve' in vals:
            state = vals.pop('wkf_evolve')
        super(OpenbaseValidation, self).write(cr, uid, ids, vals, context=context)
        if state:
            wkf_service = netsvc.LocalService('workflow')
            for id in ids:
                wkf_service.trg_validate(uid, 'openbase.validation', id, state, cr)
        return True
    
OpenbaseValidation()

class OpenbaseValidationLog(OpenbaseCore):
    _name = 'openbase.validation.log'
    _columns = {
        'note': fields.text('Note'),
        'validation_id': fields.many2one('openbase.validation', 'Validation'),
        'validation_item_id': fields.many2one('openbase.validation.item', 'Validation', required=True),
        'user_id': fields.many2one('res.users', 'Validator name', required=True),
        'date': fields.datetime('Date', required=True),
        'state': fields.selection([('confirm','Confirm'), ('refuse','Refuse')], required=True)
    }
    
    _defaults = {
        'date': fields.datetime.now
    }
    
OpenbaseValidationLog()

class OpenstcService(OpenbaseCore):
    
    _inherit = 'openstc.service'
    _columns = {
        'purchase_validation_type': fields.selection([('and', 'ET'), ('or', 'OU'), ('next', 'Ensuite')], 'Validation type'),
        'purchase_validation_item_ids':fields.many2many('openbase.validation.item', 'purchase_validation_validation_item_rel', 'validation_id', 'item_id', 'Validations'),
    }
    
    _defaults = {
        'purchase_validation_type': lambda *a: 'next',
    }
OpenstcService()
    