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
    This is a generic interface that processes teflo's orchestration actions.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from ..core import LoggerMixin, TimeMixin
from ..exceptions import TefloOrchestratorError


class ActionOrchestrator(LoggerMixin, TimeMixin):
    """Action Orchestrator.

    This is a generic interface that processes teflo's orchestration actions.
    """
    __orchestrator_name__ = 'action-orchestrator'

    def __init__(self, package):
        """Constructor.

        Action resource

        :param action: teflo action resource
        :type action: object
        """
        self.action = package
        self.plugin = getattr(package, 'orchestrator')(package)

    def validate(self):
        """Validate the orchestration action params supplied are supported by the plugin."""

        try:
            self.plugin.validate()
        except Exception:
            raise
        else:
            self.logger.info('successfully validated scenario Action %s against the schema!' % self.plugin.action_name)

    def run(self):
        """Run method for orchestrator.
        """
        res = self.plugin.run()
        if res == 0:
            setattr(self.action, 'status', 0)
            self.logger.info('Orchestration passed : Successfully completed orchestrate action: %s.'
                             % self.plugin.action_name)
        else:
            setattr(self.action, 'status', 1)
            raise TefloOrchestratorError("Orchestration failed : Failed to perform  %s" % self.plugin.action_name)
