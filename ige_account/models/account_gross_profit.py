# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _, fields
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from datetime import datetime, timedelta


class ReportGrossProfit(models.AbstractModel):
    _inherit = "account.report"
    _name = "account.gross.profit"
    _description = "Gross Profit"

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_year'}
    filter_all_entries = False
    filter_unfold_all = False
    filter_account_type = [{'id': 14, 'name': _('Income'), 'selected': False},
                           {'id': 17, 'name': _('Cost of Revenue'), 'selected': False}]



    # TODO: remove when https://github.com/odoo/odoo/pull/31211 is merged and _lt is used above
    def _build_options(self, previous_options=None):
        self.filter_account_type = [{'id': 14, 'name': _('Income'), 'selected': False},
                                    {'id': 16, 'name': _('Expense'), 'selected': False},
                                    {'id': 17, 'name': _('Cost of Revenue '), 'selected': False},
 ]
        return super(ReportGrossProfit, self)._build_options(previous_options=previous_options)

    def _get_templates(self):
        templates = super(ReportGrossProfit, self)._get_templates()
        templates['line_template'] = 'ige_account.line_template_product_ledger_report'
        return templates

    def _get_columns_name(self, options):
        columns = [
            {},
            {'name': _('JRNL')},
            {'name': _('Account')},
            {'name': _('Ref')},
            {'name': _('Quantity')},
            {'name': _('Date'), 'class': 'date'},
            # {'name': _('Debit'), 'class': 'number'},
            # {'name': _('Credit'), 'class': 'number'}
         ]

        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': _('Amount Currency'), 'class': 'number'})

        columns.append({'name': _('Gross Profit'), 'class': 'number'})

        return columns

    def _set_context(self, options):
        ctx = super(ReportGrossProfit, self)._set_context(options)
        ctx['strict_range'] = True
        return ctx

    def _do_query_group_by_account(self, options, line_id):
        account_types = [a.get('id') for a in options.get('account_type') if a.get('selected', False)]
        if not account_types:
            account_types = [a.get('id') for a in options.get('account_type')]
        # Create the currency table.
        user_company = self.env.user.company_id
        companies = self.env['res.company'].search([])
        rates_table_entries = []
        for company in companies:
            if company.currency_id == user_company.currency_id:
                rate = 1.0
            else:
                rate = self.env['res.currency']._get_conversion_rate(
                    company.currency_id, user_company.currency_id, user_company, datetime.today())
            rates_table_entries.append((company.id, rate, user_company.currency_id.decimal_places))
        currency_table = ','.join('(%s, %s, %s)' % r for r in rates_table_entries)
        with_currency_table = 'WITH currency_table(company_id, rate, precision) AS (VALUES %s)' % currency_table

        # Sum query
        debit_field =  'debit'
        credit_field = 'credit'
        balance_field = 'balance'
        tables, where_clause, params = self.env['account.move.line']._query_get(
            [('account_id.user_type_id', 'in', account_types)])
        query = '''
                SELECT
                    \"account_move_line\".product_id,
                    SUM(ROUND(\"account_move_line\".''' + debit_field + ''' * currency_table.rate, currency_table.precision))     AS debit,
                    SUM(ROUND(\"account_move_line\".''' + credit_field + ''' * currency_table.rate, currency_table.precision))    AS credit,
                    SUM(ROUND(\"account_move_line\".''' + balance_field + ''' * currency_table.rate, currency_table.precision))   AS balance
                FROM %s
                LEFT JOIN currency_table                    ON currency_table.company_id = \"account_move_line\".company_id
                WHERE %s
                AND \"account_move_line\".product_id IS NOT NULL
                GROUP BY \"account_move_line\".product_id
            ''' % (tables, where_clause)
        if line_id:
            query = query.replace('WHERE', 'WHERE \"account_move_line\".product_id = %s AND ')
            params = [str(line_id)] + params
        self._cr.execute(with_currency_table + query, params)
        query_res = self._cr.dictfetchall()
        return dict((res['product_id'], res) for res in query_res)

    def _group_by_product_id(self, options, line_id):
        products = {}
        account_types = [a.get('id') for a in options.get('account_type') if a.get('selected', False)]
        if not account_types:
            account_types = [a.get('id') for a in options.get('account_type')]
        date_from = options['date']['date_from']
        results = self._do_query_group_by_account(options, line_id)
        context = self.env.context
        base_domain = [('date', '<=', context['date_to']), ('company_id', 'in', context['company_ids']),
                       ('account_id.user_type_id', 'in', account_types)]
        base_domain.append(('date', '>=', date_from))
        if context['state'] == 'posted':
            base_domain.append(('move_id.state', '=', 'posted'))

        if self.env.context.get('model') == 'account.gross.profit':
            base_domain += ['!', '&', '&', ('credit', '=', 0.0), ('debit', '=', 0.0),
                            ('amount_currency', '!=', 0.0)]
        for product_id, result in results.items():
            domain = list(base_domain)  # copying the base domain
            domain.append(('product_id', '=', product_id))
            # browse the product name and trust field in sudo, as we may not have full access to the record (but we still have to see it in the report)
            product = self.env['product.product'].sudo().browse(product_id)
            products[product] = result

            products[product]['total_lines'] = 0

            if not context.get('print_mode'):
                products[product]['total_lines'] = self.env['account.move.line'].search_count(domain)
                offset = int(options.get('lines_offset', 0))
                limit = self.MAX_LINES
                products[product]['lines'] = self.env['account.move.line'].search(domain, order='date,id', limit=limit,
                                                                                  offset=offset)
            else:
                products[product]['lines'] = self.env['account.move.line'].search(domain, order='date,id')


        return products

    @api.model
    def _get_lines(self, options, line_id=None):
        offset = int(options.get('lines_offset', 0))
        lines = []
        context = self.env.context
        company_id = context.get('company_id') or self.env.user.company_id
        if line_id:
            line_id = int(line_id.split('_')[1]) or None
        elif options.get('product_ids') and len(options.get('product_ids')) == 1:
            # If a default product is set, we only want to load the line referring to it.
            product_id = options['product_ids'][0]
            line_id = product_id
        if line_id:
            if 'product_' + str(line_id) not in options.get('unfolded_lines', []):
                options.get('unfolded_lines', []).append('product_' + str(line_id))


        grouped_products = self._group_by_product_id(options, line_id)
        sorted_products = sorted(grouped_products, key=lambda p: p.name or '')
        unfold_all = context.get('print_mode') and not options.get('unfolded_lines')
        total_debit = total_credit = total_balance = 0.0
        for product in sorted_products:
            debit = grouped_products[product]['debit']
            credit = grouped_products[product]['credit']
            balance = grouped_products[product]['balance']

            total_debit += debit
            total_credit += credit
            total_balance -= balance
            columns =[] # [self.format_value(debit), self.format_value(credit)]
            if self.user_has_groups('base.group_multi_currency'):
                columns.append('')
            columns.append(self.format_value(-balance))
            # don't add header for `load more`
            if offset == 0:
                lines.append({
                    'id': 'product_' + str(product.id),
                    'name': '[ ' + product.default_code + ' ] '+ product.name,
                    'columns': [{'name': v} for v in columns],
                    'level': 2,
                    'trust':'normal',
                    'unfoldable': True,
                    'unfolded': 'product_' + str(product.id) in options.get('unfolded_lines') or unfold_all,
                    'colspan':6,
                })
            user_company = self.env.user.company_id
            used_currency = user_company.currency_id
            if 'product_' + str(product.id) in options.get('unfolded_lines') or unfold_all:
                if offset == 0:
                    progress = 0
                else:
                    progress = float(options.get('lines_progress', 0))
                domain_lines = []
                amls = grouped_products[product]['lines']

                for line in amls:
                    if options.get('cash_basis'):
                        line_debit = line.debit_cash_basis
                        line_credit = line.credit_cash_basis
                    else:
                        line_debit = line.debit
                        line_credit = line.credit
                    date = amls.env.context.get('date') or fields.Date.today()
                    line_currency = line.company_id.currency_id
                    line_debit = line_currency._convert(line_debit, used_currency, user_company, date)
                    line_credit = line_currency._convert(line_credit, used_currency, user_company, date)

                    progress = line_credit - line_debit
                    caret_type = 'account.move'
                    if line.invoice_id:
                        caret_type = 'account.invoice.in' if line.invoice_id.type in (
                        'in_refund', 'in_invoice') else 'account.invoice.out'
                    elif line.payment_id:
                        caret_type = 'account.payment'
                    domain_columns = [line.journal_id.code, line.account_id.code, self._format_aml_name(line),
                                      line.quantity,
                                      line.date_maturity and format_date(self.env, line.date_maturity) or '',

                                      # line_debit != 0 and self.format_value(line_debit) or '',
                                      # line_credit != 0 and self.format_value(line_credit) or ''
                                      ]
                    if self.user_has_groups('base.group_multi_currency'):
                        domain_columns.append(self.with_context(no_format=False).format_value(line.amount_currency,
                                                                                              currency=line.currency_id) if line.amount_currency != 0 else '')
                    domain_columns.append(self.format_value(progress))
                    columns = [{'name': v} for v in domain_columns]
                    columns[3].update({'class': 'date'})
                    domain_lines.append({
                        'id': line.id,
                        'parent_id': 'product_' + str(product.id),
                        'name': format_date(self.env, line.date),
                        'class': 'date',
                        'columns': columns,
                        'caret_options': caret_type,
                        'level': 4,
                    })

                lines += domain_lines

        if not line_id:
            total_columns = ['', '', '', '',''] #,self.format_value(total_debit), self.format_value(total_credit)
            if self.user_has_groups('base.group_multi_currency'):
                total_columns.append('')
            total_columns.append(self.format_value(total_balance))
            lines.append({
                'id': 'grouped_partners_total',
                'name': _('Total'),
                'level': 0,
                'class': 'o_account_reports_domain_total',
                'columns': [{'name': v} for v in total_columns],
            })

        return lines

    @api.model
    def _get_report_name(self):
        return _('Gross Profit')
