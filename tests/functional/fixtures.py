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
    tests.fixtures

    Module containing commonly used pytest fixtures.

    How to add a new common fixture for use by all pytests?
        1. Add your fixture to this module
        2. Import the fixture in the conftest module
        3. Inside your test module, you will be able to access the fixture
        (no need to import fixture - conftest handles everything)

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import copy
import os
from teflo.helpers import validate_render_scenario
import mock
import pytest
from teflo.resources import Action, Execute, Asset, Report, Scenario, Notification
from teflo.utils.config import Config
from teflo._compat import ConfigParser
from teflo.core import TefloProvider, ImporterPlugin

os.environ['TEFLO_SETTINGS'] = '../assets/teflo.cfg'


@pytest.fixture
def config():
    config_file = '../assets/teflo.cfg'
    cfgp = ConfigParser()
    cfgp.read(config_file)
    if cfgp.get('feature_toggles:host', 'plugin_implementation') != 'False':
        cfgp.set('feature_toggles:host', 'plugin_implementation', 'False')
        with open(config_file, 'w') as cf:
            cfgp.write(cf)
    if cfgp.get('task_concurrency', 'provision') != 'False':
        cfgp.set('task_concurrency', 'provision', 'False')
        with open(config_file, 'w') as cf:
            cfgp.write(cf)
    if cfgp.get('task_concurrency', 'report') != 'False':
        cfgp.set('task_concurrency', 'report', 'False')
        with open(config_file, 'w') as cf:
            cfgp.write(cf)
    config = Config()
    config.load()
    return config


@pytest.fixture
def default_host_params():
    return dict(
        groups='client',
        provider=dict(
            name='openstack',
            credential='openstack',
            image='image',
            flavor='small',
            networks=['network']
        )
    )


@pytest.fixture
def timeout_param_provision():
    return dict(
        groups='client',
        provider=dict(
            name='openstack',
            credential='openstack',
            image='image',
            flavor='small',
            networks=['network']),
        provision_timeout=20
    )


@pytest.fixture
def timeout_param_execute():
    return dict(description='description', hosts='test', executor='runner', labels='label2', execute_timeout=20)


@pytest.fixture
def timeout_param_report():
    return dict(
                  description='description',
                  executes='execute',
                  provider=dict(name='polarion',
                                credential='polarion'
                                ),
                                report_timeout=20
                  )


@pytest.fixture
def timeout_param_orchestrate(config):
    return dict(
        description='description',
        hosts=['host_3'],
        orchestrator='ansible',
        labels='label3',
        orchestrate_timeout=20
    )


@pytest.fixture
def default_note_params():
    params = dict(
        description='description goes here.',
        notifier='email-notifier',
        to=['jimmy@who.com'],
        credential='email'
    )
    params.setdefault('from', 'tommy@who.com')

    return params


@pytest.fixture
def notification_on_start_resource(default_note_params, config):
    params = copy.deepcopy(default_note_params)
    params['on_start'] = True
    return Notification(name='note01', parameters=params, config=config)


@pytest.fixture
def notification_default_resource(default_note_params, config):
    params = copy.deepcopy(default_note_params)
    params['on_tasks'] = ['validate']
    return Notification(name='note02', parameters=params, config=config)


@pytest.fixture
def notification_on_success_resource(default_note_params, config):
    params = copy.deepcopy(default_note_params)
    params['on_tasks'] = ['provision']
    params['on_success'] = True
    return Notification(name='note03', parameters=params, config=config)


@pytest.fixture
def notification_on_failure_resource(default_note_params, config):
    params = copy.deepcopy(default_note_params)
    params['on_tasks'] = ['report']
    params['on_failure'] = True
    return Notification(name='note04', parameters=params, config=config)


@pytest.fixture
def notification_on_demand_resource(default_note_params, config):
    params = copy.deepcopy(default_note_params)
    params['on_demand'] = True
    return Notification(name='note05', parameters=params, config=config)

# TODO: Scenario Graph related
# All scenario graph should be automatically generated
# the sdf files should be generated by automation
@pytest.fixture
def basic_scenario_graph_with_provision_only(config):
    config['WORKSPACE'] = '../assets/scenario_graph_basic_test/'
    scenario_graph = validate_render_scenario('../assets/scenario_graph_basic_test/sdf0.yml', config)
    return scenario_graph


@pytest.fixture
def scenario_resource():
    return Scenario(config=Config(), parameters={'k': 'v'})


@pytest.fixture
def scenario_resource1(config):
    return Scenario(config=config, parameters={'k': 'v'})


@pytest.fixture
def action_resource(config):
    return Action(
        name='action',
        config=config,
        parameters=dict(
            description='description',
            hosts=['host01'],
            orchestrator='ansible'
        )
    )


@pytest.fixture
def action_resource_cleanup(config):
    return Action(
        name='action',
        config=config,
        parameters=dict(
            description='description',
            hosts=['host01'],
            orchestrator='ansible',
            cleanup=dict(
                name='cleanup_action',
                description='description',
                hosts=['host01'],
                orchestrator='ansible'
            )
        )
    )


@pytest.fixture
def host(default_host_params, config):
    return Asset(
        name='host01',
        config=config,
        parameters=copy.deepcopy(default_host_params)
    )


@pytest.fixture
def asset1(default_host_params, config):
    return Asset(
        name='host_0',
        config=config,
        parameters=copy.deepcopy(default_host_params)
    )


@pytest.fixture
def asset2(default_host_params, config):
    param = copy.deepcopy(default_host_params)
    param.update(groups='test')
    param.update(labels='label2')
    return Asset(
        name='host_1',
        config=config,
        parameters=param
    )


@pytest.fixture
def asset3(default_host_params, config):
    param = copy.deepcopy(default_host_params)
    param.pop('groups')
    param.update(groups='group_test')
    param.update(labels='label3')
    return Asset(
        name='host_3',
        config=config,
        parameters=param
    )


@pytest.fixture
def action1(config):
    return Action(
        name='action',
        config=config,
        parameters=dict(
            description='description',
            hosts=['client'],
            orchestrator='ansible',
            labels='label2'
        )
    )


@pytest.fixture
def action2(config):
    return Action(
        name='action',
        config=config,
        parameters=dict(
            description='description',
            hosts=['host_3'],
            orchestrator='ansible',
            labels='label3'
        )
    )


@pytest.fixture
def execute1(config):
    params = dict(description='description', hosts='test', executor='runner', labels='label2')
    return Execute(name='execute1', config=config, parameters=params)


@pytest.fixture
def execute2(config):
    params = dict(description='description', hosts='group_test', executor='runner', labels='label3')
    return Execute(name='execute2', config=config, parameters=params)


@pytest.fixture
def scenario1(asset1, action1, scenario_resource1, execute1):
    scenario_resource1.add_assets(asset1)
    scenario_resource1.add_actions(action1)
    scenario_resource1.add_executes(execute1)
    return scenario_resource1


@pytest.fixture
def execute_resource(config):
    params = dict(description='description', hosts='host01', executor='runner')
    return Execute(name='execute', config=config, parameters=params)


@pytest.fixture
@mock.patch('teflo.resources.reports.get_importers_plugin_list')
@mock.patch('teflo.resources.reports.get_importer_plugin_class')
def report_resource(mock_plugin_class, mock_plugin_list, config):
    mock_plugin_list.return_value = ['polarion']
    mock_plugin_class.return_value = ImporterPlugin
    params = dict(description='description', executes='execute',
                  provider=dict(name='polarion',
                                credential='polarion'
                                ),
                  do_import=False)
    report = Report(name='text.xml', parameters=params, config=config)
    # setting this to false since no actual importer is present
    report.do_import = False
    return report


@pytest.fixture
def scenario(action_resource, host, execute_resource, report_resource,
             scenario_resource, notification_on_start_resource, notification_default_resource,
             notification_on_demand_resource, notification_on_failure_resource, notification_on_success_resource):
    scenario_resource.add_assets(host)
    scenario_resource.add_actions(action_resource)
    scenario_resource.add_executes(execute_resource)
    scenario_resource.add_reports(report_resource)
    scenario_resource.add_notifications(notification_on_start_resource)
    scenario_resource.add_notifications(notification_default_resource)
    scenario_resource.add_notifications(notification_on_demand_resource)
    scenario_resource.add_notifications(notification_on_success_resource)
    scenario_resource.add_notifications(notification_on_failure_resource)
    return scenario_resource


@pytest.fixture
def master_child_scenario(action_resource, host, execute_resource, report_resource,
                          scenario_resource, default_host_params, config):
    child_scenario = Scenario(config=Config(), parameters={'k': 'v'})
    host2 = Asset(
        name='host02',
        config=config,
        parameters=copy.deepcopy(default_host_params)
    )
    execute_res2 = Execute(name='execute02', config=config,
                           parameters=dict(description='description', hosts='host02', executor='runner'))
    child_scenario.add_assets(host2)
    child_scenario.add_executes(execute_res2)
    scenario_resource.add_child_scenario(child_scenario)
    scenario_resource.add_assets(host)
    scenario_resource.add_actions(action_resource)
    scenario_resource.add_executes(execute_resource)
    scenario_resource.add_reports(report_resource)
    return scenario_resource


@pytest.fixture
def scenario_labels(asset2, asset3, action1, action2, scenario_resource1, execute1, execute2):
    scenario_resource1.add_assets(asset2)
    scenario_resource1.add_assets(asset3)
    scenario_resource1.add_actions(action1)
    scenario_resource1.add_actions(action2)
    scenario_resource1.add_executes(execute1)
    scenario_resource1.add_executes(execute2)
    return scenario_resource1
