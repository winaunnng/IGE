
# See LICENSE file for full copyright and licensing details.

{
    'name': 'IGE Accounting Custom',
    'version': '12.0.1.0.0',
    'author': 'SME Intellect Co., Ltd',
    'category': 'Account Management',
    'website': '',
    'depends': ['base','account','account_analytic_default','account_reports'],
    'summary': 'Accounting',
    'description': """
    Inventory & Payments
    ====================
    - Journal Entry Chatter
    - Keeping Balance Sheet journal items with analytic accounting
    - Adding Analytic Filters and Account Filters in Aged Receivable and Age Payable
    - Gross Profit Custom Report
   """,
    # 'demo': [''],
    'data': [
        'views/account_view.xml',
        'views/report_financial.xml',
        'data/account_financial_report_data.xml',

    ],
    'qweb': [''],
    'css': [' '],

    'application': True
}
