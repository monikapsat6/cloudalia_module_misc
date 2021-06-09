# -*- coding: utf-8 -*-
from urllib.parse import urlparse
import logging
import werkzeug
from odoo import http, _
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class AuthSignupHome(AuthSignupHome):

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        if qcontext.get('mobile'):
            values = {key: qcontext.get(key)
                      for key in ('login', 'name', 'password', 'mobile', 'vat', 'street', 'street2', 'zip', 'city', 'state_id', 'country_id', 'escola')}
            values.update({'escola': escola})
            if not values:
                raise UserError(_("The form was not properly filled in."))
            if values.get('password') != qcontext.get('confirm_password'):
                raise UserError(
                    _("Passwords do not match; please retype them."))
            supported_langs = [
                lang['code'] for lang in request.env['res.lang'].sudo().search_read([], ['code'])]
            if request.lang in supported_langs:
                values['lang'] = request.lang
            self._signup_with_values(qcontext.get('token'), values)
            request.env.cr.commit()
        else:
            values = {key: qcontext.get(key)
                      for key in ('login', 'name', 'password')}
            if not values:
                raise UserError(_("The form was not properly filled in."))
            if values.get('password') != qcontext.get('confirm_password'):
                raise UserError(
                    _("Passwords do not match; please retype them."))
            supported_langs = [
                lang['code'] for lang in request.env['res.lang'].sudo().search_read([], ['code'])]
            if request.lang in supported_langs:
                values['lang'] = request.lang
            self._signup_with_values(qcontext.get('token'), values)
            request.env.cr.commit()

    @http.route('/web/signup/<string:escola_id>', type='http', auth='public', website=True,
                sitemap=False, methods=['GET'])
    def web_auth_signup(self, *args, **kw):
        value_dict = dict(kw)

        escoles = {'holi': 1, 'cmontserrat': 29,
                   'eminguella': 19, 'jpelegri': 9, 'lestonnac': 14, 'inscassaselva': 32}

        for school in escoles:
            if str(value_dict["escola_id"]).find(str(escoles[school])) != -1:
                url_escola = True
                global escola
                escola = school

        if url_escola:
            qcontext = self.get_auth_signup_qcontext()
            qcontext['states'] = request.env['res.country.state'].sudo().search([
            ])
            qcontext['countries'] = request.env['res.country'].sudo().search([])

            if not qcontext.get('token') and not qcontext.get('signup_enabled'):
                raise werkzeug.exceptions.NotFound()

            if 'error' not in qcontext and request.httprequest.method == 'POST':
                try:
                    self.do_signup(qcontext, escola)
                    # Send an account creation confirmation email
                    if qcontext.get('token'):
                        user_sudo = request.env['res.users'].sudo().search(
                            [('login', '=', qcontext.get('login'))])
                        template = request.env.ref(
                            'auth_signup.mail_template_user_signup_account_created',
                            raise_if_not_found=False)
                        if user_sudo and template:
                            template.sudo().with_context(
                                lang=user_sudo.lang,
                                auth_login=werkzeug.url_encode({
                                    'auth_login': user_sudo.email
                                }),
                            ).send_mail(user_sudo.id, force_send=True)
                    return super(AuthSignupHome, self).web_login(*args, **kw)
                except UserError as e:
                    qcontext['error'] = e.name or e.value
                except (SignupError, AssertionError) as e:
                    if request.env["res.users"].sudo().search(
                            [("login", "=", qcontext.get("login"))]):
                        qcontext["error"] = _(
                            "Another user is already registered using this email address.")
                    else:
                        _logger.error("%s", e)
                        qcontext['error'] = _(
                            "Could not create a new account.")

            response = request.render(
                'cloudalia_module_misc.registro_login', qcontext)

        else:
            qcontext = self.get_auth_signup_qcontext()
            qcontext['states'] = request.env['res.country.state'].sudo().search([
            ])
            qcontext['countries'] = request.env['res.country'].sudo().search([])

            if not qcontext.get('token') and not qcontext.get('signup_enabled'):
                raise werkzeug.exceptions.NotFound()

            if 'error' not in qcontext and request.httprequest.method == 'POST':
                try:
                    self.do_signup(qcontext)
                    # Send an account creation confirmation email
                    if qcontext.get('token'):
                        user_sudo = request.env['res.users'].sudo().search(
                            [('login', '=', qcontext.get('login'))])
                        template = request.env.ref(
                            'auth_signup.mail_template_user_signup_account_created',
                            raise_if_not_found=False)
                        if user_sudo and template:
                            template.sudo().with_context(
                                lang=user_sudo.lang,
                                auth_login=werkzeug.url_encode({
                                    'auth_login': user_sudo.email
                                }),
                            ).send_mail(user_sudo.id, force_send=True)
                    return super(AuthSignupHome, self).web_login(*args, **kw)
                except UserError as e:
                    qcontext['error'] = e.name or e.value
                except (SignupError, AssertionError) as e:
                    if request.env["res.users"].sudo().search(
                            [("login", "=", qcontext.get("login"))]):
                        qcontext["error"] = _(
                            "Another user is already registered using this email address.")
                    else:
                        _logger.error("%s", e)
                        qcontext['error'] = _(
                            "Could not create a new account.")

            response = request.render('auth_signup.signup', qcontext)

        response.headers['X-Frame-Options'] = 'DENY'
        return response

    def get_auth_signup_qcontext(self):
        """ Shared helper returning the rendering context for signup and reset password """
        qcontext = request.params.copy()
        print(request.params)
        qcontext.update(self.get_auth_signup_config())
        if not qcontext.get('token') and request.session.get('auth_signup_token'):
            qcontext['token'] = request.session.get('auth_signup_token')
        if qcontext.get('token'):
            try:
                # retrieve the user info (name, login or email) corresponding to a signup token
                token_infos = request.env['res.partner'].sudo(
                ).signup_retrieve_info(qcontext.get('token'))
                for k, v in token_infos.items():
                    qcontext.setdefault(k, v)
            except:
                qcontext['error'] = _("Invalid signup token")
                qcontext['invalid_token'] = True
        return qcontext


class Controller(http.Controller):

    @http.route(['/web/signup/<string:variable>'],
                type='http', auth="user", methods=['GET'], website=True)
    def view(self, **kwargs):
        values = dict(kwargs)
        object_ids = request.env['model.name'].search(
            [('your_field', '=', values['variable'])])
        values['object_ids'] = object_ids
        values['customer'] = object_ids[0].customer_id.name
        return request.render('module.template_id', values)
