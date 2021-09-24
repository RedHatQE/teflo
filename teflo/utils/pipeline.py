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
    teflo.utils.pipeline

    Module containing classes and functions for building pipelines of resources
    and tasks for teflo to run.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from collections import namedtuple
from teflo.resources.scenario import Scenario
from teflo.utils.scenario_graph import ScenarioGraph

from ..constants import TASKLIST, NOTIFYSTATES
from ..exceptions import TefloError
from ..helpers import fetch_assets, get_core_tasks_classes, fetch_executes, filter_actions_on_failed_status, \
    set_task_class_concurrency, filter_resources_labels, filter_notifications_to_skip, filter_notifications_on_trigger

from ..tasks import CleanupTask


class PipelineFactory(object):

    @staticmethod
    def get_pipeline(task):
        if task in TASKLIST:
            return PipelineBuilder(task)
        else:
            return NotificationPipelineBuilder(task)


class PipelineBuilder(object):
    """
    The primary class for building teflos pipelines to execute. A pipeline
    will exists for each teflo task. Within each pipeline consists of all
    resources for that specific task to process.
    """

    def __init__(self, name):
        """Constructor.

        :param name: teflo task name
        :type name: str
        """
        self._name = name

        # pipelines are a tuple data structure consisting of a name, type and
        # list of tasks
        self.pipeline_template = namedtuple(
            'Pipeline', ('name', 'type', 'tasks'))

    @property
    def name(self):
        """Return the pipeline name"""
        return self._name

    def is_task_valid(self):
        """Check if the pipeline task name is valid for teflo.

        :return: whether task is valid or not.
        :rtype: bool
        """
        try:
            TASKLIST.index(self.name)
        except ValueError:
            return False
        return True

    def task_cls_lookup(self):
        """Lookup the pipeline task class type.

        :return: the class associated for the pipeline task.
        :rtype: class
        """
        for cls in get_core_tasks_classes():
            if cls.__task_name__ == self.name:
                return cls
        raise TefloError('Unable to lookup task %s class.' % self.name)

    def build(self, scenario: Scenario, teflo_options, scenario_graph: ScenarioGraph = None):
        """Build teflo pipeline.

        This method first collects scenario tasks and resources for each scenario(child and master). It filters out
        specific resources for the scenario based on if labels or skip_labels are provided in teflo options.
        If no labels/ skip_labels are provided all resources for that scenario are picked.
        Then for each of the resource/scenario task the method checks if that resource/scenario tasks has any tasks
        with name matching the name for self.task(the task for which the pipeline is getting built). If it has then that
        tasks gets added to the pipeline and that gets returned

        :param scenario: teflo scenario object containing all scenario
               data.
        :type scenario: scenario object
        :param teflo_options: extra options provided during teflo run
        :type teflo_options: dict
        :return: teflo pipeline to run for the given task for all the scenarios
        :rtype: namedtuple
        """

        # pipeline init
        pipeline = self.pipeline_template(
            self.name,
            self.task_cls_lookup(),
            list()
        )

        scenario_get_tasks = list()
        scenario_get_tasks.extend([item for item in getattr(scenario, 'get_tasks')()])

        # Collecting resources based on task type
        if self.name.lower() in ['validate', 'provision', 'cleanup']:
            # scenario resource
            for task in scenario_get_tasks:
                if task['task'].__task_name__ == self.name:
                    pipeline.tasks.append(set_task_class_concurrency(task, task['resource']))

            # asset resource filtered based on labels
            for asset in filter_resources_labels(scenario.get_assets(), teflo_options):
                for task in asset.get_tasks():
                    if task['task'].__task_name__ == self.name:
                        pipeline.tasks.append(set_task_class_concurrency(task, asset))

        if self.name.lower() in ['validate', 'orchestrate', 'cleanup']:
            # action resource
            # get action resource based on if its status
            # check if cleanup task do NOT filter by status
            if self.name != 'cleanup':
                scenario_actions = filter_actions_on_failed_status(scenario.get_actions())
            else:
                scenario_actions = scenario.get_actions()
            # action resource filtered  based on labels
            for action in filter_resources_labels(scenario_actions, teflo_options):
                for task in action.get_tasks():
                    if task['task'].__task_name__ == self.name:
                        # fetch & set hosts for the given action task
                        task = fetch_assets(scenario_graph.get_assets(), task)
                        pipeline.tasks.append(set_task_class_concurrency(task, action))

        if self.name.lower() in ['validate', 'execute']:
            # execute resource filtered  based on labels
            for execute in filter_resources_labels(scenario.get_executes(), teflo_options):
                for task in execute.get_tasks():
                    if task['task'].__task_name__ == self.name:
                        # fetch & set hosts for the given executes task
                        task = fetch_assets(scenario_graph.get_assets(), task)
                        pipeline.tasks.append(set_task_class_concurrency(task, execute))

        if self.name.lower() in ['validate', 'report']:
            # report resource filtered  based on labels
            for report in filter_resources_labels(scenario.get_reports(), teflo_options):
                for task in report.get_tasks():
                    if task['task'].__task_name__ == self.name:
                        # fetch & set hosts and executes for the given reports task
                        task = fetch_executes(scenario_graph.get_executes(), scenario_graph.get_assets(), task)
                        pipeline.tasks.append(set_task_class_concurrency(task, report))

        if self.name.lower() in ['validate']:
            # notification resource
            for notification in filter_notifications_to_skip(scenario.get_notifications(), teflo_options):
                for task in notification.get_tasks():
                    if task['task'].__task_name__ == self.name:
                        task['resource'].scenario = scenario
                        pipeline.tasks.append(task)

        # reverse the order of the tasks to be executed for cleanup task
        if self.name == CleanupTask.__task_name__:
            pipeline.tasks.reverse()

        return pipeline


class NotificationPipelineBuilder(PipelineBuilder):

    """
    The primary class for building teflos notification pipelines to execute.
    """

    def __init__(self, trigger):

        super(NotificationPipelineBuilder, self).__init__('notify')
        self.trigger = trigger

    def is_task_valid(self):
        """Check if the pipeline task name is valid for teflo.

        :return: whether task is valid or not.
        :rtype: bool
        """
        try:
            NOTIFYSTATES.index(self.trigger)
        except ValueError:
            return False
        return True

    def build(self, scenario: Scenario, teflo_options, scenario_graph: ScenarioGraph = None):
        """Build teflo notification pipeline.

        This method first collects scenario tasks and resources for each scenario(child and master). It filters out
        specific resources for the scenario based on if labels or skip_labels are provided in teflo options.
        If no labels/ skip_labels are provided all resources for that scenario are picked.
        Then for each of the resource/scenario task the method checks if that resource/scenario tasks has any tasks
        with name matching the name for self.task(the task for which the pipeline is getting built). If it has then that
        tasks gets added to the pipeline and that gets returned

        :param scenario: teflo scenario object containing all scenario
               data.
        :type scenario: scenario object
        :param teflo_options: extra options provided during teflo run
        :type teflo_options: dict
        :return: teflo notification pipeline to run for the given task for all the scenarios
        :rtype: namedtuple
        """

        # pipeline init
        pipeline = self.pipeline_template(
            self.name,
            self.task_cls_lookup(),
            list()
        )

        # TODO: Scenario Graph related
        # We should allow customer to configure wheather they want to send notification with the information
        # from the whole scenario graph or just the current scenario, we only allow the current scenario for
        # this moment, for notification with failed/passed task information from whole scenario graph to be
        # Added

        # get notifications
        scenario_notifications = []
        scenario: Scenario
        # for scenario in scenario_graph:
        if getattr(scenario, "passed_tasks", None) is not None and getattr(scenario,
                                                                            "failed_tasks", None) is not None:

            scenario_notifications.extend(
                [item for item in filter_notifications_to_skip(scenario.get_notifications(),
                                                                                            teflo_options)])
            scenario_notifications = [item for item in
                                        filter_notifications_on_trigger(self.trigger, scenario_notifications,
                                                                        getattr(scenario, 'passed_tasks'),
                                                                        getattr(scenario, 'failed_tasks'))
                                      ]

            # notification resource

        for notification in scenario_notifications:
            for task in notification.get_tasks():
                if task['task'].__task_name__ == self.name:
                    task['resource'].scenario = scenario
                    pipeline.tasks.append(task)

        return pipeline
