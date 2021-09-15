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
    tests.test_pipeline_class

    Unit tests for testing teflos pipeline builder class.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from teflo.utils.scenario_graph import ScenarioGraph
from teflo.resources.scenario import Scenario
import pytest
from teflo.exceptions import TefloError
from teflo.tasks import CleanupTask, ExecuteTask, ProvisionTask, \
    OrchestrateTask, ReportTask, ValidateTask, NotificationTask
from teflo.utils.pipeline import PipelineBuilder, NotificationPipelineBuilder, PipelineFactory
from teflo._compat import string_types
from teflo.resources import Asset


@pytest.fixture(scope='class')
def pipe_builder():
    return PipelineBuilder(name='validate')


@pytest.fixture(scope='class')
def invalid_pipe_builder():
    return PipelineBuilder(name='null')


@pytest.fixture(scope='class')
def notify_pipe_builder():
    return NotificationPipelineBuilder(trigger='on_start')


@pytest.fixture(scope='class')
def notify_invalid_pipe_builder():
    return NotificationPipelineBuilder(trigger='null')


class TestPipelineFactory(object):

    @staticmethod
    def test_get_default_pipeline():
        pb = PipelineFactory.get_pipeline('validate')
        assert isinstance(pb, PipelineBuilder)

    @staticmethod
    def test_get_notify_pipeline():
        pb = PipelineFactory.get_pipeline('on_start')
        assert isinstance(pb, NotificationPipelineBuilder)


class TestPipelineBuilder(object):
    @staticmethod
    def test_constructor(pipe_builder):
        assert isinstance(pipe_builder, PipelineBuilder)

    @staticmethod
    def test_name_property(pipe_builder):
        assert pipe_builder.name == 'validate'

    @staticmethod
    def test_verify_task_is_valid(pipe_builder):
        assert pipe_builder.is_task_valid()

    @staticmethod
    def test_verify_task_is_invalid(invalid_pipe_builder):
        assert not invalid_pipe_builder.is_task_valid()

    @staticmethod
    def test_valid_task_class_lookup(pipe_builder):
        cls = pipe_builder.task_cls_lookup()
        assert getattr(cls, '__task_name__') == pipe_builder.name

    @staticmethod
    def test_invalid_task_class_lookup(invalid_pipe_builder):
        with pytest.raises(TefloError) as ex:
            invalid_pipe_builder.task_cls_lookup()
        assert 'Unable to lookup task %s class.' % invalid_pipe_builder.name \
               in ex.value.args[0]

    @staticmethod
    def test_build_validate_task_pipeline(scenario):
        builder = PipelineBuilder(name='validate')
        pipeline = builder.build(scenario, teflo_options={})
        assert getattr(pipeline, 'name') == 'validate'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert getattr(pipeline, 'type') is ValidateTask

    @staticmethod
    def test_build_provision_task_pipeline(scenario):
        builder = PipelineBuilder(name='provision')
        pipeline = builder.build(scenario, teflo_options={})
        assert getattr(pipeline, 'name') == 'provision'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert getattr(pipeline, 'type') is ProvisionTask

    @staticmethod
    def test_build_orchestrate_task_pipeline(scenario):
        builder = PipelineBuilder(name='orchestrate')
        pipeline = builder.build(scenario, teflo_options={})
        assert getattr(pipeline, 'name') == 'orchestrate'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert getattr(pipeline, 'type') is OrchestrateTask

    @staticmethod
    def test_build_execute_task_pipeline(scenario):
        builder = PipelineBuilder(name='execute')
        pipeline = builder.build(scenario, teflo_options={})
        assert getattr(pipeline, 'name') == 'execute'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert getattr(pipeline, 'type') is ExecuteTask

    @staticmethod
    def test_build_report_task_pipeline(scenario):
        builder = PipelineBuilder(name='report')
        pipeline = builder.build(scenario, teflo_options={})
        assert getattr(pipeline, 'name') == 'report'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert getattr(pipeline, 'type') is ReportTask

    @staticmethod
    def test_build_cleanup_task_pipeline(scenario):
        builder = PipelineBuilder(name='cleanup')
        pipeline = builder.build(scenario, teflo_options={})
        assert getattr(pipeline, 'name') == 'cleanup'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert getattr(pipeline, 'type') is CleanupTask


# TODO: Scenario Graph related
# REFACTOR the tests below with scenario graph
# We should either write some new tests with scenario graph
# or reuse below tests

    # @staticmethod
    # def test_build_cleanup_task_pipeline_failed_orch_status(scenario1, action_resource_cleanup):
    #     """Validate that orchestrate tasks with a failed status aren't getting filtered for cleanup"""
    #     setattr(action_resource_cleanup, 'status', 1)
    #     scenario1.add_actions(action_resource_cleanup)
    #     builder = PipelineBuilder(name='cleanup')
    #     pipeline = builder.build(scenario1, teflo_options={})
    #     assert getattr(pipeline, 'name') == 'cleanup'
    #     assert isinstance(getattr(pipeline, 'tasks'), list)
    #     assert getattr(pipeline, 'type') is CleanupTask
    #     assert len([task for task in getattr(pipeline, 'tasks') if 'package' in task]) == 2

    # @staticmethod
    # def test_pipeline_with_asset_count_for_action(scenario1):
    #     builder = PipelineBuilder(name='orchestrate')
    #     pipeline = builder.build(scenario1, teflo_options={})
    #     tasks = getattr(pipeline, 'tasks')
    #     assert isinstance(getattr(tasks[0].get('package'), 'hosts')[-1], Asset)
    #     assert len(getattr(tasks[0].get('package'), 'hosts')) == 1
    #     assert getattr(getattr(tasks[0].get('package'), 'hosts')[-1], 'name') == 'host_0'

    # @staticmethod
    # def test_pipeline_with_asset_count_using_groups_for_execute(scenario1, asset3, execute2):
    #     scenario1.add_assets(asset3)
    #     scenario1.add_executes(execute2)
    #     builder = PipelineBuilder(name='execute')
    #     pipeline = builder.build(scenario1, teflo_options={})
    #     tasks = getattr(pipeline, 'tasks')
    #     assert isinstance(getattr(scenario1, 'executes')[0].hosts[-1], string_types)
    #     assert len(getattr(tasks[1].get('package'), 'hosts')) == 1
    #     assert getattr(getattr(tasks[1].get('package'), 'hosts')[-1], 'name') == 'host_3'

    # @staticmethod
    # def test_pipeline_with_label(scenario_labels):
    #     builder = PipelineBuilder(name='orchestrate')
    #     pipeline = builder.build(scenario_labels, teflo_options={'labels': ('label3',)})
    #     tasks = getattr(pipeline, 'tasks')
    #     assert isinstance(getattr(tasks[0].get('package'), 'hosts')[-1], Asset)
    #     assert len(getattr(tasks[0].get('package'), 'hosts')) == 1
    #     assert getattr(getattr(tasks[0].get('package'), 'hosts')[-1], 'name') == 'host_3'

    # @staticmethod
    # def test_pipeline_with_skip_label(scenario_labels):
    #     builder = PipelineBuilder(name='execute')
    #     pipeline = builder.build(scenario_labels, teflo_options={'skip_labels': ('label2',)})
    #     tasks = getattr(pipeline, 'tasks')
    #     assert isinstance(getattr(tasks[0].get('package'), 'hosts')[-1], Asset)
    #     assert len(getattr(tasks[0].get('package'), 'hosts')) == 1
    #     assert getattr(getattr(tasks[0].get('package'), 'hosts')[-1], 'name') == 'host_3'


class TestNotificationPipelineBuilder(object):
    @staticmethod
    def test_constructor(notify_pipe_builder):
        assert isinstance(notify_pipe_builder, NotificationPipelineBuilder)

    @staticmethod
    def test_name_property(notify_pipe_builder):
        assert notify_pipe_builder.name == 'notify'

    @staticmethod
    def test_verify_task_is_valid(notify_pipe_builder):
        assert notify_pipe_builder.is_task_valid()

    @staticmethod
    def test_verify_task_is_invalid(notify_invalid_pipe_builder):
        assert not notify_invalid_pipe_builder.is_task_valid()

    @staticmethod
    def test_valid_task_class_lookup(notify_pipe_builder):
        cls = notify_pipe_builder.task_cls_lookup()
        assert getattr(cls, '__task_name__') == notify_pipe_builder.name

    @staticmethod
    def test_build_on_start_notify_task_pipeline(scenario):
        setattr(scenario, 'overall_status', 0)
        setattr(scenario, 'passed_tasks', ['validate'])
        setattr(scenario, 'failed_tasks', [])
        builder = NotificationPipelineBuilder(trigger='on_start')
        pipeline = builder.build(scenario, teflo_options={})
        assert getattr(pipeline, 'name') == 'notify'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert len(getattr(pipeline, 'tasks')) == 1
        assert getattr(pipeline, 'type') is NotificationTask

    @staticmethod
    def test_build_on_complete_mixed_success_notify_task_pipeline(scenario):
        setattr(scenario, 'overall_status', 0)
        setattr(scenario, 'passed_tasks', ['validate'])
        setattr(scenario, 'failed_tasks', [])
        builder = NotificationPipelineBuilder(trigger='on_complete')
        pipeline = builder.build(scenario, teflo_options={})
        assert getattr(pipeline, 'name') == 'notify'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert len(getattr(pipeline, 'tasks')) == 1
        assert getattr(pipeline, 'type') is NotificationTask

    @staticmethod
    def test_build_on_complete_mixed_failure_notify_task_pipeline(scenario):
        setattr(scenario, 'overall_status', 0)
        setattr(scenario, 'passed_tasks', [])
        setattr(scenario, 'failed_tasks', ['validate'])
        builder = NotificationPipelineBuilder(trigger='on_complete')
        pipeline = builder.build(scenario, teflo_options={})
        assert getattr(pipeline, 'name') == 'notify'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert len(getattr(pipeline, 'tasks')) == 1
        assert getattr(pipeline, 'type') is NotificationTask

    @staticmethod
    def test_build_on_complete_on_success_notify_task_pipeline(scenario):
        setattr(scenario, 'overall_status', 0)
        setattr(scenario, 'passed_tasks', ['provision'])
        setattr(scenario, 'failed_tasks', [])
        builder = NotificationPipelineBuilder(trigger='on_complete')
        pipeline = builder.build(scenario, teflo_options={})
        assert getattr(pipeline, 'name') == 'notify'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert len(getattr(pipeline, 'tasks')) == 1
        assert getattr(pipeline, 'type') is NotificationTask

    @staticmethod
    def test_build_on_complete_on_success_multi_notify_task_pipeline(scenario):
        setattr(scenario, 'overall_status', 0)
        setattr(scenario, 'passed_tasks', ['validate', 'provision'])
        setattr(scenario, 'failed_tasks', [])
        builder = NotificationPipelineBuilder(trigger='on_complete')
        pipeline = builder.build(scenario, teflo_options={})
        assert getattr(pipeline, 'name') == 'notify'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert len(getattr(pipeline, 'tasks')) == 2
        assert getattr(pipeline, 'type') is NotificationTask

    @staticmethod
    def test_build_on_complete_on_failure_notify_task_pipeline(scenario):
        setattr(scenario, 'overall_status', 0)
        setattr(scenario, 'passed_tasks', [])
        setattr(scenario, 'failed_tasks', ['report'])
        builder = NotificationPipelineBuilder(trigger='on_complete')
        pipeline = builder.build(scenario, teflo_options={})
        assert getattr(pipeline, 'name') == 'notify'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert len(getattr(pipeline, 'tasks')) == 1
        assert getattr(pipeline, 'type') is NotificationTask

    @staticmethod
    def test_build_on_complete_on_failure_multi_notify_task_pipeline(scenario):
        setattr(scenario, 'overall_status', 0)
        setattr(scenario, 'passed_tasks', [])
        setattr(scenario, 'failed_tasks', ['validate', 'report'])
        builder = NotificationPipelineBuilder(trigger='on_complete')
        pipeline = builder.build(scenario, teflo_options={})
        assert getattr(pipeline, 'name') == 'notify'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert len(getattr(pipeline, 'tasks')) == 2
        assert getattr(pipeline, 'type') is NotificationTask

    @staticmethod
    def test_build_on_demand_notify_task_pipeline(scenario):
        setattr(scenario, 'overall_status', 0)
        setattr(scenario, 'passed_tasks', ['validate'])
        setattr(scenario, 'failed_tasks', [])
        builder = NotificationPipelineBuilder(trigger='on_demand')
        pipeline = builder.build(scenario, teflo_options={})
        assert getattr(pipeline, 'name') == 'notify'
        assert isinstance(getattr(pipeline, 'tasks'), list)
        assert len(getattr(pipeline, 'tasks')) == 1
        assert getattr(pipeline, 'type') is NotificationTask
