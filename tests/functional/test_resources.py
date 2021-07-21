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
    tests.test_resources

    Unit tests for testing teflo resources classes.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import copy
import os
import uuid

import mock
import pytest

from teflo._compat import ConfigParser, string_types
from teflo.exceptions import TefloActionError, TefloExecuteError, \
    ScenarioError, TefloError, TefloReportError, TefloResourceError
from teflo.executors.ext.ansible_executor_plugin import AnsibleExecutorPlugin
from teflo.orchestrators.ext.ansible_orchestrator_plugin import AnsibleOrchestratorPlugin
from teflo.providers import OpenstackProvider
from teflo.provisioners.ext import OpenstackLibCloudProvisionerPlugin
from teflo.resources import Action, Execute, Asset, Report, Scenario, Notification
from teflo.utils.config import Config
from teflo.core import ImporterPlugin, TefloProvider
from teflo.notifiers.ext import EmailNotificationPlugin


@pytest.fixture(scope='class')
def feature_toggle_config():
    config_file = '../assets/teflo.cfg'
    cfgp = ConfigParser()
    cfgp.read(config_file)
    cfgp.set('feature_toggles:host','plugin_implementation','True')
    with open(config_file, 'w') as cf:
        cfgp.write(cf)
    os.environ['TEFLO_SETTINGS'] = config_file
    config = Config()
    config.load()
    return config


@pytest.fixture
def default_report_params():
    params = dict(
        description='description',
        executes='execute',
        provider=dict(name='polarion',
                      credential='polarion'
                      )
    )
    return params


@pytest.fixture
def report_params_np():
    params = dict(
        description='description',
        executes='execute',
        importer='polarion',
        credential='polarion'
    )
    return params


@pytest.fixture
def host2(default_host_params, config):
    host2 = Asset(name='host_count', config=config, parameters=copy.deepcopy(default_host_params))
    return host2


@pytest.fixture
def host3(default_host_params, config):
    host3 = Asset(name='host_number_3', config=config, parameters=copy.deepcopy(default_host_params))
    return host3


@pytest.fixture
@mock.patch('teflo.resources.reports.get_importers_plugin_list')
@mock.patch('teflo.resources.reports.get_importer_plugin_class')
def report1(mock_plugin_class, mock_plugin_list, default_report_params, config):
    mock_plugin_list.return_value = ['polarion']
    mock_plugin_class.return_value = ImporterPlugin
    return Report(name='SampleTest.xml', parameters=copy.deepcopy(default_report_params), config=config)


@pytest.fixture
@mock.patch('teflo.resources.reports.get_importers_plugin_list')
@mock.patch('teflo.resources.reports.get_importer_plugin_class')
def report2(mock_plugin_class, mock_plugin_list, default_report_params, config):
    mock_plugin_list.return_value = ['polarion']
    mock_plugin_class.return_value = ImporterPlugin
    return Report(name='SampleTest2.xml', parameters=copy.deepcopy(default_report_params), config=config)


@pytest.fixture
@mock.patch('teflo.resources.reports.get_importers_plugin_list')
@mock.patch('teflo.resources.reports.get_importer_plugin_class')
def report3(mock_plugin_class, mock_plugin_list, default_report_params, config):
    mock_plugin_list.return_value = ['polarion']
    mock_plugin_class.return_value = ImporterPlugin
    return Report(name='SampleTest3.xml', parameters=copy.deepcopy(default_report_params), config=config)


@pytest.fixture
def scenario_res1(config, host2, host, report1):
    scenario1 = Scenario(config=config, parameters={'k': 'v'})
    scenario1.add_assets(host2)
    scenario1.add_assets(host)
    scenario1.add_reports(report1)
    return scenario1


@pytest.fixture
def scenario_res2(config, host2, host, report1):
    scenario1 = Scenario(config=config, parameters={'k': 'v'})
    scenario1.add_assets(host2)
    scenario1.add_assets(host)
    scenario1.add_reports(report1)
    return scenario1


@pytest.fixture
def scenario_res3(config, host2, host, host3, report1, report2, report3):
    scenario1 = Scenario(config=config, parameters={'k': 'v'})
    scenario1.add_assets(host3)
    scenario1.add_assets(host2)
    scenario1.add_assets(host)
    scenario1.add_reports(report1)
    scenario1.add_reports(report2)
    scenario1.add_reports(report3)
    return scenario1


@pytest.fixture
def task_list_host(host2, host):

    param1 = copy.deepcopy(host2.profile())
    param1.update(name='host_count_0')
    param2 = copy.deepcopy(host2.profile())
    param2.update(name='host_count_1')

    task_result_list = [
        {'status': 0,
         'task': 'teflotaskobj1',
         'methods': [{'status': 0, 'rvalue': [param1, param2], 'name':'run'}],
         'bid': 123,
         'asset': host2,
         'msg': 'hostcreation1'
         },
        {'status': 0,
         'task': 'teflotaskobj2',
         'methods': [{'status': 0, 'rvalue': None, 'name':'run'}],
         'bid': 456,
         'asset': host,
         'msg': 'hostcreation2'
         }
    ]

    return task_result_list


@pytest.fixture
def task_list_host_1(host2):

    param1 = copy.deepcopy(host2.profile())
    param1.update(name='host_count_0')
    param2 = copy.deepcopy(host2.profile())
    param2.update(name='host_count_1')

    task_result_list = [
        {'status': 0,
         'task': 'teflotaskobj1',
         'methods': [{'status': 0, 'rvalue': [param1, param2], 'name':'run'}],
         'bid': 123,
         'asset': host2,
         'msg': 'hostcreation1'
         }

    ]

    return task_result_list

@pytest.fixture
def task_list_host_with_3(host2, host, host3):

    param1 = copy.deepcopy(host2.profile())
    param1.update(name='host_count_0')
    param2 = copy.deepcopy(host2.profile())
    param2.update(name='host_count_1')

    task_result_list = [
        {'status': 0,
         'task': 'teflotaskobj3',
         'methods': [{'status': 0, 'rvalue': None, 'name':'run'}],
         'bid': 789,
         'asset': host3,
         'msg': 'hostcreation3'
         },
        {'status': 0,
         'task': 'teflotaskobj1',
         'methods': [{'status': 0, 'rvalue': [param1, param2], 'name':'run'}],
         'bid': 123,
         'asset': host2,
         'msg': 'hostcreation1'
         },
        {'status': 0,
         'task': 'teflotaskobj2',
         'methods': [{'status': 0, 'rvalue': None, 'name':'run'}],
         'bid': 456,
         'asset': host,
         'msg': 'hostcreation2'
         }

    ]

    return task_result_list


@pytest.fixture
def task_list_host_with_3_no_count(host2, host, host3):

    task_result_list = [
        {'status': 0,
         'task': 'teflotaskobj3',
         'methods': [{'status': 0, 'rvalue': None, 'name':'run'}],
         'bid': 789,
         'asset': host3,
         'msg': 'hostcreation3'
         },
        {'status': 0,
         'task': 'teflotaskobj1',
         'methods': [{'status': 0, 'rvalue': None, 'name':'run'}],
         'bid': 123,
         'asset': host2,
         'msg': 'hostcreation1'
         },
        {'status': 0,
         'task': 'teflotaskobj2',
         'methods': [{'status': 0, 'rvalue': None, 'name':'run'}],
         'bid': 456,
         'asset': host,
         'msg': 'hostcreation2'
         }

    ]

    return task_result_list


@pytest.fixture
def task_list_report(report1):

    task_result_list = [
        {'status': 0,
         'task': 'ReportTask',
         'methods': [{'status': 0, 'rvalue': None, 'name': 'run'}],
         'package': report1,
         'bid': 234,
         'msg': 'reporting SampleTest.xml', 'name': 'SampleTest.xml'
         }
    ]
    return task_result_list


@pytest.fixture
def task_list_report_2(report1, report2, report3):

    task_result_list = [
        {'status': 0,
         'task': 'ReportTask',
         'methods': [{'status': 0, 'rvalue': None, 'name': 'run'}],
         'package': report1,
         'bid': 234,
         'msg': 'reporting SampleTest.xml', 'name': 'SampleTest.xml'
         },
        {'status': 0,
         'task': 'ReportTask',
         'methods': [{'status': 0, 'rvalue': None, 'name': 'run'}],
         'package': report2,
         'bid': 101,
         'msg': 'reporting SampleTest2.xml', 'name': 'SampleTest2.xml'
         },
        {'status': 0,
         'task': 'ReportTask',
         'methods': [{'status': 0, 'rvalue': None, 'name': 'run'}],
         'package': report3,
         'bid': 222,
         'msg': 'reporting SampleTest3.xml', 'name': 'SampleTest3.xml'
         }
    ]
    return task_result_list

class TestActionResource(object):
    @staticmethod
    def test_create_action_with_name():
        params = dict(
            description='description goes here.',
            hosts=['host01']
        )
        action = Action(name='action', parameters=params)
        assert isinstance(action, Action)

    @staticmethod
    def test_timeout_from_scenario(timeout_param_orchestrate):
        action = Action(name='action', parameters=timeout_param_orchestrate)
        assert action._orchestrate_timeout is 20

    @staticmethod
    def test_timeout_from_cfg(config):
        params = dict(
            description='description goes here.',
            hosts=['host01']
        )
        action = Action(name='action', parameters=params, config=config)
        assert action._orchestrate_timeout is 25

    @staticmethod
    def test_create_action_without_name():
        params = dict(
            description='description goes here.',
            hosts=['host01']
        )

        with pytest.raises(TefloActionError):
            Action(parameters=params)

    @staticmethod
    def test_create_action_with_name_in_parameters():
        params = dict(
            name='action',
            description='description goes here.',
            hosts=['host01']
        )

        action = Action(parameters=params)
        assert action.name == 'action'

    @staticmethod
    def test_create_action_without_hosts():
        params = dict(
            name='action',
            description='description goes here.',
            hosts=None
        )
        with pytest.raises(TefloActionError) as ex:
            Action(parameters=params)
        assert 'Unable to associate hosts to action: action.No hosts ' \
               'defined!' in ex.value.args[0]

    @staticmethod
    def test_create_action_with_hosts_as_str():
        params = dict(
            description='description goes here.',
            hosts='host01, host02',
            key='value'
        )
        action = Action(name='action', parameters=params)
        assert isinstance(action.hosts, list)

    @staticmethod
    def test_create_action_with_invalid_orchestrator():
        params = dict(
            description='description goes here.',
            hosts=['host01'],
            orchestrator='abc'
        )
        with pytest.raises(TefloActionError) as ex:
            Action(name='action', parameters=params)
        assert 'Orchestrator: abc is not supported!' in ex.value.args

    @staticmethod
    def test_orchestrator_property(action_resource):
        assert action_resource.orchestrator == AnsibleOrchestratorPlugin

    @staticmethod
    def test_orchestrator_setter(action_resource):
        with pytest.raises(AttributeError) as ex:
            action_resource.orchestrator = 'null'
        assert 'Orchestrator class property cannot be set.' in ex.value.args

    @staticmethod
    def test_build_profile_case_01(action_resource):
        assert isinstance(action_resource.profile(), dict)

    @staticmethod
    def test_build_profile_case_02(action_resource):
        host = mock.MagicMock()
        host.name = 'host01'
        action_resource.hosts = [host]
        assert isinstance(action_resource.profile(), dict)

    @staticmethod
    def test_create_action_with_cleanup_action(action_resource_cleanup):
        assert hasattr(action_resource_cleanup, 'cleanup')


class TestReportResource(object):
    @staticmethod
    def test_constructor(report_resource):
        assert isinstance(report_resource, Report)

    @staticmethod
    def test_build_profile(report_resource):
        assert isinstance(report_resource.profile(), dict)

    @staticmethod
    @mock.patch('teflo.resources.reports.get_importers_plugin_list')
    @mock.patch('teflo.resources.reports.get_importer_plugin_class')
    def test_timeout_from_scenario(mock_plugin_class, mock_plugin_list, timeout_param_report, config):
        mock_plugin_list.return_value = ['polarion']
        mock_plugin_class.return_value = ImporterPlugin
        params = copy.deepcopy(timeout_param_report)
        report = Report(name='report', parameters=params, config=config)
        assert report._report_timeout is 20

    @staticmethod
    @mock.patch('teflo.resources.reports.get_importers_plugin_list')
    @mock.patch('teflo.resources.reports.get_importer_plugin_class')
    def test_timeout_from_cfg(mock_plugin_class, mock_plugin_list, config, report_params_np):
        mock_plugin_list.return_value = ['polarion']
        mock_plugin_class.return_value = ImporterPlugin
        report = Report(name='test.xml', parameters=report_params_np, config=config)
        assert report._report_timeout is 25

    @staticmethod
    def test_create_report_with_name(report1):
        assert isinstance(report1, Report)

    @staticmethod
    def test_create_report_without_name():
        with pytest.raises(TefloReportError) as ex:
            Report()
        assert 'Unable to build report object. Name field missing!' in \
               ex.value.args[0]


    @staticmethod
    def test_create_report_without_executes(default_report_params, config):
        params = copy.deepcopy(default_report_params)
        del params['executes']
        report = Report(name='test.xml', parameters=params, config=config)
        assert isinstance(report.executes, list)

    @staticmethod
    @mock.patch('teflo.resources.reports.get_importers_plugin_list')
    @mock.patch('teflo.resources.reports.get_importer_plugin_class')
    def test_create_report_without_executes(mock_plugin_class, mock_plugin_list, default_report_params, config):
        params = copy.deepcopy(default_report_params)
        del params['executes']
        mock_plugin_list.return_value = ['polarion']
        mock_plugin_class.return_value = ImporterPlugin
        report = Report(name='test.xml', parameters=params, config=config)
        assert isinstance(report.executes, list)

    @staticmethod
    @mock.patch('teflo.resources.reports.get_importers_plugin_list')
    @mock.patch('teflo.resources.reports.get_importer_plugin_class')
    def test_create_report_with_executes_as_str(mock_plugin_class, mock_plugin_list, default_report_params, config):
        default_report_params['executes'] = 'execute01, execute02'
        mock_plugin_list.return_value = ['polarion']
        mock_plugin_class.return_value = ImporterPlugin
        report = Report(name='test.xml', parameters=default_report_params, config=config)
        assert isinstance(report.executes, list)

    @staticmethod
    @mock.patch('teflo.resources.reports.get_importers_plugin_list')
    @mock.patch('teflo.resources.reports.get_importer_plugin_class')
    def test_create_report_with_executes_as_str_1(mock_plugin_class, mock_plugin_list, default_report_params, config):
        default_report_params['executes'] = 'execute 01,execute 02, execute03'
        mock_plugin_list.return_value = ['polarion']
        mock_plugin_class.return_value = ImporterPlugin
        report = Report(name='test.xml', parameters=default_report_params, config=config)
        assert isinstance(report.executes, list)
        assert len(report.executes) == 3

    @staticmethod
    def test_build_report_profile_case_01(report_resource):
        assert isinstance(report_resource.profile(), dict)

    @staticmethod
    def test_build_report_profile_case_02(report_resource):
        execute = mock.MagicMock()
        execute.name = 'execute02'
        report_resource.executes = [execute]
        assert isinstance(report_resource.profile(), dict)

    @staticmethod
    @mock.patch('teflo.resources.reports.get_importers_plugin_list')
    @mock.patch('teflo.resources.reports.get_importer_plugin_class')
    def test_create_report_without_provider_key(mock_plugin_class, mock_plugin_list, report_params_np, config):
        """The test is to verify that when report params are passed correctly  without the provider dictionary"""
        mock_plugin_list.return_value = ['polarion']
        mock_plugin_class.return_value = ImporterPlugin
        report = Report(name='test.xml', parameters=report_params_np, config=config)
        assert report.credential['name'] == 'polarion'


class TestExecuteResource(object):
    @staticmethod
    def test_create_execute_with_name():
        params = dict(hosts=['host01'], key='value')
        execute = Execute(name='execute', parameters=params)
        assert isinstance(execute, Execute)

    @staticmethod
    def test_create_execute_without_name():
        with pytest.raises(TefloExecuteError) as ex:
            Execute()
        assert 'Unable to build execute object. Name field missing!' in \
               ex.value.args[0]
    @staticmethod
    def test_timeout_from_scenario(timeout_param_execute):
        execute = Execute(name='action', parameters=timeout_param_execute)
        assert execute._execute_timeout is 20

    @staticmethod
    def test_timeout_from_cfg(config, default_host_params):
        params = dict(hosts=['host01'], key='value')
        execute = Execute(name='action', parameters=params, config=config)
        assert execute._execute_timeout is 25

    @staticmethod
    def test_create_execute_with_invalid_executor():
        params = dict(hosts=['host01'], key='value', executor='abc')
        with pytest.raises(TefloExecuteError) as ex:
            Execute(name='execute', parameters=params)
        assert 'Executor: abc is not supported!' in ex.value.args[0]

    @staticmethod
    def test_create_execute_without_hosts():
        params = dict(hosts=None, key='value', executor='runner')
        with pytest.raises(TefloExecuteError) as ex:
            Execute(name='execute', parameters=params)
        assert 'Unable to associate hosts to executor:execute. No hosts ' \
               'defined!' in ex.value.args[0]

    @staticmethod
    def test_create_execute_with_hosts_as_str():
        params = dict(description='description', hosts='host01, host02')
        execute = Execute(name='execute', parameters=params)
        assert isinstance(execute.hosts, list)

    @staticmethod
    def test_create_execute_with_artifacts_as_str():
        params = dict(description='description', hosts='host01, host02',
                      artifacts='test.log, console.log')
        execute = Execute(name='execute', parameters=params)
        assert isinstance(execute.artifacts, list)

    @staticmethod
    def test_executor_property(execute_resource):
        assert execute_resource.executor == AnsibleExecutorPlugin


    @staticmethod
    def test_executor_setter(execute_resource):
        with pytest.raises(AttributeError) as ex:
            execute_resource.executor = 'null'
        assert 'Executor class property cannot be set.' in ex.value.args

    @staticmethod
    def test_build_profile_case_01(execute_resource):
        assert isinstance(execute_resource.profile(), dict)

    @staticmethod
    def test_build_profile_case_02(execute_resource):
        host = mock.MagicMock()
        host.name = 'host01'
        execute_resource.hosts = [host]
        assert isinstance(execute_resource.profile(), dict)


class TestScenarioResource(object):
    @staticmethod
    def test_create_scenario_01():
        scenario = Scenario(config=Config(), parameters={'k': 'v'})
        assert isinstance(scenario, Scenario)

    @staticmethod
    def test_create_scenario_02():
        config = Config()
        config['DATA_FOLDER'] = '/tmp/%s' % uuid.uuid4()
        scenario = Scenario(config=config, parameters={'k': 'v'})
        assert os.path.exists(scenario.data_folder)
        os.removedirs(scenario.data_folder)

    # TODO commented the following test, as it is failing on github action env. Need to investigate this and uncomment
    # @staticmethod
    # def test_create_scenario_03():
    #     config = Config()
    #     config['DATA_FOLDER'] = '/root/%s' % uuid.uuid4()
    #     with pytest.raises(ScenarioError):
    #         Scenario(config=config, parameters={'k': 'v'})


    @staticmethod
    @mock.patch.object(os, 'makedirs')
    @pytest.mark.filterwarnings('ignore::DeprecationWarning')
    def test_create_scenario_04(mock_method):
        config = Config()
        config['DATA_FOLDER'] = '/tmp/%s' % uuid.uuid4()
        with pytest.raises(ScenarioError):
            mock_method.side_effect = OSError()
            mock_method.side_effect.errno = 0
            Scenario(config=config, parameters={'k': 'v'})

    @staticmethod
    def test_yaml_data_property(scenario_resource):
        assert isinstance(scenario_resource.yaml_data, dict)

    @staticmethod
    def test_yaml_data_setter(scenario_resource):
        scenario_resource.yaml_data = {'name': 'scenario'}

    @staticmethod
    def test_add_host_resource(scenario_resource, host):
        scenario_resource.add_resource(host)

    @staticmethod
    def test_add_action_resource(scenario_resource, action_resource):
        scenario_resource.add_resource(action_resource)

    @staticmethod
    def test_add_execute_resource(scenario_resource, execute_resource):
        scenario_resource.add_resource(execute_resource)

    @staticmethod
    def test_add_report_resource(scenario_resource, report_resource):
        scenario_resource.add_resource(report_resource)

    @staticmethod
    def test_add_invalid_resource(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.add_resource(mock.MagicMock())

    @staticmethod
    def test_initialize_host_resource(scenario_resource, host):
        scenario_resource.initialize_resource(host)
        assert scenario_resource.assets.__len__() == 0

    @staticmethod
    def test_initialize_action_resource(scenario_resource, action_resource):
        scenario_resource.initialize_resource(action_resource)
        assert scenario_resource.actions.__len__() == 0

    @staticmethod
    def test_initialize_execute_resource(scenario_resource, execute_resource):
        scenario_resource.initialize_resource(execute_resource)
        assert scenario_resource.executes.__len__() == 0

    @staticmethod
    def test_initialize_report_resource(scenario_resource, report_resource):
        scenario_resource.initialize_resource(report_resource)
        assert scenario_resource.reports.__len__() == 0

    @staticmethod
    def test_initialize_invalid_resource(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.initialize_resource(mock.MagicMock())

    @staticmethod
    def test_hosts_property(scenario_resource):
        assert isinstance(scenario_resource.assets, list)

    @staticmethod
    def test_hosts_setter(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.assets = ['host']

    @staticmethod
    def test_add_invalid_hosts(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.add_assets(mock.MagicMock())

    @staticmethod
    def test_actions_property(scenario_resource):
        assert isinstance(scenario_resource.actions, list)

    @staticmethod
    def test_actions_setter(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.actions = ['action']

    @staticmethod
    def test_add_invalid_action(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.add_actions(mock.MagicMock())

    @staticmethod
    def test_executes_property(scenario_resource):
        assert isinstance(scenario_resource.executes, list)

    @staticmethod
    def test_executes_setter(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.executes = ['execute']

    @staticmethod
    def test_add_invalid_execute(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.add_executes(mock.MagicMock())

    @staticmethod
    def test_reports_property(scenario_resource):
        assert isinstance(scenario_resource.reports, list)

    @staticmethod
    def test_reports_setter(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.reports = ['report']

    @staticmethod
    def test_add_invalid_report(scenario_resource):
        with pytest.raises(ValueError):
            scenario_resource.add_reports(mock.MagicMock())

    @staticmethod
    def test_profile_uc01(scenario):
        profile = scenario.profile()
        assert isinstance(profile, dict)

    @staticmethod
    def test_child_scenario_property(master_child_scenario):
        ch_sc = master_child_scenario.child_scenarios
        assert isinstance(ch_sc, list)
        assert isinstance(ch_sc[0], Scenario)

    @staticmethod
    def test_reload_method_assets_mixed_tasks(task_list_host, scenario_res1):
        scenario_res1.reload_resources(task_list_host)
        assert len(scenario_res1.assets) == 3
        assert scenario_res1.assets[0].name == 'host_count_0'
        assert scenario_res1.assets[1].name == 'host_count_1'
        assert scenario_res1.assets[2].name == 'host01'

    @staticmethod
    def test_reload_method_default(task_list_host_with_3_no_count, scenario_res3):
        scenario_res3.reload_resources(task_list_host_with_3_no_count)
        assert len(scenario_res3.assets) == 3
        assert scenario_res3.assets[0].name == 'host_number_3'
        assert scenario_res3.assets[1].name == 'host_count'
        assert scenario_res3.assets[2].name == 'host01'

    @staticmethod
    def test_reload_method_assets_reversed_mixed_tasks(task_list_host, scenario_res2):
        task_list_host.reverse()
        scenario_res2.reload_resources(task_list_host)
        assert len(scenario_res2.assets) == 3
        assert scenario_res2.assets[0].name == 'host_count_0'
        assert scenario_res2.assets[1].name == 'host_count_1'
        assert scenario_res2.assets[2].name == 'host01'

    @staticmethod
    def test_reload_method_assets_count_from_middle_tasks(task_list_host_with_3, scenario_res3):
        scenario_res3.reload_resources(task_list_host_with_3)
        assert len(scenario_res3.assets) == 4
        assert scenario_res3.assets[0].name == 'host_number_3'
        assert scenario_res3.assets[1].name == 'host_count_0'
        assert scenario_res3.assets[2].name == 'host_count_1'
        assert scenario_res3.assets[3].name == 'host01'

    @staticmethod
    def test_reload_method_assets_count_reversed_from_middle_tasks(task_list_host_with_3, scenario_res3):
        task_list_host_with_3.reverse()
        scenario_res3.reload_resources(task_list_host_with_3)
        assert len(scenario_res3.assets) == 4
        assert scenario_res3.assets[0].name == 'host_number_3'
        assert scenario_res3.assets[1].name == 'host_count_0'
        assert scenario_res3.assets[2].name == 'host_count_1'
        assert scenario_res3.assets[3].name == 'host01'

    @staticmethod
    def test_reload_method_reports_tasks(task_list_report, scenario_res1):
        scenario_res1.reload_resources(task_list_report)
        assert len(scenario_res1.reports) == 1

    @staticmethod
    def test_reload_method_reports_reversed_tasks(task_list_report_2, scenario_res3):
        task_list_report_2.reverse()
        scenario_res3.reload_resources(task_list_report_2)
        assert len(scenario_res3.reports) == 3
        assert scenario_res3.reports[0].name == 'SampleTest.xml'
        assert scenario_res3.reports[1].name == 'SampleTest2.xml'
        assert scenario_res3.reports[2].name == 'SampleTest3.xml'

    @staticmethod
    def test_reload_method_assets_tasks_using_labels(task_list_host_1, scenario_res1):
        """This is to test if assets which are not picked up for a task still get added to the scenario to populate
         the results.yml"""
        scenario_res1.reload_resources(task_list_host_1)
        assert len(scenario_res1.assets) == 3
        assert scenario_res1.assets[0].name == 'host_count_0'
        assert scenario_res1.assets[1].name == 'host_count_1'
        assert scenario_res1.assets[2].name == 'host01'

    @staticmethod
    def test_reload_method_assets_tasks_using_labels_and_asset_count(task_list_host_1, scenario_res3):
        """This is to test if assets which are not picked up for a task still get added to the scenario to populate
         the results.yml"""
        scenario_res3.reload_resources(task_list_host_1)
        assert len(scenario_res3.assets) == 4
        assert scenario_res3.assets[0].name == 'host_number_3'
        assert scenario_res3.assets[1].name == 'host_count_0'
        assert scenario_res3.assets[2].name == 'host_count_1'
        assert scenario_res3.assets[3].name == 'host01'

    @staticmethod
    def test_reload_method_reports_tasks_using_labels(task_list_report_2, scenario_res3):
        """This is to test if assets which are not picked up for a task still get added to the scenario to populate
         the results.yml"""
        scenario_res3.reload_resources(task_list_report_2[1:2])
        assert len(scenario_res3.reports) == 3
        assert scenario_res3.reports[0].name == 'SampleTest.xml'
        assert scenario_res3.reports[1].name == 'SampleTest2.xml'
        assert scenario_res3.reports[2].name == 'SampleTest3.xml'

class TestAssetResource(object):
    @staticmethod
    def __get_params_copy__(params):
        return copy.deepcopy(params)

    @staticmethod
    def test_timeout_from_scenario(timeout_param_provision, config):
        asset = Asset(name='Asset', parameters=timeout_param_provision, config=config)
        assert asset._provision_timeout is 20

    @staticmethod
    def test_timeout_from_cfg(default_host_params, config):
        params = default_host_params
        asset = Asset(name='asset', config=config, parameters=params)
        assert asset._provision_timeout is 25

    def test_create_host_with_name(self, default_host_params, config):
        params = self.__get_params_copy__(default_host_params)
        host = Asset(name='host01', config=config, parameters=params)
        assert isinstance(host, Asset)
        assert host.name == 'host01'

    def test_create_host_without_name(self, default_host_params, config):
        params = self.__get_params_copy__(default_host_params)
        host = Asset(parameters=params, config=config)
        assert 'hst' in host.name

    def test_create_host_undefined_groups(self, default_host_params, config):
        params = self.__get_params_copy__(default_host_params)
        params.pop('groups')
        asset = Asset(name='host01', config=config, parameters=params)
        assert hasattr(asset, 'groups') is False

    def test_create_host_undefined_provider(self, default_host_params, config):
        params = self.__get_params_copy__(default_host_params)
        params.pop('provider')
        with pytest.raises(TefloResourceError):
            host = Asset(name='host01', parameters=params, config=config)

    def test_create_host_invalid_provider(self, default_host_params, config):
        params = self.__get_params_copy__(default_host_params)
        params['provider']['name'] = 'null'
        with pytest.raises(TefloResourceError):
            Asset(name='host01', parameters=params, config=config)

    def test_create_host_invalid_provisioner(
            self, default_host_params, config):
        params = self.__get_params_copy__(default_host_params)
        params['provisioner'] = 'null'
        with pytest.raises(TefloResourceError):
            Asset(name='host01', parameters=params, config=config)

    def test_create_host_with_provisioner_set(
            self, default_host_params, config):
        params = self.__get_params_copy__(default_host_params)
        params['provisioner'] = 'openstack-libcloud'
        host = Asset(name='host01', parameters=params, config=config)
        assert host.provisioner is OpenstackLibCloudProvisionerPlugin

    def test_create_host_undefined_credential(self, default_host_params, config):
        params = self.__get_params_copy__(default_host_params)
        params['provider'].pop('credential')
        host = Asset(name='host01', parameters=params, config=config)
        assert not hasattr(host, 'credential')

    def test_create_host_provider_static(self, default_host_params):
        params = self.__get_params_copy__(default_host_params)
        params.pop('provider')
        params['ip_address'] = '127.0.0.1'
        asset = Asset(name='host01', parameters=params)
        assert asset.is_static

    def test_ip_address_property(self, host):
        assert not hasattr(host, 'ip_address')

    def test_ip_address_setter(self, host):
        host.ip_address = '127.0.0.1'
        assert host.ip_address == '127.0.0.1'

    def test_metadata_property(self, host):
        assert host.metadata == {}

    def test_metadata_setter(self, host):
        with pytest.raises(AttributeError) as ex:
            host.metadata = {'k': 'v'}
        assert 'You cannot set metadata directly. Use function ' \
               '~Asset.set_metadata' in ex.value.args

    def test_set_metadata(self, host):
        with pytest.raises(NotImplementedError):
            host.set_metadata()

    def test_ansible_params_property(self, host):
        assert host.ansible_params == {}

    def test_ansible_params_setter(self, host):
        with pytest.raises(AttributeError) as ex:
            host.ansible_params = {'ansible_user': 'user01'}
        assert 'You cannot set the ansible parameters directly. This is set' \
               ' one time within the YAML input.' in ex.value.args

    def test_provider_property(self, host):
        assert isinstance(host.provider, string_types)

    def test_provider_setter(self, host):
        with pytest.raises(AttributeError) as ex:
            host.provider = 'null'
        assert 'You cannot set the asset provider after asset class is ' \
               'instantiated.' in ex.value.args[0]

    def test_group_property(self, default_host_params, config):
        params = self.__get_params_copy__(default_host_params)
        params.update(dict(groups=['group1']))
        host = Asset(name='host01', parameters=params, config=config)
        assert host.groups[-1] == 'group1'

    def test_group_setter(self, host):
        with pytest.raises(AttributeError) as ex:
            host.groups = 'test'
        assert 'You cannot set the groups after asset class is instantiated.' in \
               ex.value.args[0]

    def test_build_profile_uc01(self, host):
        assert isinstance(host.profile(), dict)

    def test_build_profile_uc02(self, host):
        static_host = copy.copy(host)
        setattr(static_host, 'ip_address', '127.0.0.1')
        assert isinstance(static_host.profile(), dict)

    def test_validate_success(self, host):
        host.validate()

    def test_provisioner_property(self, default_host_params, feature_toggle_config):
        params = self.__get_params_copy__(default_host_params)
        host = Asset(name='host01', parameters=params, config=feature_toggle_config)
        assert host.provisioner is OpenstackLibCloudProvisionerPlugin

    def test_provisioner_setter(self, default_host_params, feature_toggle_config):
        params = self.__get_params_copy__(default_host_params)
        host = Asset(name='host01', parameters=params, config=feature_toggle_config)
        with pytest.raises(AttributeError) as ex:
            host.provisioner = 'null'
        assert 'You cannot set the asset provisioner plugin after asset class ' \
               'is instantiated.' in ex.value.args[0]

    @staticmethod
    def test_same_groups_name_host_name_error(default_host_params, config):
        params = default_host_params
        with pytest.raises(TefloResourceError) as ex:
            asset = Asset(name='client', config=config, parameters=params)
        assert "Asset name client cannot be same as groups name ['client']" in ex.value.args[0]


class TestNotificationResource(object):

    @staticmethod
    def test_create_notification_with_name():
        params = dict(
            description='description goes here.',
            notifier='email-notifier'
        )
        note = Notification(name='note', parameters=params)
        assert isinstance(note, Notification)

    @staticmethod
    def test_create_notification_without_name():
        params = dict(
            description='description goes here.',
            notifier='email-notifier'
        )

        with pytest.raises(TefloResourceError):
            Notification(parameters=params)

    @staticmethod
    def test_create_notification_with_name_in_parameters():
        params = dict(
            name='note',
            description='description goes here.',
            notifier='email-notifier'
        )

        note = Notification(parameters=params)
        assert note.name == 'note'

    @staticmethod
    def test_create_notification_without_notifier():
        params = dict(
            name='note',
            description='description goes here.'
        )
        note = Notification(parameters=params)
        assert note.notifier

    @staticmethod
    def test_create_notification_unregistered_notifier():
        params = dict(
            name='note',
            description='description goes here.',
            notifier='blah'
        )
        with pytest.raises(TefloResourceError) as ex:
            Notification(parameters=params)

    @staticmethod
    def test_notification_set_notifier():
        params = dict(
            name='note',
            description='description goes here.',
        )
        note = Notification(parameters=params)
        with pytest.raises(AttributeError) as ex:
            note.notifier = 'blah'

    @staticmethod
    def test_create_notification_default_triggers():
        params = dict(
            description='description goes here.',
            notifier='email-notifier'
        )
        note = Notification(name='note', parameters=params)
        assert note.on_success
        assert note.on_failure

    @staticmethod
    def test_create_notification_on_success():
        params = dict(
            description='description goes here.',
            notifier='email-notifier',
            on_success=True
        )
        note = Notification(name='note', parameters=params)
        assert note.on_success

    @staticmethod
    def test_notification_set_on_success():
        params = dict(
            description='description goes here.',
            notifier='email-notifier',
            on_success=True
        )
        note = Notification(name='note', parameters=params)
        with pytest.raises(AttributeError):
            note.on_success = False

    @staticmethod
    def test_create_notification_on_failure():
        params = dict(
            description='description goes here.',
            notifier='email-notifier',
            on_failure=True
        )
        note = Notification(name='note', parameters=params)
        assert note.on_failure

    @staticmethod
    def test_notification_set_on_failure():
        params = dict(
            description='description goes here.',
            notifier='email-notifier',
            on_failure=True
        )
        note = Notification(name='note', parameters=params)
        with pytest.raises(AttributeError):
            note.on_failure = False

    @staticmethod
    def test_create_notification_on_success_and_failure():
        params = dict(
            description='description goes here.',
            notifier='email-notifier',
            on_success=True,
            on_failure=False
        )
        note = Notification(name='note', parameters=params)
        assert note.on_success
        assert not note.on_failure

    @staticmethod
    def test_create_notification_on_tasks():
        tasks = ['validate', 'provision']
        params = dict(
            description='description goes here.',
            notifier='email-notifier',
            on_tasks=tasks
        )
        note = Notification(name='note', parameters=params)
        assert note.on_tasks
        assert set(note.on_tasks).intersection(tasks)

    @staticmethod
    def test_notification_set_on_tasks():
        tasks = ['validate', 'provision']
        params = dict(
            description='description goes here.',
            notifier='email-notifier',
            on_tasks=tasks
        )
        note = Notification(name='note', parameters=params)
        with pytest.raises(AttributeError):
            note.on_tasks = tasks

    @staticmethod
    def test_create_notification_on_start():
        params = dict(
            description='description goes here.',
            notifier='email-notifier',
            on_start=True
        )
        note = Notification(name='note', parameters=params)
        assert note.on_start
        assert getattr(note, 'on_success') is None

    @staticmethod
    def test_notification_set_on_start():
        params = dict(
            description='description goes here.',
            notifier='email-notifier',
            on_start=True
        )
        note = Notification(name='note', parameters=params)
        with pytest.raises(AttributeError):
            note.on_start = False

    @staticmethod
    def test_create_notification_on_demand():
        params = dict(
            description='description goes here.',
            notifier='email-notifier',
            on_demand=True
        )
        note = Notification(name='note', parameters=params)
        assert note.on_demand
        assert getattr(note, 'on_start') is None

    @staticmethod
    def test_notification_set_on_demand():
        params = dict(
            description='description goes here.',
            notifier='email-notifier',
            on_demand=True
        )
        note = Notification(name='note', parameters=params)
        with pytest.raises(AttributeError):
            note.on_demand = False

    @staticmethod
    def test_notification_no_credential():
        params = dict(
            description='description goes here.',
            notifier='email-notifier'
        )
        note = Notification(name='note', parameters=params)
        assert not note.credential

    @staticmethod
    def test_notification_credential(config):
        params = dict(
            description='description goes here.',
            notifier='email-notifier'
        )
        note = Notification(name='note', parameters=params, config=config)
        assert note.credential is None

    @staticmethod
    def test_notification_set_credential():
        params = dict(
            description='description goes here.',
            notifier='email-notifier'
        )
        note = Notification(name='note', parameters=params)
        with pytest.raises(AttributeError):
            note.credential = 'gmail'

    @staticmethod
    def test_notification_set_scenario(scenario1):
        params = dict(
            description='description goes here.',
            notifier='email-notifier',
            on_start=True
        )
        note = Notification(name='note', parameters=params)
        note.scenario = scenario1
        assert note.scenario

    @staticmethod
    def test_notification_build_profile():
        params = dict(
            description='description goes here.',
            notifier='email-notifier',
            on_start=True
        )
        note = Notification(name='note', parameters=params)
        assert isinstance(note.profile(), dict)

    @staticmethod
    def test_notification_load_params():
        params = dict(
            description='description goes here.',
            notifier='email-notifier',
            foo='bar'
        )
        note = Notification(name='note', parameters=params)
        assert note.foo
