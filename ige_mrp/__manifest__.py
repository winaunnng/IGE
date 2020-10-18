# See LICENSE file for full copyright and licensing details.

{
    'name': 'IGE MRP Custom',
    'version': '12.0.1.0.0',
    'author': 'SME Intellect Co., Ltd',
    'category': 'Manufacturing Management',
    'website': '',
    'depends': ['mrp',],
    'summary': ' Manufacturing',
    'description': """
    MRP
    ====================
    - Manufacturing order with back date entry
   """,

    'data': [
        'views/mrp_production_views.xml',
    ],
    'qweb': [''],
    'css': [' '],

    'application': True
}
