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
    tests.ansible_helpers

    Unit tests for testing resource_checker class

    :copyright: (c) 2020 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import pytest
import mock
import json
from teflo.utils.resource_checker import ResourceChecker
from teflo.ansible_helpers import AnsibleService
from teflo.helpers import StatusPageHelper
from teflo.exceptions import TefloError
import cachetclient.cachet as cachet


@pytest.fixture()
def resource_checker1(config, scenario):
    scenario.resource_check['script'] = [{'name': 'abc.py', 'executables': 'python'}]
    #scenario.resource_check['service'] = ['umb']
    scenario.resource_check['monitored_services'] = ['umb']
    res_check = ResourceChecker(scenario, config)
    res_check.ans_service = AnsibleService(config, hosts=[], all_hosts=[], ansible_options=None)
    return res_check


@pytest.fixture()
def resource_checker2(config, scenario):
    scenario.resource_check['playbook'] = [{'name': 'pqr.yml'}]
    #scenario.resource_check['service'] = ['umb']
    scenario.resource_check['monitored_services'] = ['umb']
    res_check = ResourceChecker(scenario, config)
    res_check.ans_service = AnsibleService(config, hosts=[], all_hosts=[], ansible_options=None)
    return res_check


@pytest.fixture()
def resource_checker3(config, scenario):
    config['RESOURCE_CHECK_ENDPOINT'] = 'https://internal.status.redhat.com/api/v1'
    # scenario.resource_check['service'] = ['umb']
    scenario.resource_check['monitored_services'] = ['umb']
    res_check = ResourceChecker(scenario, config)
    res_check.ans_service = AnsibleService(config, hosts=[], all_hosts=[], ansible_options=None)
    return res_check

@pytest.fixture()
def resource_checker4(config, scenario):
    config['RESOURCE_CHECK_ENDPOINT'] = 'https://semaphore-status.statuspage.io/'
    # scenario.resource_check['service'] = ['umb']
    scenario.resource_check['monitored_services'] = ['psi-registry']
    res_check = ResourceChecker(scenario, config)
    res_check.ans_service = AnsibleService(config, hosts=[], all_hosts=[], ansible_options=None)
    return res_check


@pytest.fixture()
def resource_checker5(config, scenario):
    config['RESOURCE_CHECK_ENDPOINT'] = 'https://semaphore-status.statuspage.io/'
    # scenario.resource_check['service'] = ['umb']
    scenario.resource_check['monitored_services'] = ['umb']
    res_check = ResourceChecker(scenario, config)
    res_check.ans_service = AnsibleService(config, hosts=[], all_hosts=[], ansible_options=None)
    return res_check


class TestResourceChecker(object):

    @staticmethod
    def run_script_playbook(*args, **kwargs):
        return {'rc': 1, 'host': 'localhost', 'err': 'ERROR'}

    @staticmethod
    def run_playbook(*args, **kwargs):
        return [1, '']

    @staticmethod
    def get_info(*args,**kwargs):
        return {
            "psi-registry": {
            "created_at": "2021-01-14T14:07:17.527Z",
            "description": "Container registry provided by PSI.",
            "group": False,
            "group_id": None,
            "id": "8sjpsjffpr4p",
            "name": "psi-registry",
            "only_show_if_degraded": False,
            "page_id": "h4lkfpbd49vk",
            "position": 22,
            "showcase": False,
            "start_date": "2021-01-14",
            "status": "operational",
            "updated_at": "2021-02-04T20:07:28.764Z"
        }
        }

    @staticmethod
    def my_get(*args, **kwargs):
        comp_data = {
                      "meta": {
                        "pagination": {
                          "total": 1,
                          "count": 1,
                          "per_page": 20,
                          "current_page": 1,
                          "total_pages": 1,
                          "links": {
                            "next_page": "null",
                            "previous_page": "null"
                          }
                        }
                      },
                      "data": []
                    }
        return json.dumps(comp_data)

    @staticmethod
    @mock.patch.object(AnsibleService, 'run_script_playbook', run_script_playbook)
    def test_check_custom_resource_script(resource_checker1):
        with pytest.raises(TefloError) as ex:
            resource_checker1.validate_resources()
        assert 'Failed to run resource_check validation for playbook/script' in ex.value.args[0]

    @staticmethod
    @mock.patch.object(AnsibleService, 'run_playbook', run_playbook)
    def test_check_custom_resource_playbook(resource_checker2):
        with pytest.raises(TefloError) as ex:
            resource_checker2.validate_resources()
        assert 'Failed to run resource_check validation for playbook/script' in ex.value.args[0]

    @staticmethod
    @mock.patch.object(cachet.Components, 'get', my_get)
    def test_check_custom_resource_service(resource_checker3):
        with pytest.raises(TefloError) as ex:
            resource_checker3.validate_resources()
        assert 'will not be run! Not all external resources are available or valid' in ex.value.args[0]


    @staticmethod
    @mock.patch.object(StatusPageHelper,"get_info",get_info)
    def test_check_custom_resource_service1(resource_checker4):
        with pytest.raises(TefloError) as ex:
            resource_checker4.validate_resources()
        assert not 'will not be run! Not all external resources are available or valid' in ex.value.args[0]


    @staticmethod
    @mock.patch.object(StatusPageHelper,"get_info",get_info)
    def test_check_custom_resource_service1(resource_checker5):
        with pytest.raises(TefloError) as ex:
            resource_checker5.validate_resources()
        assert 'will not be run! Not all external resources are available or valid' in ex.value.args[0]
