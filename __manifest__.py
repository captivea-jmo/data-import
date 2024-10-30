
{
    'name': 'Data Import XLSX',
    'version': '17.0.0.2',
    'summary': 'Module to import data from XLSX file via JSON-RPC',
    'category': 'Tools',
    'author': 'captivea-jmo',
    'depends': ['base'],
    'data': [
        'views/import_wizard_view.xml',
        'views/menu_item.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
}
