# -*- coding: utf-8 -*-
##############################################################################
#
#   Openstc-oe
#
##############################################################################

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
        
        "security/ir.model.access.csv",
             ],
    "demo": [],
    "test": [],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
