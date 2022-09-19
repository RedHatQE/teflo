# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 Red Hat, Inc.
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
    tests.test_asset_provisioner

    Unit tests for testing teflo asset provisioner class.

    :copyright: (c) 2022 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import mock
import pytest

from teflo.resources import Notification
from teflo.core import NotificationPlugin
from teflo.notifiers import Notifier


@pytest.fixture(scope='class')
def note_params():
    params = dict(description='description',
                  notifier='email-notifier',
                  to='jsmith@email.com',
                  subject='test')
    params['from'] = 'fbar@email.com'
    return params


@pytest.fixture(scope='class')
def plugin():
    pg = mock.MagicMock(spec=NotificationPlugin,
                        __plugin_name__='email-notifier')
    pg.notify = mock.MagicMock(return_value=[])
    pg.validate = mock.MagicMock(return_value=[])
    return pg


@pytest.fixture(scope='class')
def note(plugin, note_params):
    note = mock.MagicMock(spec=Notification, name='Test-Note')
    plugin.notification = note
    note.notifier = plugin
    return note


@pytest.fixture(scope='class')
def note_emitter(note):
    ne = Notifier(note)
    return ne


class TestNotificationEmitter(object):

    @staticmethod
    def test_notification_emitter_constructor(note_emitter):
        assert isinstance(note_emitter, Notifier)

    @staticmethod
    def test_notification_emitter_notify(plugin, note_emitter):
        note_emitter.plugin = plugin
        note_emitter.notify()
        plugin.notify.assert_called()

    @staticmethod
    def test_notification_emitter_validate(plugin, note_emitter):
        note_emitter.plugin = plugin
        note_emitter.validate()
        plugin.validate.assert_called()

    @staticmethod
    def test_notification_emitter_notify_exception(plugin, note_emitter):
        plugin.notify.side_effect = Exception('Mock Notify Failure')
        note_emitter.plugin = plugin
        with pytest.raises(Exception):
            note_emitter.notify()

    @staticmethod
    def test_notification_emitter_validate_exception(plugin, note_emitter):
        plugin.validate.side_effect = Exception('Mock Validate Failure')
        note_emitter.plugin = plugin
        with pytest.raises(Exception):
            note_emitter.validate()