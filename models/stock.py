# -*- coding: utf-8 -*-
# no acabado
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class stockpicking(models.Model):
    _inherit = 'stock.picking'

    purchase_ship_order = fields.Char(compute="_get_ship_order")

    @api.depends('purchase_id')
    def _get_ship_order(self):

        for record in self:

            if record.purchase_id.ship_order:

                record.purchase_ship_order = record.purchase_id.ship_order

    @api.multi
    def fill_all_product_quantities(self):

        for o in self.move_lines:
            """
            if product.quantity_done < product.product_uom_qty:
                product.quantity_done = product.product_uom_qty
            """
            # print("" + str(o.product_id))
            print("#" * 25)
            print("" + str(o.quantity_done))
            print("#" * 25)

    @api.multi
    def button_validate(self):
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some lines to move'))

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')

        no_quantities_done_sg = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits)
                                    for move_line in self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        no_reserved_quantities_sg = all(float_is_zero(
            move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in self.move_line_ids)

        no_quantities_done_nsg = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits)
                                     for move_line in self.move_lines.filtered(lambda m: m.state not in ('done', 'cancel')))
        no_reserved_quantities_nsg = all(float_is_zero(
            move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in self.move_lines)
        if no_reserved_quantities_sg and no_quantities_done_sg and no_quantities_done_nsg and no_reserved_quantities_nsg:
            raise UserError(
                _('You cannot validate a transfer if you have not processed any quantity. You should rather cancel the transfer.'))

        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check_sg = self.move_line_ids
            lines_to_check_nsg = self.move_lines

            if not no_quantities_done_sg:
                lines_to_check_sg = lines_to_check_sg.filtered(
                    lambda line: float_compare(line.qty_done, 0,
                                               precision_rounding=line.product_uom_id.rounding)
                )

            if not no_quantities_done_nsg:
                lines_to_check_nsg = lines_to_check_nsg.filtered(
                    lambda line: float_compare(line.qty_done, 0,
                                               precision_rounding=line.product_uom_id.rounding)
                )

            for line in lines_to_check_sg:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(
                            _('You need to supply a lot/serial number for %s.') % product.display_name)

            for line in lines_to_check_nsg:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(
                            _('You need to supply a lot/serial number for %s.') % product.display_name)

        if no_quantities_done_sg and no_quantities_done_nsg:
            view = self.env.ref('stock.view_immediate_transfer')
            wiz = self.env['stock.immediate.transfer'].create(
                {'pick_ids': [(4, self.id)]})
            return {
                'name': _('Immediate Transfer?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.immediate.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
            view = self.env.ref('stock.view_overprocessed_transfer')
            wiz = self.env['stock.overprocessed.transfer'].create(
                {'picking_id': self.id})
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.overprocessed.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        # Check backorder should check for other barcodes
        if self._check_backorder():
            return self.action_generate_backorder_wizard()
        self.action_done()
        return


class stockmove(models.Model):
    _inherit = 'stock.move'

    ship_order_move = fields.Char(compute="_get_purchase_ship_order")

    @api.depends('picking_id')
    def _get_purchase_ship_order(self):

        for record in self:
            stock_picking = record.env['stock.picking']

            if stock_picking.browse(record.picking_id.id):

                record.ship_order_move = stock_picking.browse(
                    record.picking_id.id).purchase_ship_order
