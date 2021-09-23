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
    tests.email_plugin

    Unit tests for testing email notifier plguin class

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import pytest
import mock
import smtplib
import os
from smtplib import SMTPAuthenticationError, SMTPException
from teflo.notifiers.ext import EmailNotificationPlugin
from teflo.resources import Notification
from teflo.exceptions import TefloNotifierError

@pytest.fixture(scope='class')
def note_params():

    params = dict(
        description='description goes here.',
        notifier='email-notifier',
        on_start=True,
        to=['jimmy@who.com'],
    )
    params.setdefault('from','tommy@who.com')

    return params

@pytest.fixture(scope='class')
def note_config_params():
    params = dict(
        smtp_port='33',
        smtp_starttl='True',
        smtp_user='joey',
        smtp_password='changeMe123'
    )

    return params


class TestEmailNotifier(object):
    from teflo.resources import Scenario
    @staticmethod
    def send_message():
        return

    @staticmethod
    def test_notify_no_config(scenario:Scenario, note_params):
        setattr(scenario, 'passed_tasks', ['validate'])
        setattr(scenario, 'failed_tasks', [])
        setattr(scenario, 'overall_status', 0)

        note = Notification(name='note', parameters=note_params, config=getattr(scenario, 'config'))
        setattr(note, 'scenario', scenario)
        emailer = EmailNotificationPlugin(note)
        with pytest.raises(TefloNotifierError):
            emailer.notify()

    @staticmethod
    @mock.patch.object(EmailNotificationPlugin, 'send_message', send_message)
    def test_default_on_success_notify(scenario:Scenario):
        setattr(scenario, 'passed_tasks', ['validate'])
        setattr(scenario, 'failed_tasks', [])
        setattr(scenario, 'overall_status', 0)
        note = [note for note in scenario.get_notifications() if note.name == 'note02']
        for n in note:
            setattr(n, 'scenario', scenario)
            emailer = EmailNotificationPlugin(n)
            emailer.notify()

    @staticmethod
    @mock.patch.object(EmailNotificationPlugin, 'send_message', send_message)
    def test_default_on_failure_notify(scenario:Scenario):
        setattr(scenario, 'passed_tasks', ['validate'])
        setattr(scenario, 'failed_tasks', ['provision'])
        setattr(scenario, 'overall_status', 1)
        note = [note for note in scenario.get_notifications() if note.name == 'note02']
        for n in note:
            setattr(n, 'scenario', scenario)
            emailer = EmailNotificationPlugin(n)
            emailer.notify()

    @staticmethod
    @mock.patch.object(EmailNotificationPlugin, 'send_message', send_message)
    def test_default_on_start_notify(scenario:Scenario):
        setattr(scenario, 'passed_tasks', ['validate'])
        setattr(scenario, 'failed_tasks', [])
        setattr(scenario, 'overall_status', 0)
        note = [note for note in scenario.get_notifications() if note.name == 'note01']
        for n in note:
            setattr(n, 'scenario', scenario)
            emailer = EmailNotificationPlugin(n)
            emailer.notify()

    @staticmethod
    @mock.patch.object(Notification, 'workspace', os.path.abspath(os.path.join(os.path.dirname(
        os.path.dirname(__file__)), 'assets')))
    @mock.patch.object(EmailNotificationPlugin, 'send_message', send_message)
    def test_custom_message_template_notify(scenario:Scenario):
        setattr(scenario, 'passed_tasks', ['validate'])
        setattr(scenario, 'failed_tasks', [])
        setattr(scenario, 'overall_status', 0)
        note = [note for note in scenario.get_notifications() if note.name == 'note01']

        for n in note:
            setattr(n, 'scenario', scenario)
            setattr(n, 'message_template', 'test_email_template.jinja')
            emailer = EmailNotificationPlugin(n)
            emailer.notify()

    @staticmethod
    @mock.patch('smtplib.SMTP')
    def test_send_email_notify(mock_smtp, scenario:Scenario):

        setattr(scenario, 'passed_tasks', ['validate'])
        setattr(scenario, 'failed_tasks', [])
        setattr(scenario, 'overall_status', 0)
        note = [note for note in scenario.get_notifications() if note.name == 'note01']

        for n in note:
            setattr(n, 'scenario', scenario)
            setattr(n, 'attachments', [os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                                                    'assets/vars_data.yml')
                                                      )]
                    )
            setattr(n, 'cc', ['joey@who.com'])
            emailer = EmailNotificationPlugin(n)
            emailer.notify()
