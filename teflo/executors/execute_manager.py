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

    This is a generic interface that processes teflo's execute tasks.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from ..core import LoggerMixin, TimeMixin
from ..exceptions import TefloExecuteError


class ExecuteManager(LoggerMixin, TimeMixin):
    """ The main executor for Teflo.

    The runner class provides three different types on how you can execute
    tests. Its intention is to be generic enough where you just need to supply
    your test commands and it will process them. All tests executed against
    remote hosts will be run through ansible.
    """

    __executor_name__ = 'execute_manager'

    def __init__(self, package):
        """Constructor.

        :param package: execute resource
        :type package: object
        """
        self.execute = package
        self.plugin = getattr(package, 'executor')(package)

        # # attribute defining overall status of test execution. why is this
        # # needed? when a test fails we handle the exception raised and call
        # # the method to archive test artifacts. once fetching artifacts is
        # # finished this status is used to fail teflo (if needed)
        # self.status = 0

    def validate(self):
        """Validate the executes params supplied are supported by the plugin."""

        try:
            self.plugin.validate()
        except Exception:
            raise
        else:
            self.logger.info('successfully validated scenario Execute resource %s against the schema!'
                             % self.plugin.execute_name)

    def run(self):

        """Run method for executor.
        """
        res = self.plugin.run()
        if res == 0:
            setattr(self.execute, 'status', 0)
            self.logger.info('Execute stage passed : Successfully completed execute task: %s.'
                             % self.plugin.execute_name)
        else:
            setattr(self.execute, 'status', 1)
            raise TefloExecuteError("Execute stage failed : Failed to perform %s" % self.plugin.execute_name)
