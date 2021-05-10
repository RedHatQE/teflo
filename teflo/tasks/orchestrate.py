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
    teflo.tasks.install

    Here you add brief description of what this module is about

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import TefloTask
from teflo.orchestrators import ActionOrchestrator


class OrchestrateTask(TefloTask):
    """Orchestrate task."""
    __task_name__ = 'orchestrate'
    __concurrent__ = False

    def __init__(self, msg, package, **kwargs):
        """Constructor.

        :param msg: task message
        :type msg: str
        :param package: package reference
        :type package: object
        :param kwargs: additional keyword arguments
        :type kwargs: dict
        """
        super(OrchestrateTask, self).__init__(**kwargs)
        self.msg = msg

        # create the orchestrator object
        self.orchestrator = ActionOrchestrator(package)

    def run(self):
        """Run.

        This method is the main entry point to the task.
        """
        self.logger.info(self.msg)
        try:
            # run the configuration with the given orchestrator
            self.orchestrator.run()
        except Exception as ex:
            self.logger.error('Failed to run orchestration %s ' % self.name)
            stackmsg = self.get_formatted_traceback()
            self.logger.error(ex)
            self.logger.error(stackmsg)
            raise
