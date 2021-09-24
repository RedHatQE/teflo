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
    teflo.resources.executes

    Module used for building teflo execute compounds. A execute's main goal
    is to run tests against the set of hosts for the scenario.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from .._compat import string_types
from ..core import TefloResource
from ..constants import EXECUTOR
from ..helpers import get_executor_plugin_class, \
    get_executors_plugin_list
from ..tasks import ExecuteTask, ValidateTask
from ..exceptions import TefloExecuteError
from collections import OrderedDict
from ..executors import ExecuteManager


class Execute(TefloResource):
    """
    The execute resource class.
    """

    _valid_tasks_types = ['validate', 'execute']
    # The fields (ansible_options, git, shell, and script) could have been
    # optional parameters for the runner executor; however, since this is
    # planned to be the main executor, it made sense to define them here
    # and not appending runner to those keys.  This can be changed if
    # there are more executors added.
    _fields = [
        'name',
        'description',
        'hosts',
        'ansible_options',
        'git',
        'ignore_rc',
        'valid_rc',
        'artifacts',
        'artifact_locations',
        'labels',
        'testrun_results',
        'artifacts_location',
        "execute_timeout",
        "validate_timeout"
    ]

    def __init__(self,
                 config=None,
                 name=None,
                 parameters: dict = {},
                 execute_task_cls=ExecuteTask,
                 validate_task_cls=ValidateTask,
                 **kwargs):
        """Constructor.

        :param config: teflo configuration
        :type config: dict
        :param name: execute resource name
        :type name: str
        :param parameters: content which makes up the execute resource
        :type parameters: dict
        :param execute_task_cls: teflos execute task class
        :type execute_task_cls: object
        :param validate_task_cls: teflos validate task class
        :type validate_task_cls: object
        :param kwargs: additional key:value(s)
        :type kwargs: dict
        """
        super(Execute, self).__init__(config=config, name=name, **kwargs)

        # set the timeout for VALIDATE
        try:
            if parameters.get('validate_timeout') is not None:
                self._validate_timeout = parameters.pop("validate_timeout")
            else:
                self._validate_timeout = config["TIMEOUT"]["VALIDATE"]
        except TypeError:
            self.logger.error("No teflo.cfg found,  so no timeout will be set")
            self._validate_timeout = 0

        # set the timeout for execution
        try:
            if parameters.get('execute_timeout') is not None:
                self._execute_timeout = parameters.pop("execute_timeout")
            else:
                self._execute_timeout = config["TIMEOUT"]["EXECUTE"]
        except TypeError:
            self.logger.error("No teflo.cfg found,  so no timeout will be set")
            self._execute_timeout = 0

        # set the execute resource name
        if name is None:
            self._name = parameters.pop('name', None)
            if self._name is None:
                raise TefloExecuteError('Unable to build execute object. Name'
                                         ' field missing!')
        else:
            self._name = name

        # set the execute description
        self._description = parameters.pop('description', None)

        # every execute has a mandatory executor, lets set it
        executor_name = parameters.pop('executor', EXECUTOR)

        if executor_name not in get_executors_plugin_list():
            raise TefloExecuteError('Executor: %s is not supported!' %
                                     executor_name)

        # get the executor class
        self._executor = get_executor_plugin_class(executor_name)

        # using plugin's method to get the schema keys and check if they are present in the parameters and then
        # set them as executor's parameters
        if self.executor:
            for p in getattr(self.executor, 'get_schema_keys')():
                if parameters.get(p, None):
                    setattr(self, p, parameters.get(p))
        else:
            raise TefloExecuteError('Executor: %s plugin was not found!' %
                                     executor_name)

        self.hosts = parameters.pop('hosts')
        if self.hosts is None:
            raise TefloExecuteError('Unable to associate hosts to executor:'
                                     '%s. No hosts defined!' % self._name)

        # convert the hosts into list format if hosts defined as str format
        if isinstance(self.hosts, string_types):
            self.hosts = self.hosts.replace(' ', '').split(',')

        # set labels
        setattr(self, 'labels', parameters.pop('labels', []))

        # set up status code
        self._status = parameters.pop('status', 0)

        self.artifacts = parameters.pop('artifacts', [])
        if self.artifacts:
            if isinstance(self.artifacts, string_types):
                self.artifacts = self.artifacts.replace(' ', '').split(',')

        self.artifact_locations = parameters.pop('artifact_locations', [])

        self.testrun_results = dict()

        # set the teflo task classes for the resource
        self._validate_task_cls = validate_task_cls
        self._execute_task_cls = execute_task_cls

        # reload construct task methods
        self.reload_tasks()

        # load the parameters into the object itself
        if parameters:
            self.load(parameters)

    @property
    def executor(self):
        """Executor property.

        :return: executor class object
        :rtype: object
        """
        return self._executor

    @executor.setter
    def executor(self, value):
        """Set executor property."""
        raise AttributeError('Executor class property cannot be set.')

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    def profile(self):
        """Build a profile for the execute resource.

        :return: the execute profile
        :rtype: OrderedDict
        """
        profile = OrderedDict()
        profile.update({'name': self.name})
        profile.update({'description': self.description})
        if isinstance(self.executor, string_types):
            profile.update({'executor': self.executor})
        else:
            profile.update({'executor': getattr(self.executor, '__executor_name__')})

        # set the execute's hosts
        if all(isinstance(item, string_types) for item in self.hosts):
            profile.update(hosts=[host for host in self.hosts])
        else:
            profile.update(dict(hosts=[host.name for host in self.hosts]))

        # update the profile with executor properties
        if not isinstance(self.executor, string_types):
            profile.update(getattr(self.executor, 'build_profile')(self))

        for item in getattr(self, '_fields'):
            if item == 'hosts':
                continue
            elif getattr(self, item, None):
                profile.update({item: getattr(self, item)})

        profile.update({'status': self.status})

        return profile

    def validate(self):
        """Validate the action object using the orchestrator plugin's validate method."""
        getattr(ExecuteManager(self), 'validate')()

    def _construct_validate_task(self):
        """Constructs the validate task associated to the execute resource.

        :return: validate task definition
        :rtype: dict
        """
        task = {
            'task': self._validate_task_cls,
            'name': str(self.name),
            'resource': self,
            'methods': self._req_tasks_methods,
            "timeout": self._validate_timeout
        }
        return task

    def _construct_execute_task(self):
        """Constructs the execute task associated to the execute resource.

        :return: execute task definition
        :rtype: dict
        """
        task = {
            'task': self._execute_task_cls,
            'name': str(self.name),
            'package': self,
            'msg': '   executing %s' % self.name,
            'methods': self._req_tasks_methods,
            "timout": self._execute_timeout
        }
        return task
