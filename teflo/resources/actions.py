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
    teflo.resources.actions

    Module used for building teflo action compounds. An action's main goal
    is to perform some sort of work.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from copy import copy

from .._compat import string_types
from ..constants import ORCHESTRATOR
from ..core import TefloResource
from ..orchestrators import ActionOrchestrator
from ..helpers import get_orchestrator_plugin_class, \
    get_orchestrators_plugin_list
from ..exceptions import TefloActionError
from ..tasks import OrchestrateTask, ValidateTask, CleanupTask
from collections import OrderedDict


class Action(TefloResource):
    """
    The action resource class. The teflo compound can contain x amount of
    actions. Their primary responsibility is to do some sort of work. Actions
    can handle any sort of task to be processed. Most of the time you will
    see actions consisting of the following:
        - System configuration
        - Product installation/configuration
        - Test setup (test framework installation/configuration)

    Each action has an associated orchestrator. The orchestrator is what
    processes (completes) the given action.
    """

    _valid_tasks_types = ['validate', 'orchestrate', 'cleanup']
    _fields = ['name', 'description', 'orchestrator', 'hosts', 'labels', 'status' 'orchestrate_timeout',
               'cleanup_timeout', 'validate_timeout']

    def __init__(self,
                 config=None,
                 name=None,
                 parameters=dict,
                 validate_task_cls=ValidateTask,
                 orchestrate_task_cls=OrchestrateTask,
                 cleanup_task_cls=CleanupTask,
                 **kwargs):
        """Constructor.

        The primary focus of the constructor is to build the action object
        containing all necessary parts to process the action.

        :param config: teflo configuration
        :type config: dict
        :param name: action resource name
        :type name: str
        :param parameters: content which makes up the action resource
        :type parameters: dict
        :param validate_task_cls: teflos validate task class
        :type validate_task_cls: object
        :param orchestrate_task_cls: teflos orchestrate task class
        :type orchestrate_task_cls: object
        :param cleanup_task_cls: teflos cleanup task class
        :type cleanup_task_cls: object
        :param kwargs: additional key:value(s)
        :type kwargs: dict
        """
        super(Action, self).__init__(config=config, name=name, **kwargs)

        # set the action resource name
        if name is None:
            self._name = parameters.pop('name', None)
            if self._name is None:
                raise TefloActionError('Unable to build action object. Name'
                                        ' field missing!')
        else:
            self._name = name

        # set the timeout for VALIDATE
        try:
            if parameters.get('validate_timeout') is not None:
                self._validate_timeout = parameters.pop("validate_timeout")
            else:
                self._validate_timeout = config["TIMEOUT"]["VALIDATE"]
        except TypeError:
            self.logger.error("No teflo.cfg found,  so no timeout will be set")
            self._validate_timeout = 0

        # set the timeout for ORCHESTRATE
        try:
            if parameters.get('orchestrate_timeout') is not None:
                self._orchestrate_timeout = parameters.pop("orchestrate_timeout")
            else:
                self._orchestrate_timeout = config["TIMEOUT"]["ORCHESTRATE"]
        except TypeError:
            self.logger.error("No teflo.cfg found,  so no timeout will be set")
            self._orchestrate_timeout = 0

        # set the timeout for cleanup
        try:
            if parameters.get('cleanup_timeout') is not None:
                self._cleanup_timeout = parameters.pop("cleanup_timeout")
            else:
                self._cleanup_timeout = config["TIMEOUT"]["CLEANUP"]
        except TypeError:
            self.logger.error("No teflo.cfg found,  so no timeout will be set")
            self._cleanup_timeout = 0

        # set the action description
        self._description = parameters.pop('description', None)

        # each action will have x number of hosts associated to it. lets
        # associate the list of hosts to the action object itself. currently
        # the hosts are strings, when teflo builds the pipeline, they will
        # be updated with their corresponding host object.
        self.hosts = parameters.pop('hosts')
        if self.hosts is None:
            raise TefloActionError('Unable to associate hosts to action: %s.'
                                    'No hosts defined!' % self._name)

        # convert the hosts into list format if hosts defined as str format
        if isinstance(self.hosts, string_types):
            self.hosts = self.hosts.replace(' ', '').split(',')

        # every action has a mandatory orchestrator, lets set it
        orchestrator_name = parameters.pop('orchestrator', ORCHESTRATOR)

        if orchestrator_name not in get_orchestrators_plugin_list():
            raise TefloActionError('Orchestrator: %s is not supported!' %
                                    orchestrator_name)

        # now that we know the orchestrator, lets get the class
        self._orchestrator = get_orchestrator_plugin_class(orchestrator_name)

        # using plugin's method to get the schema keys and check if they are present in the parameters and then
        # set them as action's parameters
        if self.orchestrator:
            for p in getattr(self.orchestrator, 'get_schema_keys')():
                if parameters.get(p, None):
                    setattr(self, p, parameters.get(p))
        else:
            raise TefloActionError('Orchestrator: %s plugin was not found!' %
                                    orchestrator_name)

        # set up status code
        self._status = parameters.pop('status', 0)

        # set labels
        setattr(self, 'labels', parameters.pop('labels', []))

        # ******** CLEANUP ACTIONS ******** #
        # check if the action requires any cleanup actions prior to host
        # deletion
        self.cleanup = None
        self.cleanup_def = parameters.pop('cleanup', None)

        if self.cleanup_def:
            # create the cleanup sub-action for this parent action
            self.cleanup = Action(
                config=self.config,
                parameters=copy(self.cleanup_def)
            )

        # set the teflo task classes for the resource
        self._validate_task_cls = validate_task_cls
        self._orchestrate_task_cls = orchestrate_task_cls
        self._cleanup_task_cls = cleanup_task_cls

        # reload construct task methods
        self.reload_tasks()

        # load the parameters set into the object itself
        if parameters:
            self.load(parameters)

    @property
    def orchestrator(self):
        """Orchestrator property.

        :return: orchestrator class object
        :rtype: object
        """
        return self._orchestrator

    @orchestrator.setter
    def orchestrator(self, value):
        """Set orchestrator property."""
        raise AttributeError('Orchestrator class property cannot be set.')

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    def profile(self):
        """Builds a profile for the action resource.

        :return: the action profile
        :rtype: OrderedDict
        """
        profile = OrderedDict()
        profile['name'] = self.name
        profile['description'] = self.description
        if isinstance(self.orchestrator, string_types):
            profile['orchestrator'] = self.orchestrator
        else:
            profile['orchestrator'] = getattr(
                    self.orchestrator, '__plugin_name__')
            #
        # set the action's hosts
        if all(isinstance(item, string_types) for item in self.hosts):
            profile.update(hosts=[host for host in self.hosts])
        else:
            profile.update(dict(hosts=[host.name for host in self.hosts]))

        # Update profile with all the parameters for the orchestrator
        if not isinstance(self.orchestrator, string_types):
            profile.update(getattr(self.orchestrator, 'build_profile')(self))

        if self.cleanup_def:
            profile.update({'cleanup': self.cleanup_def})

        # set labels
        profile.update({'labels': self.labels})
        profile.update({'status': self.status})

        return profile

    def validate(self):
        """Validate the action object using the orchestrator plugin's validate method."""
        getattr(ActionOrchestrator(self), 'validate')()

    def _construct_validate_task(self):
        """Constructs the validate task associated to the action resource.

        :returns: validate task definition
        :rtype: dict
        """
        task = {
            'task': self._validate_task_cls,
            'name': str(self.name),
            'resource': self,
            'methods': self._req_tasks_methods,
            'timeout': self._validate_timeout
        }
        return task

    def _construct_orchestrate_task(self):
        """Constructs the orchestrate task associated to the action.

        :return: orchestrate task definition
        :rtype: dict
        """
        task = {
            'task': self._orchestrate_task_cls,
            'name': str(self.name),
            'package': self,
            'msg': '   running orchestration %s for %s' % (
                self.name, self.hosts),
            'methods': self._req_tasks_methods,
            "time_out": self._orchestrate_timeout
        }
        return task

    def _construct_cleanup_task(self):
        """Constructs the clean up task associated to the action.

        :return: clean up task definition
        :rtype: dict
        """
        task = {
            'task': self._cleanup_task_cls,
            'name': str(self.name),
            'package': self,
            'msg': '   running clean up %s for %s' % (
                self.name, self.hosts),
            'methods': self._req_tasks_methods,
            "timeout": self._cleanup_timeout

        }
        return task
