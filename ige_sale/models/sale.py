# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields,_
from odoo.exceptions import UserError, ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    confirmation_date = fields.Datetime(string='Confirmation Date', readonly=False, index=True, help="Date on which the sales order is confirmed.", oldname="date_confirm", copy=False)
    effective_date = fields.Date("Effective Date", compute='_compute_effective_date', store=True, help="Completion date of the first delivery order.")

    @api.depends('picking_ids.write_date')
    def _compute_effective_date(self):
        for order in self:
            pickings = order.picking_ids.filtered(
                lambda x: x.state == 'done' and x.location_dest_id.usage == 'customer')
            dates_list = [date for date in pickings.mapped('date_done') if date]
            order.effective_date = dates_list and min(dates_list).date()

    @api.model
    def default_get(self, fields_list):
        defaults = super(SaleOrder, self).default_get(fields_list)
        rec = self.env['account.analytic.default'].account_get(partner_id =self.partner_id.id,
            user_id = self.user_id.id or self.env.uid,
            date =fields.Date.today(),
            company_id=self.company_id.id
        )
        if rec:
            if 'analytic_account_id' in fields_list:
                defaults.update({
                    'analytic_account_id': rec.analytic_id.id,
                })

        return defaults

    @api.multi
    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'sale',
            'confirmation_date': self.confirmation_date or fields.Datetime.now()
        })

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        context = self._context.copy()
        context.pop('default_name', None)

        self.with_context(context)._action_confirm()
        if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
            self.action_done()
        return True

