# -*- coding: utf-8 -*-

##############################################################################
#
#    OpenCivil module for OpenERP, module Etat-Civil
#    Copyright (C) 200X Company (<http://website>) pyf
#
#    This file is a part of penCivil
#
#    penCivil is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, ors_user
#    (at your option) any later version.
#
#    penCivil is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from osv.orm import browse_record, browse_null
from osv import osv, fields
import re
import unicodedata
from reportlab.lib.set_ops import intersect
from datetime import datetime
#----------------------------------------------------------
# Services
#----------------------------------------------------------

def _test_params(params, keys):
    param_ok = True
    for key in keys :
        if params.has_key(key) == False :
            param_ok = False
        else :
            if params[key]==None or params[key]=='' or params[key]==0 :
                param_ok = False
    return param_ok

class service(osv.osv):
    _name = "openstc.service"
    _description = "openstc.service"
    _rec_name = "name"
    _parent_name = "service_id"

    _actions = {
        'create':lambda self,cr,uid,record, groups_code: 'MANA' in groups_code or 'DIRE' in groups_code,
        'update':lambda self,cr,uid,record, groups_code: 'MANA' in groups_code or 'DIRE' in groups_code,
        'delete':lambda self,cr,uid,record, groups_code: 'DIRE' in groups_code,
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
            'favcolor':  fields.char('Name', size=128),
            'code': fields.char('Code', size=32, required=True),
            'service_id':fields.many2one('openstc.service', 'Service Parent'),
            'technical': fields.boolean('Technical service'),
            'manager_id': fields.many2one('res.users', 'Manager'),
            'user_ids': fields.one2many('res.users', 'service_id', "Users"),
            'team_ids': fields.many2many('openstc.team', 'openstc_team_services_rel', 'service_id','team_id','Teams'),
            'site_ids':fields.many2many('openstc.site', 'openstc_site_services_rel', 'service_id', 'site_id', 'Sites'),
            'actions':fields.function(_get_actions, method=True, string="Actions possibles",type="char", store=False),
            'partner_id':fields.many2one('res.partner','Partner'),
    }
    
    def link_with_partner(self, cr, uid, id, context=None):
        service = self.browse(cr, uid, id, context=None)
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        vals = {
        'name':service.name,
        'parent_id':user.company_id.partner_id and user.company_id.partner_id.id or False,
        'is_department':True
        }
        partner_id = self.pool.get('res.partner').create(cr, uid, vals, context=context)
        service.write({'partner_id':partner_id},context=context)
        return True
    
    def create(self, cr, uid, vals, context=None):
        ret = super(service, self).create(cr, uid, vals, context=context)
        self.link_with_partner(cr, uid, ret, context=context)
        return ret

    
    _sql_constraints = [
        ('code_uniq', 'unique (code)', '*code* / The code name must be unique !')
    ]

service()

#----------------------------------------------------------
# Partner
#----------------------------------------------------------

class openstc_partner_type(osv.osv):
    _name = "openstc.partner.type"
    _description = "openstc.partner.type"
    _rec_name = "name"


    _actions = {
        'delete':lambda self,cr,uid,record, groups_code: 'DIRE' in groups_code,
        'update': lambda self,cr,uid,record, groups_code: 'MANA' in groups_code or 'DIRE' in groups_code,
        'create': lambda self,cr,uid,record,groups_code: 'MANA' in groups_code or 'DIRE' in groups_code,
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
            'code': fields.char('Code', size=32, required=True),
            'claimers': fields.one2many('res.partner', 'type_id', "Claimers"),
            'actions':fields.function(_get_actions, method=True, string="Actions possibles",type="char", store=False),
            'parent_id':fields.many2one('openstc.partner.type', 'Parent type'),
    }
    _sql_constraints = [
        ('code_uniq', 'unique (code)', '*code* / The code name must be unique !')
    ]
openstc_partner_type()

class openstc_partner_activity(osv.osv):
    _name = "openstc.partner.activity"

    def _name_get_func(self, cr, uid, ids, name, args, context=None):
        ret = {}
        for item in self.name_get(cr, uid, ids, context=context):
            ret[item[0]]=item[1]
        return ret


    _columns = {
        'name':fields.char('Activity name',size=128, required=True),
        'parent_activity_id':fields.many2one('openstc.partner.activity','Parent Activity'),
        'complete_name':fields.function(_name_get_func, string='Activity name',type='char', method=True, store={'openstc.partner.activity':[lambda self,cr,uid,ids,ctx={}:ids, ['name','parent_id'],10]}),
        }

    def recursive_name_get(self, cr, uid, record, context=None):
        name = record.name
        if record.parent_activity_id:
            name = self.recursive_name_get(cr, uid, record.parent_activity_id, context=context) + ' / ' + name
            return name
        return name

    def name_get(self, cr, uid, ids, context=None):
        ret = []
        for activity in self.browse(cr, uid, ids, context=None):
            #get parent recursively
            name = self.recursive_name_get(cr, uid, activity, context=context)
            ret.append((activity.id,name))
        return ret

    def name_search(self, cr, uid, name='', args=[], operator='ilike', context={}, limit=80):
        if name:
            args.extend([('name',operator,name)])
        ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context=context)

openstc_partner_activity()


class res_partner(osv.osv):
     _inherit = "res.partner"

     _columns = {
        'activity_ids':fields.many2many('openstc.partner.activity','openstc_partner_activity_rel','partner_id','activity_id', 'Supplier Activities'),
        'type_id': fields.many2one('openstc.partner.type', 'Type'),
        'is_department':fields.boolean('is department'),

 }
res_partner()

#claimer linked with a res.users
class res_partner_address(osv.osv):
    _description ='Partner Addresses st'
    _name = 'res.partner.address'
    _inherit = "res.partner.address"
    _order = 'type, name'


    _columns = {
        'user_id': fields.many2one('res.users', 'User'),
    }

    def create(self, cr, uid, data, context=None):
        res = super(res_partner_address, self).create(cr, uid, data, context)
        self.create_account(cr, uid, [res], data, context)
        return res



    def write(self, cr, uid, ids, data, context=None):

        user_obj = self.pool.get('res.users')
        partner_address = self.read(cr, uid, ids[0],
                                    ['user_id'],
                                    context)

        if partner_address.has_key('user_id')!= False :
            if partner_address['user_id'] != False :
                user = user_obj.browse(cr, uid, partner_address['user_id'][0], context=context)
                if user.id != 0 and  _test_params(data, ['login','password','name','email'])!= False :
                    user_obj.write(cr, uid, [user.id], {
                                    'name': data['name'],
                                    'firstname': data['name'],
                                    'user_email': data['email'],
                                    'login': data['login'],
                                    'new_password': data['password'],
                            }, context=context)

            else :
                self.create_account(cr, uid, ids, data, context)



        res = super(res_partner_address, self).write(cr, uid, ids, data, context)
        return res

    def create_account(self, cr, uid, ids, params, context):
        if _test_params(params, ['login','password','name','email'])!= False :

            company_ids = self.pool.get('res.company').name_search(cr, uid, name='STC')
            if len(company_ids) == 1:
                params['company_id'] = company_ids[0][0]
            else :
                params['company_id'] = 1;

            user_obj = self.pool.get('res.users')

            group_obj = self.pool.get('res.groups')
            #Get partner group (code group=PART)
            group_id = group_obj.search(cr, uid, [('code','=','PART')])[0]
            user_id = user_obj.create(cr, uid,{
                    'name': params['name'],
                    'firstname': params['name'],
                    'user_email': params['email'],
                    'login': params['login'],
                    'new_password': params['password'],
                    'groups_id' : [(6, 0, [group_id])],
                    })
            self.write(cr, uid, ids, {
                    'user_id': user_id,
                }, context=context)


res_partner_address()

class groups(osv.osv):
    _name = "res.groups"
    _description = "Access Groups"
    _inherit = "res.groups"
    _rec_name = 'full_name'

    _columns = {
        'code': fields.char('Code', size=128),
        'perm_request_confirm' : fields.boolean('Demander la Confirmation'),
    }

groups()

class users(osv.osv):
    _name = "res.users"
    _description = "res users st"
    _inherit = "res.users"
    _rec_name = "name"

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','firstname'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['firstname']:
                name =  record['firstname'] + '  '+  name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    #Calculates if agent belongs to 'arg' code group
    def _get_group(self, cr, uid, ids, fields, arg, context):
         res = {}
         user_obj = self.pool.get('res.users')
         group_obj = self.pool.get('res.groups')

         for id in ids:
            user = user_obj.read(cr, uid, id,['groups_id'],context)
            #Get 'arg' group (MANAGER or DIRECTOR)
            group_ids = group_obj.search(cr, uid, [('code','=', arg),('id','in',user['groups_id'])])
            res[id] = True if len( group_ids ) != 0 else False
         return res

    def get_menu_formatted(self, cr, uid, context=None):
        def parseToUrl(val):
            regexp_remove = re.compile("[\-:]+")
            regexp_dot = re.compile(" ")
            if not isinstance(val,(str, unicode)):
                return val
            uval = val
            if not isinstance(uval, unicode):
                uval = val.decode('utf-8')
            ret = []
            items = regexp_remove.sub('', uval)
            items = regexp_dot.split(items)
            for item in items:
                ret.append(''.join([x for x in unicodedata.normalize('NFKD',item) if unicodedata.category(x)[0] in ('L','N')]))
            ret = '-'.join(ret)
            return ret.lower()
        
        """
        @param item: current item to retrieve children menuitem recursively
        @param menu_dict: dict of all of the menuitems to be assembled
        """
        def get_menu_hierarchy(item,menu_dict):
            ret = []
            for child_id in item['child_id']:
                child = menu_dict.get(child_id)
                child.update({'tag':parseToUrl(child['name'])})
                child.update({'children':get_menu_hierarchy(child,menu_dict)})
                ret.append(child)
            return ret
        #get the user context (because method is called without context, by default)
        if not context or context is None:
            context = self.pool.get("res.users").context_get(cr, uid, context=context)
        data_obj = self.pool.get('ir.model.data')
        menu_obj = self.pool.get('ir.ui.menu')
        #retrieve all OpenSTC modules, because stc users have only access to root OpenSTC menus and not any other OpenERP menu
        menu_root_ids = menu_obj.search(cr, uid, [('parent_id','=', False)],context=context)
        #default value to return if not any menu is found (bad user configuration)
        final_menu = {}
        if menu_root_ids:
            menu_ids = menu_obj.search(cr, uid, [('id','child_of',menu_root_ids)], context=context)
            #and retrieve corresponding ir.model.data to know in which module they have been created
            menu_data_ids = data_obj.search(cr, uid, [('model','=','ir.ui.menu'),('res_id','in',menu_ids)])
            menu_data = data_obj.read(cr, uid, menu_data_ids, ['module','res_id'],context=context)
            menu_data = dict([(item['res_id'],item['module']) for item in menu_data ])
            menu = menu_obj.read(cr, uid, menu_ids, ['id','name','parent_id','child_id'], context=context)
            menu = sorted(menu, key=lambda item: item['parent_id'])
            menu_dict = {}
            #for each menuitem of OpenSTC, add a slugify-like tag, and a tag-module to be retrieved according to module
            for item in menu:
                item.update({'tag':parseToUrl(item['name']),
                             'tag_module':menu_data.get(item['id'],'')})
                menu_dict.update({item['id']:item})
            
            for item in menu:
                if not item['parent_id']:
                    #retrieve only STC menus
                    #if menu_stc and item['id'] in root_openstc_menu_dict.keys():    
                    item.update({'children':get_menu_hierarchy(item, menu_dict),
                                 #'module':root_openstc_menu_map.get(root_openstc_menu_dict.get(item['id']))
                                 })
                    final_menu.update({item['tag']:item})
        #print final_menu
        return final_menu

    _actions = {
        'create':lambda self,cr,uid,record, groups_code: 'MANA' in groups_code or 'DIRE' in groups_code,
        'update':lambda self,cr,uid,record, groups_code: 'MANA' in groups_code or 'DIRE' in groups_code,
        'delete':lambda self,cr,uid,record, groups_code: 'DIRE' in groups_code,
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

    #get OpenSTC groups and retrieve the higher one the user has
    def _get_current_group(self, cr, uid, ids, name ,args, context=None):

        def weight_hierarchy(current_group, groups, i=0):
            current_group['hierarchy_sequence'] = i + 1
            groups_implie_current = [g for g in groups if g['implied_ids'] and current_group['id'] in g['implied_ids']]
            for g in groups_implie_current:
                weight_hierarchy(g, groups, i+1)
            return
        ret = {}.fromkeys(ids,False)
        #first, order groups by their 'weight' in hierarchy
        #i begin by getting all openstc Groups
        groups_id = self.pool.get("res.groups").search(cr, uid, [('name','ilike','openstc')], context=context)
        groups = self.pool.get("res.groups").read(cr, uid, groups_id, ['name','implied_ids'])
        #and i order them, starting with lower of them (the ones which don't implied others)
        first_groups = [g for g in groups if not g['implied_ids'] or not intersect(g['implied_ids'], groups_id)]
        for g in first_groups:
            weight_hierarchy(g, groups)

        #and loop groups (ordered by higher weight) to check groups_id of each user
        users = self.pool.get("res.users").read(cr, uid, ids,['groups_id'])
        for g in sorted(groups, key=lambda(item):item['hierarchy_sequence'], reverse=True):
            for user in users:
                #if user has this group
                if g['id'] in user['groups_id']:
                    #link user with its higher group, keep only simple string from group_name (display string after last slash)
                    ret[user['id']] = [g['id'],g['name'].split('/')[-1]]
                    #and remove user for next loops
                    users.remove(user)
        return ret

    _fields_names = {'service_names':'service_ids',
                    }

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

        ret = super(users, self).__init__(pool,cr)
        #add _field_names to fields definition of the model
        for f in self._fields_names.keys():
            #force name of new field with '_names' suffix
            self._columns.update({f:fields.function(_get_fields_names, type='char',method=True, multi='field_names',store=False)})
        return ret

    _columns = {
            'firstname': fields.char('firstname', size=128),
            'lastname': fields.char('lastname', size=128),
            'complete_name': fields.function(_name_get_fnc, type="char", string='Name', method=True, store={'res.users':[lambda self,cr,uid,ids,ctx={}:ids, ['name','firstname'], 10]}),
            'service_id':fields.many2one('openstc.service', 'Service    '),
            'service_ids': fields.many2many('openstc.service', 'openstc_user_services_rel', 'user_id', 'service_id', 'Services'),
            'cost': fields.integer('Coût horaire'),
            'post': fields.char('Post', size=128),
            'position': fields.char('Grade', size=128),
            'arrival_date': fields.datetime('Date d\'arrivée'),
            'birth_date': fields.datetime('Date de naissance'),
            'address_home': fields.char('Address', size=128),
            'city_home': fields.char('City', size=128),
            'phone': fields.char('Phone Number', size=12),
            'contact_id': fields.one2many('res.partner.address', 'user_id', "Partner"),
            'team_ids': fields.many2many('openstc.team', 'openstc_team_users_rel', 'user_id', 'team_id', 'Teams'),
            'manage_teams': fields.one2many('openstc.team', 'manager_id', "Teams"),
            'isDST' : fields.function(_get_group, arg="DIRE", method=True,type='boolean', store=False), #DIRECTOR group
            'isManager' : fields.function(_get_group, arg="MANA", method=True,type='boolean', store=False), #MANAGER group
            'actions':fields.function(_get_actions, method=True, string="Actions possibles",type="char", store=False),
            'current_group':fields.function(_get_current_group, method=True, string="OpenSTC higher group", help="The OpenSTC higher group of the user"),
    }
    _defaults = {
        'context_tz' : lambda self, cr, uid, context : 'Europe/Paris',
    }

    """
    @param ids: user to check
    @note: this method is used to check that service_id is in service_ids (for work-model purpose)
            after each create / update action on res.users
    """
    def check_service_id_and_service_ids(self, cr, uid, ids, context=None):
        if not isinstance(ids,list):
            ids = [ids]
        for user in self.read(cr, uid, ids, ['service_id','service_ids'],context=context):
            if user['service_id'] and user['service_id'][0] not in user['service_ids']:
                self.write(cr, uid, user['id'], {'service_ids':[(4,user['service_id'][0])]})
        return True

    def create(self, cr, uid, data, context={}):
        #_logger.debug('create USER-----------------------------------------------');
        res = super(users, self).create(cr, uid, data, context)

        company_ids = self.pool.get('res.company').name_search(cr, uid, name='STC')
        if len(company_ids) == 1:
            data['company_id'] = company_ids[0][0]
        else:
            data['company_id'] = 1;
        if data.has_key('isManager')!=False and data['isManager']==True :
            self.set_manager(cr, uid, [res], data, context)
        #TODO
        #else
        self.check_service_id_and_service_ids(cr, uid, [res], context=context)
        return res

    def write(self, cr, uid, ids, data, context=None):
        if data.has_key('isManager')!=False and data['isManager']==True :
            self.set_manager(cr, uid, ids, data, context)

        res = super(users, self).write(cr, uid, ids, data, context=context)
        self.check_service_id_and_service_ids(cr, uid, ids, context=context)
        return res

    def set_manager(self, cr, uid, ids, data,context):

        service_obj = self.pool.get('openstc.service')

        group_obj = self.pool.get('res.groups')
        #Get officer group (code group=OFFI)
        group_id = group_obj.search(cr, uid, [('code','=','OFFI')])[0]

        service_id = service_obj.browse(cr, uid, data['service_id'], context=context)
        #Previous manager become an agent
        manager = service_obj.read(cr, uid, data['service_id'],
                                    ['manager_id'], context)
        if manager and manager['manager_id']:
            self.write(cr, uid, [manager['manager_id'][0]], {
                    'groups_id' : [(6, 0, [group_id])],
                }, context=context)

        #Update service : current user is service's manager
        service_obj.write(cr, uid, data['service_id'], {
                 'manager_id': ids[0],
             }, context=context)

            #Calculates the agents can be added to the team


    def get_manageable_teams(self,cr,uid,target_user_id, context=None):
        """
        :rtype : List
        :param cr: database cursor
        :param uid: current_connected_user
        :param target_user_id: the target user
        :param context:
        :return: List of teams
        """
        target_user = self.browse(cr, uid, target_user_id, context=context)
        teams_collection = self.pool.get('openstc.team')
        formater = lambda team: {'id': team['id'] ,
                               'name': team['name'],
                               'manager_id': team['manager_id'],
                               'members':  teams_collection._get_members(cr, uid, [team['id']],None,None,context)
                               }

        if target_user.isDST:
            search_criterions = []

        elif target_user.isManager:
            search_criterions = [('service_ids.id','child_of',target_user.service_id.id)]

        else:
            search_criterions = [('manager_id.id','=',target_user.id)]

        teams_ids = teams_collection.search(cr,uid,search_criterions)
        teams = teams_collection.read(cr,uid,teams_ids,['id','name','manager_id','members'])
        return map(formater,teams)

    def get_manageable_officers(self, cr, uid, target_user_id, context=None):
        """
        Returns the user list available for task assignations
        for DST: all user from technical services
        for MANAGER : all user frpù services (and their children) manager belongs to
        for TEAM MANAGER: all user from teams TEAM MANAGER belongs to
        :rtype : List
        :param cr: database cursor
        :param uid: current user id
        :param target_user_id: target user id
        :param context: current user context
        """
        formater = lambda officer: { 'id': officer['id'],
                                     'name' : officer['name'],
                                     'firstname' : officer['firstname'],
                                     'complete_name' : ("%s %s" % (officer['firstname'], officer['name'])).strip(),
                                     'teams': officer['team_ids']}
        
        #we can't use domain as [('groups_id.code','!=','DIRE')] 
        #because each user has many groups, so all of them will have at least one group matching this criteria 
        not_dst_ids = self.search(cr, uid, [('groups_id.code','=','DIRE')],context=context)
        search_criterion = [('id','!=','1')]
        if not_dst_ids:
            search_criterion.append(('id','not in',not_dst_ids))
        target_user = self.browse(cr, uid, target_user_id, context=context)
        if target_user.isDST:
            search_criterion.append(('service_ids.technical','=',True))

        elif target_user.isManager:
            search_criterion.append(('service_ids.id','child_of',target_user.service_id.id))

        else:
            search_criterion.append(('team_ids.id','in', map((lambda t: t.id),target_user.manage_teams)))

        officers_ids = self.search(cr, uid, search_criterion)
        officers = self.read(cr,uid,officers_ids, ['name','firstname','team_ids'])
        return map(formater,officers)

    def get_manageable_teams_and_officers(self,cr,uid,target_user_id,context=None):
        return {'teams' : self.get_manageable_teams(cr,uid,target_user_id),
                'officers': self.get_manageable_officers(cr,uid,target_user_id)}


    #Get lists officers/teams where user is the referent on
    def getTeamsAndOfficers(self, cr, uid, ids,context=None):
        res = {}
        user_obj = self.pool.get('res.users')
        team_obj = self.pool.get('openstc.team')


        #get list of all agents expect administrator
        all_officer_ids = user_obj.search(cr, uid, [('id','<>','1')]);
        all_team_ids = team_obj.search(cr, uid, []);

        #get list of all teams
        all_officers = user_obj.browse(cr, uid, all_officer_ids, context);
        all_teams = team_obj.browse(cr, uid, all_team_ids, context);

        officers = []
        teams = []
        managerTeamID = []

        res['officers'] = []
        res['teams'] = []
        newOfficer = {}
        newTeam = {}
        #get user
        user = self.browse(cr, uid, uid, context=context)
        #If users connected is the DST get all teams and all officers
        if user.isDST:
            #Serialize each officer with name and firstname
            for officer in user_obj.read(cr, uid, all_officer_ids, ['id','name','firstname','team_ids']):
                newOfficer = { 'id'  : officer['id'],
                               'name' : officer['name'],
                               'firstname' : officer['firstname'],
                               'complete_name' : (officer['firstname'] or '')  + '  ' +  (officer['name'] or ''),
                               'teams': officer['team_ids']
                            }
                officers.append(newOfficer)
            res['officers'] =  officers

            #Serialize each team with name, manager and officers (with name and firstname)
            for team in team_obj.read(cr, uid, all_team_ids, ['id','name','manager_id','members']):
                newTeam = { 'id'   : team['id'] ,
                            'name' : team['name'],
                            'manager_id' : team['manager_id'],
                            'members' :  team_obj._get_members(cr, uid, [team['id']],None,None,context),
                            }
                teams.append(newTeam)
            res['teams'] = teams
        #If user connected is Manager get all teams and all officers where he is the referent
        elif user.isManager :
            #For each services authorized for user
            for officer in user_obj.read(cr, uid, all_officer_ids, ['id','name','firstname','team_ids','isDST','service_ids']):
                if not officer['isDST'] :
                    #Check if officer's services list is in user's services list
                    if (user.service_id.id in officer['service_ids']) and (officer['id'] not in officers):
                        newOfficer = { 'id'  : officer['id'],
                                      'name' : officer['name'],
                                      'firstname' : officer['firstname'],
                                      'complete_name' : (officer['firstname'] or '')  + '  ' +  (officer['name'] or ''),
                                      'teams': officer['team_ids']
                                      }
                        officers.append(newOfficer)
            res['officers'] = officers
            for team in all_teams:
                if (user.service_id in team.service_ids) and (team.id not in teams):
                    manager_id = False
                    if isinstance(team.manager_id, browse_null)!= True :
                        manager_id = team.manager_id.id
                    newTeam = { 'id'   : team.id ,
                        'name' : team.name,
                        'manager_id' : manager_id,
                        'members' : team_obj._get_members(cr, uid, [team.id],None,None,context)
                        }
                    teams.append(newTeam)
            res['teams'] = teams
        #If user connected is an officer
        else:
            #Get all teams where officer is manager on it
            for team_id in user.manage_teams :
                managerTeamID.append(team_id.id)
            if len(managerTeamID) > 0 :
                #For each officer
                for officer in all_officers:
                    if not officer.isDST :
                        #Check if user is the manager on officer's teams
                        for team_id in officer.team_ids :
                            if (team_id.id in managerTeamID) and (officer.id not in officers) :
                                newOfficer = { 'id'  : officer.id,
                                              'name' : officer.name,
                                              'firstname' : officer.firstname,
                                              'complete_name' : (officer['firstname'] or '')  + '  ' +  (officer['name'] or ''),
                                              'teams': officer.team_ids
                                          }
                                officers.append(newOfficer)
                                break
                res['officers'] = officers

        return res


users()

class team(osv.osv):
    _name = "openstc.team"
    _description = "team stc"
    _rec_name = "name"


    #Calculates the agents can be added to the team
    def _get_free_users(self, cr, uid, ids, fields, arg, context):
        res = {}
        user_obj = self.pool.get('res.users')
        group_obj = self.pool.get('res.groups')

        for id in ids:
            #get current team object
            team = self.browse(cr, uid, id, context=context)
            team_users = []
            #get list of agents already belongs to team
            for user_record in team.user_ids:
                team_users.append(user_record.id)
            #get list of all agents
            all_users = user_obj.search(cr, uid, []);

            free_users = []
            for user_id in all_users:
                #get current agent object
                user = user_obj.read(cr, uid, user_id,['groups_id'],context)
                #Current agent is DST (DIRECTOR group)?
                group_ids = group_obj.search(cr, uid, [('code','=','DIRE'),('id','in',user['groups_id'])])
                #Agent must not be DST and not manager of team and no already in team
                if (len( group_ids ) == 0) and (user_id != team.manager_id.id) and (user_id not in team_users):
                    free_users.append(user_id)

            res[id] = free_users

        return res

    _actions = {
        'create':lambda self,cr,uid,record, groups_code: 'MANA' in groups_code or 'DIRE' in groups_code,
        'update':lambda self,cr,uid,record, groups_code: 'MANA' in groups_code or 'DIRE' in groups_code,
        'delete':lambda self,cr,uid,record, groups_code: 'DIRE' in groups_code,
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

    _fields_names = {'service_names':'service_ids',
                    'user_names':'user_ids'}

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

        ret = super(team, self).__init__(pool,cr)
        #add _field_names to fields definition of the model
        for f in self._fields_names.keys():
            #force name of new field with '_names' suffix
            self._columns.update({f:fields.function(_get_fields_names, type='char',method=True, multi='field_names',store=False)})
        return ret


    _columns = {
            'name': fields.char('name', size=128),
            'deleted_at': fields.date('Deleted date'),
            'manager_id': fields.many2one('res.users', 'Manager'),
            'service_ids': fields.many2many('openstc.service', 'openstc_team_services_rel', 'team_id', 'service_id', 'Services'),
            'user_ids': fields.many2many('res.users', 'openstc_team_users_rel', 'team_id', 'user_id', 'Users'),
            'free_user_ids' : fields.function(_get_free_users, method=True,type='many2one', store=False),
            'actions':fields.function(_get_actions, method=True, string="Actions possibles",type="char", store=False),

    }
    #Calculates the agents can be added to the team
    def _get_members(self, cr, uid, ids, fields, arg, context):
        res = {}
        user_obj = self.pool.get('res.users')
        #for id in ids:
        team = self.browse(cr, uid, ids[0], context=context)
        team_users = []
        #get list of agents already belongs to team
        for user_record in team.user_ids:
             officer = user_obj.read(cr, uid, user_record.id,['id','name','firstname'],context)
             officerSerialized = { 'id'  : officer['id'],
                               'name' : officer['name'],
                               'firstname' : officer['firstname']
                               }
             team_users.append(officerSerialized)
            #res[id] = team_users
        return team_users

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        deleted_domain = []
        for s in args :
            if 'deleted_at' in s  :
                args.remove(s)
                deleted_domain = [('deleted_at','=', False)]
        args.extend(deleted_domain)
        return super(team, self).search(cr, uid, args, offset, limit, order, context, count)

    def unlink(self, cr, uid, ids, context=None):
       self.write(cr, uid, ids, {'deleted_at':datetime.now().strftime('%Y-%m-%d')})
       return True

team()


