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
    teflo.tasks.validate

    Here you add brief description of what this module is about

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import TefloTask


class ValidateTask(TefloTask):
    """Validate task."""
    __task_name__ = 'validate'

    def __init__(self, resource, **kwargs):
        """Constructor.

        :param resource: resource reference
        :type resource: object
        :param kwargs: additional keyword arguments
        :type kwargs: dict
        """
        super(ValidateTask, self).__init__(**kwargs)
        self.resource = resource

    def run(self):
        """Run.

        This method is the main entry point to the task.
        """
        self.logger.info(
            'Validating %s (%s)', self.resource.__class__, self.resource.name
        )
        try:
            # validate the given resource
            self.resource.validate()
        except Exception:
            self.logger.error('Failed to validate %s' % self.resource.name)
            stackmsg = self.get_formatted_traceback()
            self.logger.error(stackmsg)
            raise
