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
    teflo.provisioners.host_provisioner

    Base provisioner module to be used as an interface for implementing any
    new provisioners within teflo.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from pprint import pformat

from teflo.core import LoggerMixin, TimeMixin
from teflo.helpers import mask_credentials_password
import copy
import json


class Notifier(LoggerMixin, TimeMixin):
    """Notification Emitter class.

    This class is the generic interface that sends out notifications

    """
    __notification_name__ = 'notifier'

    def __init__(self, notification):
        """Constructor.

        Notification resource

        :param notification: teflo notification resource
        :type notification: object
        """

        self.plugin = getattr(notification, 'notifier')(notification)

    def validate(self):
        """

        validate the params provided are supported by the plugin
        :return:
        """
        try:
            self.plugin.validate()
        except Exception:
            raise
        else:
            self.logger.info('successfully validated scenario Notification against the schema!')

    def notify(self):
        """Notify method. Calls the plugin notify method
        """
        name = getattr(getattr(self.plugin, 'notification'), 'name')
        try:
            self.logger.info('Triggering notification %s.' % name)
            self.plugin.notify()
            self.logger.info('Successfully triggered notification %s.' % name)

        except Exception as ex:
            self.logger.error(ex)
            raise
