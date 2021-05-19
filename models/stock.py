# -*- coding: utf-8 -*-

from odoo import models, fields, api


class stockpicking(models.Model):
    _inherit = 'stock.picking'

    purchase_ship_order = fields.Char(compute="_get_ship_order")

    @api.depends('purchase_id')
    def _get_ship_order(self):

        for record in self:

            if record.purchase_id & record.purchase_id.ship_order:
                record.purchase_ship_order = record.purchase_id.ship_order


class stockmove(models.Model):
    _inherit = 'stock.move'

    ship_order_move = fields.Char(compute="_get_purchase_ship_order")

    @api.depends('picking_id')
    def _get_purchase_ship_order(self):

        for record in self:
            picking_id = record.env['stock.picking'].browse(
                record.picking_id)[0]

            if picking_id & picking_id.purchase_ship_order:

                record.ship_order_move = record.env['stock.picking'].browse(
                    record.picking_id.purchase_ship_order)[0]
