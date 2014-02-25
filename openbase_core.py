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
from osv import fields, osv
import datetime as dt
from datetime import datetime, date, timedelta
from dateutil import *
from dateutil.tz import *
#Core abstract model to add SICLIC custom features, such as actions rights calculation (to be used in SICLIC custom GUI)
class OpenbaseCore(osv.Model):
    _auto = True
    _register = False # not visible in ORM registry, meant to be python-inherited only
    _transient = False # True in a TransientModel


    _actions_to_eval = {}
    _fields_names_to_eval = {}
    _actions = {}
    _fields_names = {}

    #keywords to compute filter domain
    DATE_KEYWORDS = ['FIRSTDAYWEEK', 'LASTDAYWEEK',  'FIRSTDAYMONTH',  'LASTDAYMONTH', 'OVERMONTH', 'OUTDATED']
    DATE_FMT = "%Y-%m-%d"
    DATE_TIME_FMT = "%Y-%m-%d %H:%M:%S"


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

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        new_args = []
        #fields = self.fields_get(cr, uid, context=context).items()
        for id, domain  in enumerate(args) :
            #Test if domain tuple = ('key','operator','value')
            if len(domain) == 3 :
                #Get key, operator and domain
                k, o, v = domain
                #Get field's type
                try:
                    type = self._columns[k]._type
                except (KeyError):
                    type = None
                #if domain contains special keyword
                if v in self.DATE_KEYWORDS :
                    #Adapts keyword in domain to specials filter that need to be computed (cf get_date_from_keyword method)
                    domain[2] = self.get_date_from_keyword(v)
                elif  type != None and type == 'datetime':
                    try:
                        #Test if already format with hours
                        datetime.strptime(v,self.DATE_TIME_FMT)
                    except ValueError:
                        #Format date with hours
                        domain[2] = datetime.strftime(datetime.strptime(v,self.DATE_FMT), "%Y-%m-%d %H:%M:%S")
            new_args.extend([domain])
        return super(OpenbaseCore, self).search(cr, uid, new_args, offset, limit, order, context, count)


    """
    @param keyword: keyword to compute corresponding date
    @return: return string date for domain search
        domain is used to filter OpenBase object (ask (request), project (intervention)  :
        * from current week
        * from current month
        * delayed (deadline spent)
    """
    def get_date_from_keyword(self, keyword):
        val = ""
        timeDtFrmt = "%Y-%m-%d %H:%M:%S"
        today = date.today()
        start_day_month = dt.datetime(today.year, today.month, 1)
        dates = [today + dt.timedelta(days=i) for i in range(0 - today.weekday(), 7 - today.weekday())]
        if keyword == 'FIRSTDAYWEEK':
             return datetime.strftime(dates[0],timeDtFrmt)
        elif keyword == 'LASTDAYWEEK':
             return datetime.strftime(dates[6],timeDtFrmt)
        elif keyword == 'FIRSTDAYMONTH':
            return datetime.strftime(dt.datetime(today.year, today.month, 1),timeDtFrmt)
        elif keyword == 'LASTDAYMONTH':
            date_on_next_month = start_day_month + dt.timedelta(31)
            start_next_month = dt.datetime(date_on_next_month.year, date_on_next_month.month, 1)
            return datetime.strftime(start_next_month - dt.timedelta(1),timeDtFrmt)
        elif keyword == 'OVERMONTH':
             return datetime.strftime(start_day_month + dt.timedelta(31),timeDtFrmt)
        elif keyword == 'OUTDATED':
            return datetime.strftime(today,timeDtFrmt)
        return val
