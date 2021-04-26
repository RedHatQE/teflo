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
    teflo.tasks.notification

    Here you add brief description of what this module is about

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import TefloTask
from ..notifiers import Notifier


class NotificationTask(TefloTask):
    """Notification task."""
    __task_name__ = 'notify'

    def __init__(self, msg, resource, **kwargs):
        """Constructor.

        :param resource: resource reference
        :type resource: object
        :param kwargs: additional keyword arguments
        :type kwargs: dict
        """
        super(NotificationTask, self).__init__(**kwargs)
        self.msg = msg
        self.resource = resource
        self.notifier = Notifier(resource)

    def run(self):
        """Run.

        This method is the main entry point to the task.
        """

        try:
            # validate the given resource
            self.logger.info(self.msg)
            self.notifier.notify()
        except Exception:
            self.logger.error('Notification failed.')
            stackmsg = self.get_formatted_traceback()
            self.logger.error(stackmsg)
            raise
