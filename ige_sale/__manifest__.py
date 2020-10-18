# See LICENSE file for full copyright and licensing details.
{
    'name': 'IGE Sale Custom',
    'version': '12.0.1.0.0',
    'author': 'SME Intellect Co., Ltd',
    'category': 'Sale Management',
    'website': '',
    'depends': ['sale','account_analytic_default'],
    'summary': ' Sale ',
    'description': """
     Sale
    ====================
    - Sale Order Back Date Entry 
    - Keeping SO with default analytic account

   """,
    # 'demo': [''],
    'data': [
        'views/sale_view.xml'
    ],
    'qweb': [''],
    'css': [' '],

    'application': True
}
