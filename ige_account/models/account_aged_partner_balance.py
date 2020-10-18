# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import ast
import logging
from odoo.tools.misc import format_date


from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)

class AccountReport(models.AbstractModel):
    _inherit = 'account.report'


class report_account_aged_partner(models.AbstractModel):
    _inherit = "account.aged.partner"

    filter_ir_filters = None
    filter_analytic = None
    filter_account_type = []

    @api.model
    def _get_lines(self, options, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        account_types = [self.env.context.get('account_type')]
        accounts = [a.get('id') for a in options.get('account_type') if a.get('selected', False)]
        if not accounts:
            accounts = [a.get('id') for a in options.get('account_type')]

        results, total, amls = self.env['report.account.report_agedpartnerbalance'].with_context(account_filters =accounts,
            include_nullified_amount=True)._get_partner_move_lines(account_types, self._context['date_to'], 'posted',
                                                                   30)
        for values in results:
            if line_id and 'partner_%s' % (values['partner_id'],) != line_id:
                continue
            vals = {
                'id': 'partner_%s' % (values['partner_id'],),
                'name': values['name'],
                'level': 2,
                'columns': [{'name': ''}] * 3 + [{'name': self.format_value(sign * v)} for v in
                                                 [values['direction'], values['4'],
                                                  values['3'], values['2'],
                                                  values['1'], values['0'], values['total']]],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
            }
            lines.append(vals)
            if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    caret_type = 'account.move'
                    if aml.invoice_id:
                        caret_type = 'account.invoice.in' if aml.invoice_id.type in (
                        'in_refund', 'in_invoice') else 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    line_date = aml.date_maturity or aml.date
                    if not self._context.get('no_format'):
                        line_date = format_date(self.env, line_date)
                    vals = {
                        'id': aml.id,
                        'name': line_date,
                        'class': 'date',
                        'caret_options': caret_type,
                        'level': 4,
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': v} for v in
                                    [aml.journal_id.code, aml.account_id.code, self._format_aml_name(aml)]] + \
                                   [{'name': v} for v in
                                    [line['period'] == 6 - i and self.format_value(sign * line['amount']) or '' for i in
                                     range(7)]],
                        'action_context': aml.get_action_context(),
                    }
                    lines.append(vals)
        if total and not line_id:
            total_line = {
                'id': 0,
                'name': _('Total'),
                'class': 'total',
                'level': 2,
                'columns': [{'name': ''}] * 3 + [{'name': self.format_value(sign * v)} for v in
                                                 [total[6], total[4], total[3], total[2], total[1], total[0],
                                                  total[5]]],
            }
            lines.append(total_line)
        return lines


class report_account_aged_receivable(models.AbstractModel):
    _inherit = "account.aged.receivable"

    def _build_options(self, previous_options=None):
        account_filters = self.env['account.account'].search([('internal_type','=','receivable')])
        accounts = []
        if account_filters:
            for acc in account_filters:
                accounts.append({'id':acc.id,'name':_(acc.name),'selected':False})
        self.filter_account_type = accounts
        return super(report_account_aged_receivable, self)._build_options(previous_options=previous_options)

    @api.model
    def _get_options(self, previous_options=None):
        self.filter_analytic = True
        rslt = super(report_account_aged_partner, self)._get_options(previous_options)
        return rslt

class report_account_aged_payable(models.AbstractModel):
    _inherit = "account.aged.payable"

    def _build_options(self, previous_options=None):
        self.filter_analytic = True
        account_filters = self.env['account.account'].search([('internal_type', '=', 'payable')])
        accounts = []
        if account_filters:
            for acc in account_filters:
                accounts.append({'id': acc.id, 'name': _(acc.name), 'selected': False})
        self.filter_account_type = accounts
        return super(report_account_aged_payable, self)._build_options(previous_options=previous_options)

    @api.model
    def _get_options(self, previous_options=None):
        self.filter_analytic = True
        rslt = super(report_account_aged_partner, self)._get_options(previous_options)
        return rslt







