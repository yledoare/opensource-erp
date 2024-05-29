from odoo import models, fields, api
from datetime import datetime, date, timedelta


class EgSyncHistory(models.Model):
    _inherit = "eg.sync.history"

    @api.model
    def create(self, vals):
        if not vals.get("name"):
            vals['name'] = self.env['ir.sequence'].next_by_code('eg.ecom.instance') or "New"
        res = super(EgSyncHistory, self).create(vals)
        return res

    def unlink_history_by_cron(self):
        past_week_date = date.today() - timedelta(days=7)
        past_week_date = past_week_date.strftime("%Y-%m-%d")
        eg_history_ids = self.search([("create_date", "<=", past_week_date), ("parent_id", "=", True)])
        if eg_history_ids:
            eg_history_ids.unlink()
