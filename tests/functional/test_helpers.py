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
    tests.test_helpers

    Unit tests for testing teflo helpers.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from teflo.resources import scenario
import pytest
import os
import mock
from teflo import Teflo
from teflo.core import ImporterPlugin
from teflo.constants import TASKLIST
from teflo.resources.assets import Asset
from teflo.resources.reports import Report
from teflo.resources.executes import Execute
from teflo._compat import ConfigParser
from teflo.utils.config import Config
from teflo.exceptions import TefloError, HelpersError
from teflo.provisioners.ext import BeakerClientProvisionerPlugin
from teflo.helpers import DataInjector, validate_render_scenario, set_task_class_concurrency, \
    mask_credentials_password, sort_tasklist, find_artifacts_on_disk, \
    get_default_provisioner_plugin, get_ans_verbosity, schema_validator, filter_resources_labels,\
    create_individual_testrun_results, create_aggregate_testrun_results, filter_notifications_to_skip, \
    check_for_var_file


@pytest.fixture(scope='class')
def task_concurrency_config():
    config_file = '../assets/teflo.cfg'
    cfgp = ConfigParser()
    cfgp.read(config_file)
    cfgp.set('task_concurrency', 'provision', 'True')
    cfgp.set('task_concurrency', 'report', 'True')
    with open(config_file, 'w') as cf:
        cfgp.write(cf)
    os.environ['TEFLO_SETTINGS'] = config_file
    config = Config()
    config.load()
    return config


@pytest.fixture(scope='class')
def data_injector():
    class Host(object):
        def __init__(self):
            self.name = 'node01'
            self.random = '123'
            self.random_01 = ['123']
            self.metadata = {
                'k1': 'v1',
                'k2': ['item1', 'item2'],
                'k3': {'k1': 'v1'},
                'k4': {'k1': [{'sk1': 'sv1'}]},
                'k5': [{'k1': 'v1'}]
            }

    return DataInjector([Host()])


@pytest.fixture(scope='class')
def task_host(task_concurrency_config):
    params = dict(groups='test_group',
                  ip_address='1.2.3.4')
    host = Asset(name='Host01',
                 config=task_concurrency_config,
                 parameters=params)
    return host


@pytest.fixture(scope='class')
@mock.patch('teflo.resources.reports.get_importers_plugin_list')
@mock.patch('teflo.resources.reports.get_importer_plugin_class')
def task_report(mock_plugin_class, mock_plugin_list, task_concurrency_config):
    e_params = dict(description='description', hosts='test', executor='runner')
    ex = Execute(name='dummy_execute', parameters=e_params)
    mock_plugin_list.return_value = ['polarion']
    mock_plugin_class.return_value = ImporterPlugin
    params = dict(description='description', executes=[ex],
                  provider=dict(name='polarion',
                                credential='polarion'
                                ),
                  do_import=False)
    report = Report(name='/tmp/dummy.xml', parameters=params, config=task_concurrency_config)
    report.do_import = False
    return report


@pytest.fixture(scope='function')
def os_creds():
    return dict(auth_url='http://test', username='tester', password='changeme')


@pytest.fixture(scope='function')
def rp_creds():
    return dict(rp_url='http://test', api_token='1234-456-78912-4567')


@pytest.fixture(scope='function')
def aws_creds():
    return dict(aws_access_key_id='ABCDEFG', aws_secret_access_key='abc123456defg')


@pytest.fixture(scope='class')
def data_folder():
    data_folder = '/tmp/.results'
    os.system('mkdir /tmp/1 /tmp/.results /tmp/.results/artifacts /tmp/.results/logs '
              '/tmp/.results/artifacts/localhosts '
              '/tmp/.results/artifacts/localhosts/payload_eg '
              '/tmp/.results/artifacts/localhosts/payload_eg/results')
    os.system('touch /tmp/.results/artifacts/localhosts/payload_eg/results/junit_example.xml '
              '/tmp/.results/junit2.xml /tmp/.results/junit3.xml')
    return data_folder


@pytest.fixture(scope='class')
def teflo1():
    teflo = Teflo(data_folder='/tmp', workspace='/tmp', labels=('label1', 'label2'), skip_notify=('note01',))
    return teflo


class TestDataInjector(object):

    def test_constructor(self, data_injector):
        assert isinstance(data_injector, DataInjector)

    def test_valid_host(self, data_injector):
        h = data_injector.host_exist('node01')
        assert getattr(h, 'name') == 'node01'

    def test_invalid_host(self, data_injector):
        with pytest.raises(TefloError) as ex:
            data_injector.host_exist('null')

        assert 'Node null not found!' in ex.value.args

    def test_inject_uc01(self, data_injector):
        cmd = data_injector.inject('cmd { node01.random }')
        assert 'cmd 123' == cmd

    def test_inject_uc02(self, data_injector):
        cmd = data_injector.inject('cmd { node01.metadata.k1 }')
        assert 'cmd v1' == cmd

    def test_inject_uc03(self, data_injector):
        cmd = data_injector.inject('cmd { node01.metadata.k2[1] }')
        assert 'cmd item2' == cmd

    def test_inject_uc04(self, data_injector):
        cmd = data_injector.inject('cmd { node01.metadata.k3.k1 }')
        assert 'cmd v1' == cmd

    def test_inject_uc05(self, data_injector):
        cmd = data_injector.inject('cmd { node01.metadata.k4.k1[0].sk1 }')
        assert 'cmd sv1' == cmd

    def test_inject_uc06(self, data_injector):
        cmd = data_injector.inject('cmd { node01.metadata.k5[0].k1 }')
        assert 'cmd v1' == cmd

    def test_inject_uc07(self, data_injector):
        with pytest.raises(TefloError):
            data_injector.inject('cmd { node01.metadata.null }')

    def test_inject_uc08(self, data_injector):
        data_injector.inject('cmd { node01.random_01[0] }')

    def test_inject_uc09(self, data_injector):
        with pytest.raises(AttributeError) as ex:
            data_injector.inject('cmd { node01.null }')
        assert 'null not found in host node01!' in ex.value.args

    def test_inject_uc10(self, data_injector):
        cmd = data_injector.inject('cmd')
        assert cmd == 'cmd'

    def test_inject_jsonpath_support_uc1(self, data_injector):
        cmd = data_injector.inject('cmd { .spec }')
        assert cmd == 'cmd { .spec }'

    def test_inject_jsonpath_support_uc2(self, data_injector):
        cmd = data_injector.inject('cmd { $ }')
        assert cmd == 'cmd { $ }'

    def test_inject_jsonpath_support_uc3(self, data_injector):
        cmd = data_injector.inject('cmd { @ }')
        assert cmd == 'cmd { @ }'

    def test_inject_jsonpath_support_uc4(self, data_injector):
        cmd = data_injector.inject('cmd { range. }')
        assert cmd == 'cmd { range. }'

    def test_inject_jsonpath_support_uc5(self, data_injector):
        cmd = data_injector.inject('cmd { test: dictionary }')
        assert cmd == 'cmd { test: dictionary }'

    def test_inject_jsonpath_support_uc6(self, data_injector):
        cmd = data_injector.inject("cmd { 'test': 'dictionary' }")
        assert cmd == "cmd { 'test': 'dictionary' }"

    def test_inject_dictionary_01(self, data_injector):
        cmd = data_injector.inject_dictionary(dict(ans_var='{ node01.random }'))
        assert cmd.get('ans_var') == '123'

    def test_inject_dictionary_02(self, data_injector):
        cmd = data_injector.inject_dictionary(dict(ans_var=['{ node01.random }']))
        assert cmd.get('ans_var')[-1] == '123'

    def test_inject_dictionary_03(self, data_injector):
        cmd = data_injector.inject_dictionary(
            dict(ans_var={'{ node01.metadata.k1 }': '{ node01.random_01[0] }'})
        )
        assert cmd.get('ans_var').get('v1') == '123'

    def test_inject_dictionary_04(self, data_injector):
        cmd = data_injector.inject_dictionary(dict(ans_args='-c -e { node01.random } { node01.random_01[0]}'))
        assert '123' in cmd.get('ans_args')

    def test_inject_list_01(self, data_injector):
        cmd = data_injector.inject_list(['{ node01.random }'])
        assert cmd[0] == '123'

    def test_inject_list_02(self, data_injector):
        cmd = data_injector.inject_list([dict(ans_args='-c -e { node01.random } { node01.random_01[0]}')])
        assert isinstance(cmd[0], dict)
        assert '123' in cmd[0].get('ans_args')

    def test_inject_list_03(self, data_injector):
        cmd = data_injector.inject_list(['hello', ['world', '{ node01.metadata.k5[0].k1 }']])
        assert cmd[0] == 'hello'
        assert isinstance(cmd[1], list)
        assert cmd[1] == ['world', 'v1']


def test_validate_render_scenario_no_include(task_concurrency_config):
    scenario_graph = validate_render_scenario(os.path.abspath('../assets/no_include.yml'), task_concurrency_config)
    assert len(scenario_graph) == 1


def test_validate_render_scenario_correct_include(task_concurrency_config):
    scenario_graph = validate_render_scenario('../assets/correct_include_descriptor.yml', task_concurrency_config)
    assert len(scenario_graph) == 2


def test_validate_render_scenario_wrong_include(task_concurrency_config):
    with pytest.raises(TefloError) as ex:
        validate_render_scenario('../assets/wrong_include_descriptor.yml', task_concurrency_config)
    assert "Included File is invalid or Include section is empty. You have to provide valid scenario files to be included." in ex.value.args[
        0]


def test_validate_render_scenario_empty_include(task_concurrency_config):
    with pytest.raises(TefloError) as ex:
        validate_render_scenario('../assets/empty_include.yml', task_concurrency_config)
    assert "Included File is invalid or Include section is empty. You have to provide valid scenario files to be included." in ex.value.args[
        0]


def test_set_task_concurrency_provision_is_false(host):
    for task in host.get_tasks():
        if task['task'].__task_name__ == 'provision':
            assert set_task_class_concurrency(task, host)['task'].__concurrent__ is False


def test_set_task_concurrency_report_is_false(report_resource):
    for task in report_resource.get_tasks():
        if task['task'].__task_name__ == 'report':
            assert set_task_class_concurrency(task, report_resource)['task'].__concurrent__ is False


def test_set_task_concurrency_provision_is_true(task_host):
    for task in task_host.get_tasks():
        if task['task'].__task_name__ == 'provision':
            assert set_task_class_concurrency(task, task_host)['task'].__concurrent__ is True


def test_set_task_concurrency_report_is_true(task_report):
    for task in task_report.get_tasks():
        if task['task'].__task_name__ == 'report':
            assert set_task_class_concurrency(task, task_report)['task'].__concurrent__ is True


def test_mask_credentials_password_param(os_creds):
    key_len = len(os_creds.get('password'))
    creds = mask_credentials_password(os_creds)
    assert '*' in creds.get('password')


def test_mask_credentials_password_token_param(rp_creds):
    key_len = len(rp_creds.get('api_token'))
    creds = mask_credentials_password(rp_creds)
    assert '*' in creds.get('api_token')


def test_mask_credentials_password_key_param(aws_creds):
    key_len = len(aws_creds.get('aws_secret_access_key'))
    creds = mask_credentials_password(aws_creds)
    assert '*' in creds.get('aws_secret_access_key')


def test_sort_tasklist():
    user_task = ['orchestrate', 'report', 'validate', 'cleanup', 'execute', 'provision']
    assert sort_tasklist(user_task) == TASKLIST


def test_find_artifacts_on_disk_no_art_location_1(data_folder):
    """
    This test verifies that no artifact locations is given we walk the results
    looking for all xml files.
    """
    assert len(find_artifacts_on_disk(data_folder, '*xml')) == 3


def test_find_artifacts_on_disk_no_art_location_2(data_folder):
    """
    This test verifies that no artifact locations is given we walk the results
    looking for specific xml file.
    """
    assert len(find_artifacts_on_disk(data_folder, 'junit2.xml')) == 1


def test_find_artifacts_on_disk_no_art_location_3(data_folder):
    """
    This test verifies that no artifact locations is given we walk the results
    looking for specific files in a subdirectory of results folder.
    """
    assert len(find_artifacts_on_disk(data_folder, 'payload_eg/*')) == 1


def test_find_artifacts_on_disk_art_location_1(data_folder):
    """
    This test verifies that with artifact locations we check the location and walk the results
    directory looking for a file using specific pattern.
    """
    art_location = ['artifacts/localhosts/payload_eg/', 'artifacts/localhosts/payload_eg/results',
                    'artifacts/localhosts/payload_eg/results/junit_example.xml']
    assert len(find_artifacts_on_disk(data_folder, 'junit_*.xml', art_location)) == 1


def test_find_artifacts_on_disk_art_location_2(data_folder):
    """
    This test verifies that with artifact locations we check the location and walk the results
    directory looking for all files using a pattern.
    """
    art_location = ['artifacts/localhosts/payload_eg/', 'artifacts/localhosts/payload_eg/results',
                    'artifacts/localhosts/payload_eg/results/junit_example.xml']
    assert len(find_artifacts_on_disk(data_folder, '*.xml', art_location)) == 3


def test_find_artifacts_on_disk_art_location_3(data_folder):
    """
    This test verifies that with artifact locations we check the location and walk the results
    directory looking for a specific file.
    """
    art_location = ['artifacts/localhosts/payload_eg/', 'artifacts/localhosts/payload_eg/results',
                    'artifacts/localhosts/payload_eg/results/junit_example.xml']
    assert len(find_artifacts_on_disk(data_folder, 'junit3.xml', art_location)) == 1


def test_find_artifacts_on_disk_art_location_4(data_folder):
    """
    This test verifies that with artifact locations we check the location and walk the results
    directory looking for a file that doesn't exist.
    """
    art_location = ['artifacts/localhosts/payload_eg/', 'artifacts/localhosts/payload_eg/results',
                    'artifacts/localhosts/payload_eg/results/junit_example.xml']
    assert len(find_artifacts_on_disk(data_folder, 'hello.xml', art_location)) == 0


def test_find_artifacts_on_disk_art_location_5(data_folder):
    """
    This test verifies that with artifact locations we check the location and walk the results
    directory looking for a files using * within a specific subdirectory. The regex generated
    will match all three items in art_locations dictionary.
    """
    art_location = ['artifacts/localhosts/payload_eg/', 'artifacts/localhosts/payload_eg/results',
                    ' artifacts/localhosts/payload_eg/results/junit_example.xml']
    assert len(find_artifacts_on_disk(data_folder, 'payload_eg/*', art_location)) == 3


def test_find_artifacts_on_disk_art_location_6(data_folder):
    """
    This test verifies that with artifact locations we check the location and walk the results
    directory looking for a specific subdirectory. The regex generated will only match payload_eg
    """
    art_location = ['artifacts/localhosts/payload_eg/', 'artifacts/localhosts/payload_eg/results',
                    'artifacts/localhosts/payload_eg/results/junit_example.xml']
    assert len(find_artifacts_on_disk(data_folder, 'payload_eg/', art_location)) == 1


def test_find_artifacts_on_disk_art_location_7(data_folder):
    """
    This test verifies that with artifact locations we check the location and walk the results
    directory looking for a specific file that is in results directory but the results directory
    was also specified in the art_locations.
    """
    art_location = ['artifacts/localhosts/payload_eg/', 'artifacts/localhosts/payload_eg/results',
                    'artifacts/localhosts/payload_eg/results/junit_example.xml',
                    'junit2.xml']
    assert len(find_artifacts_on_disk(data_folder, 'junit2.xml', art_location)) == 1


@mock.patch('teflo.helpers.get_provisioner_plugin_class')
def test_get_default_provisioner_plugin_method(mock_method):
    mock_method.return_value = BeakerClientProvisionerPlugin
    assert get_default_provisioner_plugin() == BeakerClientProvisionerPlugin


def test_ansible_verbosity_1(config):
    """This test verifies the ansible verbosity set using teflo.cfg is valid. For this test
    teflo.cfg under ../assets/teflo.cfg is used and has ansible_verbosity set as 'v'"""
    assert get_ans_verbosity(config) == 'v'


def test_ansible_verbosity_2(config):
    """This test verifies if incorrect values for ansible_verbosity is set in teflo.cfg, then verbosity is
     'vvvv' if teflo's logging level is debug.  For this test logging_level debug is set in ../assets/teflo.cfg"""
    config["ANSIBLE_VERBOSITY"] = 'aavv'
    assert get_ans_verbosity(config) == 'vvvv'


def test_ansible_verbosity_3(config):
    """This test verifies if incorrect values for ansible_verbosity is set in teflo.cfg, verbosity is
     None if teflo's logging level is info"""
    config["ANSIBLE_VERBOSITY"] = 'aavv'
    config["LOG_LEVEL"] = 'info'
    assert get_ans_verbosity(config) is None


def test_ansible_verbosity_4(config):
    """This test verifies if ansible_verbosity is NOT set in teflo.cfg, verbosity is
     None if teflo's logging level is info"""
    config["ANSIBLE_VERBOSITY"] = None
    config["LOG_LEVEL"] = 'info'
    assert get_ans_verbosity(config) is None


def test_ansible_verbosity_5(config):
    """This test verifies if ansible_verbosity is NOT set in teflo.cfg, verbosity is
     'vvvv' if teflo's logging level is debug. For this test logging_level debug is set in ../assets/teflo.cfg"""
    config["ANSIBLE_VERBOSITY"] = None
    assert get_ans_verbosity(config) == 'vvvv'


def test_schema_validator_no_creds():
    params = dict(key1='val1', key2=['val2', 'val3'])
    schema_validator(schema_data=params, schema_files=[os.path.abspath('../assets/schemas/schema_test.yml')])


def test_schema_validator_with_creds():
    params = dict(key1='val1', key2=['val2', 'val3'])
    creds = dict(name='test', username='user', password='pass123')
    schema_validator(schema_data=params,
                     schema_creds=creds,
                     schema_files=[os.path.abspath('../assets/schemas/schema_test.yml')])


def test_schema_validator_failure():
    params = dict(key1=1, key2=['val2', 'val3'])
    with pytest.raises(Exception):
        schema_validator(schema_data=params, schema_files=[os.path.abspath('../assets/schemas/schema_test.yml')])


def test_filter_resources_01(teflo1, asset2, asset3):
    """ this test verifies only resources which match the labels provided are picked"""
    res_list = [asset2, asset3]
    res = filter_resources_labels(res_list, teflo1.teflo_options)
    assert res[0] == asset2


def test_filter_resources_02(teflo1, asset2, asset3):
    """ this test verifies resources which match the skip_labels are skipped"""
    res_list = [asset2, asset3]
    teflo1.teflo_options.update(labels=tuple(), skip_labels=('label2',))
    res = filter_resources_labels(res_list, teflo1.teflo_options)
    assert res[0] == asset3


def test_filter_resources_03(asset2, asset3):
    """ this test verifies resource list is sent back when no labels or skip_labels are matched"""
    res_list = [asset2, asset3]
    res = filter_resources_labels(res_list, {})
    assert asset2 in res
    assert asset3 in res


@mock.patch('teflo.helpers.search_artifact_location_dict')
def test_create_individual_testrun_results(mock_method):
    mock_method.return_value = ['../assets/artifacts/host03/sample.xml']
    res = create_individual_testrun_results({}, {})
    assert res[0]['sample.xml'] == {'total_tests': 4, 'failed_tests': 0, 'skipped_tests': 0, 'passed_tests': 4}


@mock.patch('teflo.helpers.search_artifact_location_dict')
def test_create_individual_testrun_results_1(mock_method):
    """this test verifies xmls with tag testsuite and testsuites work correctly"""
    mock_method.return_value = ['../assets/artifacts/host03/sample1.xml', '../assets/artifacts/host03/sample.xml']
    res = create_individual_testrun_results({}, {})
    assert res[0]['sample1.xml'] == {'total_tests': 2, 'failed_tests': 0, 'skipped_tests': 0, 'passed_tests': 2}
    assert res[1]['sample.xml'] == {'total_tests': 4, 'failed_tests': 0, 'skipped_tests': 0, 'passed_tests': 4}


@mock.patch('teflo.helpers.search_artifact_location_dict')
def test_create_individual_testrun_results_with_wrong_xml(mock_method):
    mock_method.return_value = ['../assets/artifacts/host01/sample1.xml']
    with pytest.raises(TefloError) as ex:
        create_individual_testrun_results({}, {})
        assert "The xml file ../assets/artifacts/host01/sample1.xml is malformed" in ex.value.args


@mock.patch('teflo.helpers.search_artifact_location_dict')
def test_create_individual_testrun_results_with_incorrect_root_tag(mock_method):
    """The test case verifies that if the root tag is not testsuites or testsuite, it skips that xml with a warning"""
    mock_method.return_value = ['../assets/artifacts/host03/sample2.xml']
    res = create_individual_testrun_results({}, {})
    assert res == []


def test_create_aggregate_testrun_results():
    ind_res = [
                {'sample.xml': {'total_tests': 2, 'failed_tests': 0, 'skipped_tests': 0, 'passed_tests': 2}},
                {'sample1.xml': {'total_tests': 4, 'failed_tests': 2, 'skipped_tests': 0, 'passed_tests': 2}}
               ]
    res = create_aggregate_testrun_results(ind_res)
    assert res['aggregate_testrun_results']['total_tests'] == 6
    assert res['aggregate_testrun_results']['failed_tests'] == 2


def test_filter_notifications_to_skip_01(teflo1, notification_on_start_resource, notification_default_resource):
    """ this test verifies resources which match skip-notify list are not included"""
    notify_list = [notification_on_start_resource, notification_default_resource]
    res = filter_notifications_to_skip(notify_list, teflo1.teflo_options)
    assert res[0] == notification_default_resource


def test_filter_notifications_to_skip_02(teflo1, notification_on_start_resource, notification_default_resource):
    """ this test verifies skip-notify is not present original  list of notification resources are returned"""
    notify_list = [notification_on_start_resource, notification_default_resource]
    teflo1.teflo_options.update(skip_notify=())
    res = filter_notifications_to_skip(notify_list, teflo1.teflo_options)
    assert res == notify_list


def test_check_for_var_file_in_ws(teflo1):
    """This test is used to test method check_for_var_file when variable file is present in the
       workspace as var_file.yml"""
    os.system("cp ../assets/vars_data.yml /tmp/var_file.yml")
    res = check_for_var_file(teflo1.config)
    assert res[0] == '/tmp/var_file.yml'
    assert res[1] == os.path.abspath('../assets/vars_data.yml')
    os.system("rm /tmp/var_file.yml")


def test_check_for_var_file_in_ws_under_vars(teflo1):
    """This test is used to test method check_for_var_file when variable file is present in the
       workspace under vars folder as well as a var_file.yml is present """
    os.system("mkdir /tmp/vars")
    os.system("mkdir /tmp/vars/dir1")
    os.system("cp ../assets/vars_data.yml /tmp/vars/var1.yml")
    os.system("cp ../assets/vars_data.yml /tmp/vars/dir1/var2.yml")
    os.system("touch /tmp/vars/dir1/test.cfg")
    os.system("cp ../assets/vars_data.yml /tmp/var_file.yml")

    res = check_for_var_file(teflo1.config)
    assert '/tmp/vars/var1.yml' in res
    assert '/tmp/vars/dir1/var2.yml' in res
    assert res[-1] == os.path.abspath('../assets/vars_data.yml')
    assert res[-2] == '/tmp/var_file.yml'
    assert '/tmp/vars/dir1/test.cfg' not in res
    os.system("rm -r /tmp/vars")
    os.system("rm /tmp/var_file.yml")


def test_check_for_var_file_with_default_path_as_dir(teflo1):
    """This test is used to test method check_for_var_file when defaulr variable file path in teflo.cfg
    is a directory"""
    os.system("mkdir /tmp/teflo_var_file")

    os.system("mkdir /tmp/teflo_var_file/dir1")
    os.system("cp ../assets/vars_data.yml /tmp/teflo_var_file/var1.yml")
    os.system("cp ../assets/vars_data.yml /tmp/teflo_var_file/dir1/var2.yml")

    teflo1.config['VAR_FILE'] = '/tmp/teflo_var_file'

    res = check_for_var_file(teflo1.config)
    assert '/tmp/teflo_var_file/dir1/var2.yml' in res
    assert '/tmp/teflo_var_file/var1.yml' in res
    assert len(res) == 2
    os.system("rm -r /tmp/teflo_var_file")
