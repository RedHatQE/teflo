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
    teflo.tasks.cleanup

    Here you add brief description of what this module is about

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import TefloTask
from ..exceptions import TefloOrchestratorError
from ..provisioners import AssetProvisioner
from teflo.orchestrators import ActionOrchestrator


class CleanupTask(TefloTask):
    """Cleanup task."""
    __concurrent__ = False
    __task_name__ = 'cleanup'

    def __init__(self, msg, asset=None, package=None, **kwargs):
        """Constructor.

        :param msg: task message
        :type msg: str
        :param asset: asset reference
        :type asset: object
        :param package: package reference
        :type package: object
        :param kwargs: additional keyword arguments
        :type kwargs: dict
        """
        super(CleanupTask, self).__init__(**kwargs)

        # set attributes
        self.msg = msg
        self.asset = asset
        self.package = package

    def _get_orchestrator_instance(self):
        """Get the orchestrator instance to perform clean up actions with.

        :return: orchestrator class instance
        :rtype: object
        """
        # set package attributes to get actual asset objects over strings
        cleanup = getattr(self.package, 'cleanup')
        setattr(cleanup, 'all_hosts', getattr(self.package, 'all_hosts'))
        setattr(cleanup, 'hosts', getattr(self.package, 'hosts'))

        # create the orchestrator plugin object
        return ActionOrchestrator(cleanup)

    def run(self):
        """Run.

        This method is the main entry point to the task.
        """
        self.logger.info(self.msg)

        # **** TASKS BELOW ONLY SHOULD BE RELATED TO THE ORCHESTRATOR ****
        if self.package and getattr(self.package, 'cleanup') is not None:
            # get the orchestrator to invoke
            orchestrator = self._get_orchestrator_instance()

            # perform final system configuration against test systems
            try:
                getattr(orchestrator, 'run')()
            except TefloOrchestratorError:
                self.logger.warning(
                    'Errors raised during cleanup orchestrate tasks are '
                    'silenced. This allows all tasks to run through their '
                    'cleanup tasks.'
                )

        # **** TASKS BELOW ONLY SHOULD BE RELATED TO THE PROVISIONER ****
        if self.asset:
            if not getattr(self.asset, 'is_static'):
                provisioner = AssetProvisioner(self.asset)
                # teardown the asset
                getattr(provisioner, 'delete')()
            else:
                self.logger.warning('Asset %s is static, skipping teardown.' %
                                    getattr(self.asset, 'name'))
