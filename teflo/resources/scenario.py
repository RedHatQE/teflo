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
    teflo.resources.scenario

    Module used for building teflo scenario compound. Every teflo object
    has one scenario which has additional compounds associated to it.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import errno
import os
import yaml
from collections import OrderedDict
from pykwalify.errors import CoreError, SchemaError

from .actions import Action
from .executes import Execute
from .assets import Asset
from .reports import Report
from .notification import Notification
from ..constants import SCENARIO_SCHEMA, SCHEMA_EXT, \
    SET_CREDENTIALS_OPTIONS
from ..core import Inventory, TefloResource
from ..exceptions import ScenarioError

from ..helpers import gen_random_str, schema_validator
from ..tasks import ValidateTask
from ..utils.resource_checker import ResourceChecker


class Scenario(TefloResource):
    """
    The scenario resource class. It is the core resource which makes up the
    teflo compound. A scenario consists of multiple compounds of 'resources'.
    Those compounds make up the scenario which derive tasks for the scenario
    to be processed.
    """

    _valid_tasks_types = ['validate']

    _fields = [
        'name',         # the name of the scenario
        'description',  # a brief description of what the scenario is,
        'resource_check',    # external dependency check resources
        'overall_status',
        'passed_tasks',
        'failed_tasks',
        'remote_workspace'
    ]

    def __init__(self,
                 config=None,
                 name=None,
                 parameters={},
                 validate_task_cls=ValidateTask,
                 path: str = "",
                 inventory_object: Inventory = Inventory,
                 **kwargs):
        """Constructor.

        :param config: teflo configuration
        :type config: dict
        :param name: scenario name
        :type name: str
        :param parameters: content which makes up the scenario
        :type parameters: dict
        :param validate_task_cls: teflos validate task class
        :type validate_task_cls: object
        :param kwargs: additional key:value(s)
        :type kwargs: dict
        :param path: scenario file path
        :type name: str
        """
        super(Scenario, self).__init__(config=config, name=name, **kwargs)
        self._path = path
        self._fullpath = ""
        self._inventory: Inventory = inventory_object
        # set the scenario name attribute
        if not name:
            self._name = gen_random_str(15)
        else:
            self._name = name

        # set the scenario description attribute
        self._description = parameters.pop('description', None)

        # resource check dictionary , for external dependency checks, or custom validation scripts and playbooks
        self.resource_check = parameters.pop('resource_check', {})

        # set resource attributes
        self._assets = list()
        self._actions = list()
        self._executes = list()
        self._reports = list()
        self._notifications = list()
        self._yaml_data = dict()
        # Properties to take care of included scenarios
        self._child_scenarios = list()
        self._included_scenario_path = list()

        self._remote_workspace = list()
        self._scenario_graph = None

        self._passed_tasks = list()
        self._failed_tasks = list()

        # set the teflo task classes for the scenario
        self._validate_task_cls = validate_task_cls

        # create the runtime data folder for the scenario life cycle
        # TODO: cleanup task should remove this directory after report task
        try:
            if not os.path.exists(self.data_folder):
                os.makedirs(self.data_folder)
        except OSError as ex:
            if ex.errno == errno.EACCES:
                raise ScenarioError('You do not have permission to create'
                                    ' the workspace.')
            else:
                raise ScenarioError('Error creating scenario workspace: '
                                    '%s' % ex)

        # reload construct task methods
        self.reload_tasks()

        # load the parameters set into the object itself
        if parameters:
            self.load(parameters)

    def __str__(self) -> str:
        return "Scenario(\"%s\")" % self.name

    def get_all_resources(self):
        all_resources = list()

        # The order is like below so we always execute resources in below order for a single scenario node

        all_resources.extend([item for item in self.get_assets()])
        all_resources.extend([item for item in self.get_actions()])
        all_resources.extend([item for item in self.get_executes()])
        all_resources.extend([item for item in self.get_reports()])
        all_resources.extend([item for item in self.get_notifications()])
        return all_resources

    def get_assets(self):
        return getattr(self, 'assets')

    def get_actions(self):
        return getattr(self, 'actions')

    def get_executes(self):
        return getattr(self, 'executes')

    def get_reports(self):
        return getattr(self, 'reports')

    def get_notifications(self):
        return getattr(self, 'notifications')

    def get_resource_idx(self, item):
        """
        Get the idx of the resource in its corresponding list.
        :param item:
        :return:
        """
        if isinstance(item, Asset):
            if self._assets.__contains__(item):
                return self._assets.index(item)
            else:
                return None
        elif isinstance(item, Action):
            if self._actions.__contains__(item):
                return self._actions.index(item)
            else:
                return None
        elif isinstance(item, Execute):
            if self._executes.__contains__(item):
                return self._executes.index(item)
            else:
                return None
        elif isinstance(item, Report):
            if self._reports.__contains__(item):
                return self._reports.index(item)
            else:
                return None
        elif isinstance(item, Notification):
            if self._notifications.__contains__(item):
                return self._notifications.index(item)
            else:
                return None
        else:
            raise ValueError('Resource must be of a valid Resource type.'
                             'Check the type of the given item: %s' % item)

    def replace_resource(self, item, idx):
        """replace a scenario resource in its corresponding list.

      :param item: resource
      :type item: object
      :param idx: index of resource list
      :type idx: int
      """
        if isinstance(item, Asset):
            self._assets[idx] = item
        elif isinstance(item, Action):
            self._actions[idx] = item
        elif isinstance(item, Execute):
            self._executes[idx] = item
        elif isinstance(item, Report):
            self._reports[idx] = item
        elif isinstance(item, Notification):
            self._notifications[idx] = item
        else:
            raise ValueError('Resource must be of a valid Resource type.'
                             'Check the type of the given item: %s' % item)

    def add_resource(self, item, idx=None):
        """Add a scenario resource to its corresponding list.

        :param item: resource data
        :type item: object
        :param idx: index of resource list
        :type idx: int
        """
        if isinstance(item, Asset):
            if idx is not None:
                cur_idx = self.get_resource_idx(item)
                if cur_idx is not None:
                    if idx != cur_idx:
                        idx = cur_idx
                    self.replace_resource(item=item, idx=idx)
                else:
                    self._assets.insert(idx, item)
            else:
                self._assets.append(item)
        elif isinstance(item, Action):
            if idx is not None:
                cur_idx = self.get_resource_idx(item)
                if cur_idx is not None:
                    if idx != cur_idx:
                        idx = cur_idx
                    self.replace_resource(item=item, idx=idx)
                else:
                    self._actions.insert(idx, item)
            else:
                self._actions.append(item)
        elif isinstance(item, Execute):
            if idx is not None:
                cur_idx = self.get_resource_idx(item)
                if cur_idx is not None:
                    if idx != cur_idx:
                        idx = cur_idx
                    self.replace_resource(item=item, idx=idx)
                else:
                    self._executes.insert(idx, item)
            else:
                self._executes.append(item)
        elif isinstance(item, Report):
            if idx is not None:
                cur_idx = self.get_resource_idx(item)
                if cur_idx is not None:
                    if idx != cur_idx:
                        idx = cur_idx
                    self.replace_resource(item=item, idx=idx)
                else:
                    self._reports.insert(idx, item)
            else:
                self._reports.append(item)
        elif isinstance(item, Notification):
            if idx is not None:
                cur_idx = self.get_resource_idx(item)
                if cur_idx is not None:
                    if idx != cur_idx:
                        idx = cur_idx
                    self.replace_resource(item=item, idx=idx)
                else:
                    self._notifications.insert(idx, item)
            else:
                self._notifications.append(item)
        else:
            raise ValueError('Resource must be of a valid Resource type.'
                             'Check the type of the given item: %s' % item)

    def initialize_resource(self, item):
        """Initialize resource list.

        The primary purpose for this method is to wipe out an entire resource
        list if the resource passed in is a match. This is needed after
        blaster run is finished to update the scenarios resources objects.
        The reason to update them is because blaster uses multiprocessing which
        spawns new processes which may alter a scenario resource object given
        to it. Teflo then has no correlation with that updated resource.
        Which is why we need to refresh the scenario resources after run time.

        :param item: resource data
        :type item: object
        """
        if isinstance(item, Asset):
            self._assets = list()
        elif isinstance(item, Action):
            self._actions = list()
        elif isinstance(item, Execute):
            self._executes = list()
        elif isinstance(item, Report):
            self._reports = list()
        elif isinstance(item, Notification):
            self._notifications = list()
        else:
            raise ValueError('Resource must be of a valid Resource type.'
                             'Check the type of the given item: %s' % item)

    def reload_resources(self, tasks):
        """Reload scenario resources.

        This method is used to reload all resources after they have been processed (provisioned/orchestrate actions/
        execute tests/imported. Prior to adding the resource to the scenario, it filters the list by
        checking if the resource belongs to that scenario by comparing the names.

        When filtering we extract the resource, the data in rvalue, and the index the reource is at
        in the current resource list. If rvalue is present, then a provisioner with count
        feature was used so more new host resources will be created dynamically as part of this reload.
        If rvalue is not present then assume it is either a non-Asset resource or from a provisioning perspective
        count was either not used (which is equivalent of count==1), or using old provisioners so the original
        resource will be replaced with the updated resource in the task results lists.

        :param tasks: task data returned by blaster
        :type tasks: list
        """

        filtered_task_list = list()

        # This a brute force way of resolving the out of order of resources when using labels.
        # Prior to this change we would
        # 1. filter task list for resource type the scenarios has ownership
        # 2. filter existing resource list for the other resources of the same type that were filtered out by label
        # 3. re-init the resource list for the resource type with an empty array
        # 4. Append the resources that were updated from step 1
        # 5. Then append the rest of the resources from step 2
        # This lead to the resources being out of order in the results.yml
        #
        # Now we keep track of the index of the original resource so that we know where to replace/insert
        # the new resources or updated resource in the list. This will support when the resource list is
        # filtered using labels or status so we can retain proper ordering within the resource list during reload.
        #
        # New way
        # 1. filter task list for scenario resource ownership and it's index location in resource list
        # 2. if rvalue, then the first new resource will replace the original resource at the original index
        # 3. if rvalue, for each 1+N rvalue will have the index incremented by 1 and inserted at the new index
        #    pushing any resource that was at the index down the stack.
        # 4. if not rvalue, the updated resource will check to see if the original resource is at the previous index
        #    or at a new index (becaue it's been pushed down the stack) and replace the original resource accordingly.

        # TODO: Simplify the filtering of resources when resources implement __eq__/__hash__
        filtered_task_list.extend(
            [(task, self.get_resource_idx(task.get('asset')))
             for task in tasks if task.get('asset') and getattr(task.get('asset'), 'name')
             in [h.name for h in self.assets]]
        )
        filtered_task_list.extend(
            [(task, self.get_resource_idx(task.get('package')))
             for task in tasks if isinstance(task.get('package'), Report) and (getattr(task.get('package'), 'name')
                                                                               in [r.name for r in self.reports])]
        )

        filtered_task_list.extend(
            [(task, self.get_resource_idx(task.get('package'))) for task in tasks if
             isinstance(task.get('package'), Execute) and (getattr(task.get('package'), 'name')
                                                           in [r.name for r in self.executes])]
        )

        filtered_task_list.extend(
            [(task, self.get_resource_idx(task.get('package')))
             for task in tasks if isinstance(task.get('package'), Action) and (getattr(task.get('package'), 'name')
                                                                               in [r.name for r in self.actions])]
        )

        for res, rvalue, idx in [(res, item['rvalue'], idx) for task, idx in filtered_task_list
                                 for res in [task.get(r) for r in ['asset', 'package'] if r in task.keys()]
                                 for item in task.get('methods')]:
            if rvalue is not None:
                self.load_resources(Asset, rvalue, idx)
            else:
                self.add_resource(res, idx)

        return

    @property
    def name(self):
        """Scenario object name
        :return: scenario name
        :rtype: basestring
        """
        return self._name

    @name.setter
    def name(self, value):
        raise ValueError("you cannot set name of the scenario")

    @property
    def yaml_data(self):
        """Scenario file content property.

        :return: scenario file content
        :rtype: list
        """
        return self._yaml_data

    @yaml_data.setter
    def yaml_data(self, value):
        """Set scenario file content property."""
        self._yaml_data = value

    @property
    def assets(self):
        """Hosts property

        :return: host resources associated to the scenario
        :rtype: list
        """
        return self._assets

    @assets.setter
    def assets(self, value):
        """Set asset property."""
        raise ValueError('You can not set assets directly.'
                         'Use function ~Scenario.add_assets')

    def add_assets(self, host):
        """Add host resources to the scenario.

        :param host: host resource
        :type host: object
        """
        if not isinstance(host, Asset):
            raise ValueError('Asset must be of type %s ' % type(Asset))
        self._assets.append(host)

    @property
    def actions(self):
        """Actions property.

        :return: action resources associated to the scenario
        :rtype: list
        """
        return self._actions

    @actions.setter
    def actions(self, value):
        """Set actions property."""
        raise ValueError('You can not set actions directly.'
                         'Use function ~Scenario.add_actions')

    def add_actions(self, action):
        """Add action resources to the scenario.

        :param action: action resource
        :type action: object
        """
        if not isinstance(action, Action):
            raise ValueError('Action must be of type %s ' % type(Action))
        self._actions.append(action)

    @property
    def executes(self):
        """Executes property.

        :return: execute resources associated to the scenario
        :rtype: list
        """
        return self._executes

    @executes.setter
    def executes(self, value):
        """Set executes property."""
        raise ValueError('You can not set executes directly.'
                         'Use function ~Scenario.add_executes')

    def add_executes(self, execute):
        """Add execute resources to the scenario.

        :param execute: execute resource
        :type execute: object
        """
        if not isinstance(execute, Execute):
            raise ValueError('Execute must be of type %s ' % type(Execute))
        self._executes.append(execute)

    @property
    def included_scenario_path(self):
        """scenario path property.

        :return: scenario path property to the scenario
        :rtype: list
        """
        return self._included_scenario_path

    @included_scenario_path.setter
    def included_scenario_path(self, included_scenario_path):
        """scenario path property."""
        self._included_scenario_path.append(included_scenario_path)

    @property
    def remote_workspace(self):
        """remote_workspace property.

        :return: remote_workspace property to the scenario
        :rtype: list
        """
        return self._remote_workspace

    @remote_workspace.setter
    def remote_workspace(self, remote_workspace):
        """Set remote_workspace property."""
        self._remote_workspace = remote_workspace

    @property
    def reports(self):
        """Reports property.

        :return: report resources associated to the scenario
        :rtype: list
        """
        return self._reports

    @reports.setter
    def reports(self, value):
        """Set report property."""
        raise ValueError('You can not set reports directly.'
                         'Use function ~Scenario.add_reports')

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self._path = path

    @property
    def fullpath(self):
        return self._fullpath

    @fullpath.setter
    def fullpath(self, fullpath):
        self._fullpath = fullpath

    @property
    def inventory(self):
        return self._inventory

    @inventory.setter
    def inventory(self, inventory: Inventory):
        self._inventory = inventory

    @property
    def child_scenarios(self):
        """
        List of child scenarios for the master scenario
        :rtype: List
        """
        return self._child_scenarios

    @child_scenarios.setter
    def child_scenarios(self, value):
        """Set child_scenarios property."""
        raise ValueError('You can not set child_scenarios directly.'
                         'Use function ~Scenario.add_child_scenario')

    def add_child_scenario(self, scenario):
        """Add child/included scenarios to the master scenario resource.
        :param scenario: scenario resource
        :type scenario: object
        """
        if not isinstance(scenario, Scenario):
            raise ValueError('scenario must be of type %s ' % type(Scenario))
        self._child_scenarios.append(scenario)

    def add_reports(self, report):
        """Add report resources to the scenario.

        :param report: report resource
        :type report: object
        """
        if not isinstance(report, Report):
            raise ValueError('Execute must be of type %s ' % type(Execute))
        self._reports.append(report)

    @property
    def notifications(self):
        """Notifications property.

        :return: notification resources associated to the scenario
        :rtype: list
        """
        return self._notifications

    @notifications.setter
    def notifications(self, value):
        """Set executes property."""
        raise ValueError('You can not set notifications directly.'
                         'Use function ~Scenario.add_notifications')

    @property
    def scenario_graph(self):
        """scenario_graph property for the resource"""
        return self._scenario_graph

    @scenario_graph.setter
    def scenario_graph(self, value):
        """set scenario_graph property"""
        self._scenario_graph = value

    @property
    def passed_tasks(self):
        """passed_tasks property for the scenario"""
        return self._passed_tasks

    @passed_tasks.setter
    def passed_tasks(self, value):
        """set passed_tasks property"""
        if not isinstance(value, list):
            raise ScenarioError("The scenario passed_tasks value needs to be a list")
        for task in value:
            if task not in self.passed_tasks:
                self._passed_tasks.append(task)

    @property
    def failed_tasks(self):
        """failed_tasks property for the scenario"""
        return self._failed_tasks

    @failed_tasks.setter
    def failed_tasks(self, value):
        """set failed_tasks property"""
        if not isinstance(value, list):
            raise ScenarioError("The scenario failed_tasks value needs to be a list")
        for task in value:
            if task not in self.failed_tasks:
                self._failed_tasks.append(task)

    def add_notifications(self, notification):
        """Add notifications resources to the scenario.

        :param notification: notifications resource
        :type notification: object
        """
        if not isinstance(notification, Notification):
            raise ValueError('Notification must be of type %s ' % type(Notification))
        self._notifications.append(notification)

    def validate(self):
        """Validate the scenario based on the default schema."""
        self.logger.debug('Validating scenario YAML file')

        if self.resource_check:
            self.logger.debug('Validating resource check section')
            rs = ResourceChecker(self, self.config)
            rs.validate_resources()

        msg = 'validated scenario YAML file against the schema!'

        try:
            schema_validator(schema_data=yaml.safe_load(self.yaml_data),
                             schema_files=[SCENARIO_SCHEMA],
                             schema_ext_files=[SCHEMA_EXT])
            self.logger.debug('Successfully %s' % msg)
        except (CoreError, SchemaError) as ex:
            self.logger.error('Unsuccessfully %s' % msg)
            raise ScenarioError(ex.msg)

    def profile(self):
        """Builds a profile which represents the scenario and its properties.

        :return: a dictionary representing the scenario
        :rtype: OrderedDict
        """
        profile = OrderedDict()
        profile['name'] = self.name
        profile['description'] = self.description
        profile['remote_workspace'] = self.remote_workspace
        if self.child_scenarios:
            profile['include'] = self.included_scenario_path
        profile['resource_check'] = self.resource_check
        profile['provision'] = [asset.profile() for asset in self.assets]
        profile['orchestrate'] = [action.profile() for action in self.actions]
        profile['execute'] = [execute.profile() for execute in self.executes]
        profile['report'] = [report.profile() for report in self.reports]
        profile['notifications'] = [notification.profile() for notification in self.notifications]
        for prop in ['overall_status', 'passed_tasks', 'failed_tasks']:
            if hasattr(self, prop):
                profile[prop] = getattr(self, prop)
        return profile

    def _construct_validate_task(self):
        """Constructs the validate task associated to the scenario.

        :return: validate task definition
        :rtype: dict
        """
        task = {
            'task': self._validate_task_cls,
            'name': str(self.name),
            'resource': self,
            'methods': self._req_tasks_methods
        }
        return task

    def load_resources(self, res_type, res_list, idx=None):
        """
        Load the resource in the scenario list of `res_type`.

        The scenario holds a list of each resource type: hosts, actions,
        reports, etc. This function takes what type of resource is in
        list it calls ~self.scenario.add_resource for each item in the
        list of the given resources.

        For example, if we call load_resources(Asset, asset_list), the
        function will go through each item in the list, create the
        resource with Asset(parameter=item) and load it within the list
        ~self.asset.

        :param res_type: The type of resources the function will load into its
            list
        :param res_list: A list of resources dict
        :param idx: integer index where resource will be replaced/insert
        :return: None
        """
        # No resources defined, then exit
        if not res_list:
            return
        increment = False
        for item in res_list:
            if idx is not None and not increment:
                self.replace_resource(item=res_type(config=self.config, parameters=item), idx=idx)
                increment = True
                continue
            if idx is not None and increment:
                idx += 1
            self.add_resource(item=res_type(config=self.config, parameters=item), idx=idx)

    def graph_str(self, level=0):
        ret = "   " * level + "->" + self.path + "\n"
        child: Scenario
        for child in self.child_scenarios:
            ret += child.graph_str(level + 1)
        return ret
