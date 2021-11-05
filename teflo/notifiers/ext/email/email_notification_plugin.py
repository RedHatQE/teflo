# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Red Hat, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
    teflo.notifiers.email.email_notification

    Teflo's default and main executor.

    :copyright: (c) 2018 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import os
import os.path
import smtplib
from ....core import NotificationPlugin
from ....helpers import template_render, schema_validator, DataInjector, generate_default_template_vars
from ....exceptions import TefloNotifierError
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText


class EmailNotificationPlugin(NotificationPlugin):

    __plugin_name__ = 'email-notifier'
    __schema_file_path__ = os.path.abspath(os.path.join(os.path.dirname(__file__), "schema/schema.yml"))
    __schema_exts_path__ = os.path.abspath(os.path.join(os.path.dirname(__file__), "schema/email_extensions.py"))

    def __init__(self, notification):

        super(EmailNotificationPlugin, self).__init__(notification=notification)

        self.scenario = getattr(self.notification, 'scenario')
        self.scenario_graph = getattr(self.scenario, 'scenario_graph')
        self.sender = getattr(self.notification, 'from')
        self.receivers = getattr(self.notification, 'to')
        self.cc = getattr(notification, 'cc', [])
        self.subject = getattr(self.notification, 'subject',
                               'Teflo Notification.')
        self.body = getattr(self.notification, 'message_body', '')
        self.config_params = self.get_config_params()
        self.creds_params = self.get_credential_params()
        self.body_tmpl = getattr(self.notification, 'message_template', '')
        self.attachments = [os.path.abspath(a)
                            for a in getattr(self.notification, 'attachments', [])]

    def send_message(self):
        """
        Send the message.
        """
        smtp = ''
        try:
            smtp_host = self.creds_params.get('smtp_host')
            if self.creds_params.get('smtp_port', False):
                smtp_host = ':'.join([smtp_host, self.creds_params.get('smtp_port')])

            self.logger.debug("Connecting to %s", smtp_host)

            smtp = smtplib.SMTP(smtp_host)
            if self.creds_params.get('smtp_starttls', False) and self.creds_params.get('smtp_starttls') == 'True':
                if smtp.has_extn('STARTTLS'):
                    self.logger.debug("Using tls.")
                    try:
                        smtp.starttls()
                    except smtplib.SMTPException:
                        self.logger.error("unable to start an encrypted session.")
                        raise
                    try:
                        smtp.ehlo()
                    except smtplib.SMTPException:
                        self.logger.error("Helo failed after encrypting the session.")
                        raise
                else:
                    TefloNotifierError('The Start TLS is not available for the server.')

            if self.creds_params.get('smtp_user', False) and self.creds_params.get('smtp_password', False):
                if smtp.has_extn('AUTH'):
                    try:
                        smtp.login(self.creds_params.get('smtp_user'), self.creds_params.get('smtp_password'))
                    except smtplib.SMTPAuthenticationError:
                        self.logger.error('Failed to authentication. Please check the username and/or password.')
                        raise
                    except smtplib.SMTPException:
                        self.logger.error('Looks like no suitable authentication method was found.')
                        raise
                else:
                    raise TefloNotifierError('Authentication is not available for the server.')
            mail = self._build_msg()
            smtp.sendmail(from_addr=self.sender, to_addrs=self.receivers, msg=mail)

        finally:
            smtp.quit()

    def _build_msg(self):
        """Build the EmailMessage object"""

        mail = MIMEMultipart()
        if self.cc:
            mail['cc'] = ','.join(self.cc)
        mail['to'] = ','.join(self.receivers)
        mail['from'] = self.sender
        mail['subject'] = self.subject
        mail["User-Agent"] = "teflo-email-notifier"

        body = MIMEText(self.body)
        mail.attach(body)

        if self.attachments:
            for a in self.attachments:
                part = MIMEBase('application', 'octet-stream')
                with open(a, 'rb') as fp:
                    part.set_payload(fp.read())
                encoders.encode_base64(part)
                part.add_header('Content-disposition', 'attachment', filename=os.path.basename(a))
                mail.attach(part)

        return mail.as_string()

    def notify(self):
        """
        Implementation of the notify method for generating the email
        notification and sending it to an SMTP server.

        :return:
        """

        # no msg body params assume using teflo default template
        if not self.body and not self.body_tmpl:
            self.logger.info('Using generic teflo email template')
            if not getattr(self.notification, 'on_start'):
                self.body = template_render(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                            'templates/email_txt_template.jinja')
                                                            ),

                                              generate_default_template_vars(self.scenario, self.notification)
                                            )
            else:
                self.body = template_render(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                                         'templates/email_on_start_txt_template.jinja')
                                                            ),
                                            generate_default_template_vars(self.scenario, self.notification)
                                            )
        elif not self.body and self.body_tmpl:

            # this var_dict consists of scenario object and scenario_vars which are all the variables
            # used by teflo along with environment variables
            var_dict = generate_default_template_vars(self.scenario, self.notification)
            self.body = template_render(os.path.abspath(os.path.join(getattr(self.notification, 'workspace'),
                                        self.body_tmpl)), var_dict)

        self.logger.debug('The loaded message body is: \n')
        self.logger.debug(self.body)

        if self.creds_params:
            self.logger.info('Sending email out.')
            self.send_message()
        else:
            raise TefloNotifierError('No credentials for the Email Notifier was found in the teflo.cfg.')

    def validate(self):

        schema_validator(schema_data=self.build_profile(self.notification),
                         schema_creds=self.creds_params,
                         schema_files=[self.__schema_file_path__], schema_ext_files=[self.__schema_exts_path__])
