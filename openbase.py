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
#----------------------------------------------------------
# Services
#----------------------------------------------------------

class service(osv.osv):
    _name = "openstc.service"
    _description = "openstc.service"
    _rec_name = "name"

    _columns = {
            'name': fields.char('Name', size=128, required=True),
            'favcolor':  fields.char('Name', size=128),
            'code': fields.char('Code', size=32, required=True),
            'service_id':fields.many2one('openstc.service', 'Service Parent'),
            'technical': fields.boolean('Technical service'),
            'manager_id': fields.many2one('res.users', 'Manager'),
            'user_ids': fields.one2many('res.users', 'service_id', "Users"),
            'team_ids': fields.many2many('openstc.teams', 'openstc_team_services_rel', 'service_id','team_id','Teams'),
            'site_ids':fields.many2many('openstc.site', 'openstc_site_services_rel', 'service_id', 'site_id', 'Sites'),
    }
service()



#----------------------------------------------------------
# Partner
#----------------------------------------------------------

class openstc_partner_type(osv.osv):
    _name = "openstc.partner.type"
    _description = "openstc.partner.type"
    _rec_name = "name"

    _columns = {
            'name': fields.char('Name', size=128, required=True),
            'code': fields.char('Code', size=32, required=True),
            'claimers': fields.one2many('res.partner', 'type_id', "Claimers"),
    }
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
        'complete_name':fields.function(_name_get_func, string='Activity name',type='char', method=True, store={'openstc.partner.type':[lambda self,cr,uid,ids,ctx={}:ids, ['name','parent_id'],10]}),
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

 }
res_partner()

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
        
        def get_menu_hierarchy(item,menu_dict):
            ret = []
            for child_id in item['child_id']:
                child = menu_dict.get(child_id)
                child.update({'tag':parseToUrl(child['name'])})
                child.update({'children':get_menu_hierarchy(child,menu_dict)})
                ret.append(child)
            return ret
        
        menu_ids = self.pool.get("ir.ui.menu").search(cr, uid, [], context)
        menu = self.pool.get("ir.ui.menu").read(cr, uid, menu_ids, ['id','name','parent_id','child_id'], context)
        menu = sorted(menu, key=lambda item: item['parent_id'])
        menu_dict = {}
        for item in menu:
            item.update({'tag':parseToUrl(item['name'])})
            menu_dict.update({item['id']:item})
        final_menu = []
        for item in menu:
            if not item['parent_id']:
                item.update({'children':get_menu_hierarchy(item, menu_dict)})
                final_menu.append(item)
        
        #print final_menu
        return final_menu


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

            'team_ids': fields.many2many('openstc.team', 'openstc_team_users_rel', 'user_id', 'team_id', 'Teams'),
            'manage_teams': fields.one2many('openstc.team', 'manager_id', "Teams"),
            'isDST' : fields.function(_get_group, arg="DIRE", method=True,type='boolean', store=False), #DIRECTOR group
            'isManager' : fields.function(_get_group, arg="MANA", method=True,type='boolean', store=False), #MANAGER group

    }

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

        return res

    def write(self, cr, uid, ids, data, context=None):

        if data.has_key('isManager')!=False and data['isManager']==True :
            self.set_manager(cr, uid, ids, data, context)

        res = super(users, self).write(cr, uid, ids, data, context=context)
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
            search_criterions = [('service_ids.id','=',target_user.service_id.id)]

        else:
            search_criterions = [('manager_id','=',target_user.id)]

        teams_ids = teams_collection.search(cr,uid,search_criterions)
        teams = teams_collection.read(cr,uid,teams_ids,['id','name','manager_id','members'])
        return map(formater,teams)

    def get_manageable_officers(self, cr, uid, target_user_id, context=None):
        """
        Returns the user list available for task assignations

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

        target_user = self.browse(cr, uid, target_user_id, context=context)
        if target_user.isDST:
            search_criterion = [('id','!=','1')]

        elif target_user.isManager:
            search_criterion = [('service_ids.id','=',target_user.service_id.id)]

        else:
            search_criterion= [('team_ids.id','in', map((lambda t: t.id),target_user.manage_teams))]

        not_dst = [('groups_id.code','!=','DIRE')]
        officers_ids = self.search(cr, uid, search_criterion + not_dst )
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

team()


