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

{
    "name": "OpenBase",
    "version": "0.1",
    "depends": ["web", "web_calendar","base","product","purchase","sale","stock", "email_template"],
    "author": "PYF & BP",
    "category": "SICLIC",
    "description": """
    Module de Base pour toute installation d'une suite logiciel SICLIC.
    Il contient :
    * définition des modèles concernant la structure d'une mairie (Services, Groups, Teams, Users)
    * Données communes: Types de partner, usage de produits (maintenance, réservation, achats, ventes)
    * définition des modèles des sites et types de sites
    """,
    "data": [
        "data/openstc.site.type.csv",
        "views/openbase_data.xml",
        "views/base_data.xml",
        "views/openbase_views.xml",
        "views/openbase_menu.xml",
        
        "security/openbase_security.xml",
        
        "workflow/validation_workflow.xml",
        
        "security/ir.model.access.csv",
             ],
    "demo": [],
    "test": [],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
