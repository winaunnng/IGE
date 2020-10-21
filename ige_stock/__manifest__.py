
# See LICENSE file for full copyright and licensing details.

{
    'name': 'IGE Inventory Custom',
    'version': '12.0.1.0.0',
    'author': 'SME Intellect Co., Ltd',
    'category': 'Inventory Management',
    'website': '',
    'depends': ['stock',],
    'summary': ' Inventory & Accounting',
    'description': """
    Inventory & Payments
    ====================
    - Validating picking with back date entry
    - Adjusting inventory with back date entry
    - Keeping stock journal entry with analytic accounting
    
   """,
    # 'demo': [''],
    'data': [
        'views/stock_view.xml'
    ],
    'qweb': [''],
    'css': [' '],

    'application': True
}
