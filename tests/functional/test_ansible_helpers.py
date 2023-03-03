# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 Red Hat, Inc.
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

    Unit tests for testing ansible_helpers.

    :copyright: (c) 2022 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import os

import mock
import pytest

import teflo.helpers
from teflo.ansible_helpers import AnsibleController
from teflo.ansible_helpers import AnsibleService
from teflo.exceptions import AnsibleServiceError


@pytest.fixture()
def script():
    script = {
        "name": "./scripts/add_two_numbers.sh X=12 X=13",
        "creates": "./scripts/hello.txt",
    }
    return script


@pytest.fixture()
def ansible_service(config, asset1):
    config = config
    hosts = [asset1]
    all_hosts = [asset1]
    ansible_options = {}

    return AnsibleService(config, hosts, all_hosts, ansible_options)


class TestAnsibleService(object):
    @staticmethod
    def run_playbook(*args, **kwargs):
        return 0, ""

    @staticmethod
    @mock.patch.object(AnsibleController, "run_playbook", run_playbook)
    def test_run_playbook(ansible_service):
        playbook = [{"name": "hello.yml"}]
        with pytest.raises(AnsibleServiceError) as ex:
            results = ansible_service.run_playbook(playbook)
        assert "Playbook parameter can be a string or dictionary" in ex.value.args[0]

    @staticmethod
    @mock.patch.object(AnsibleController, "run_playbook")
    def test_run_playbook_name_as_str(mock_method, ansible_service):
        playbook = "cbn_execute_script_" + ansible_service.uid + ".yml"
        logger = ansible_service.logger
        ans_verbosity = ansible_service.ans_verbosity
        results = ansible_service.run_playbook(playbook)
        mock_method.assert_called_with(
            playbook="cbn_execute_script_" + ansible_service.uid + ".yml",
            logger=logger,
            extra_vars=None,
            run_options=None,
            ans_verbosity=ans_verbosity,
            env_var=os.environ,
        )

    @staticmethod
    @mock.patch.object(AnsibleController, "run_playbook")
    def test_run_playbook_name_as_dict(mock_method, ansible_service):
        playbook = {"name": "hello.yml"}
        logger = ansible_service.logger
        extra_vars = ansible_service.ans_extra_vars
        ans_verbosity = ansible_service.ans_verbosity
        results = ansible_service.run_playbook(playbook)
        mock_method.assert_called_with(
            playbook="hello.yml",
            logger=logger,
            extra_vars=extra_vars,
            run_options={},
            ans_verbosity=ans_verbosity,
            env_var=os.environ,
        )

    @staticmethod
    @mock.patch.object(AnsibleController, "run_playbook")
    def test_run_playbook_name_as_fqcn(mock_method, ansible_service):
        playbook = "coll.project.hello"
        os.system(
            "mkdir -p /tmp/ws/collections/ansible_collections/coll/project/playbooks"
        )
        os.system(
            "touch /tmp/ws/collections/ansible_collections/coll/project/playbooks/hello.yml"
        )
        test_run = ansible_service.get_playbook_path(
            ansible_service.config.get("WORKSPACE"), playbook
        )
        os.system("rm -rf /tmp/ws/collections")
        assert "ansible_collections/coll/project/playbooks/hello.yml" in test_run

    @staticmethod
    @mock.patch.object(AnsibleController, "run_playbook", run_playbook)
    def test_run_shell_playbook(ansible_service):
        setattr(ansible_service, "uid", "xyz")
        os.system("cp ../assets/script-results-xyz.json ./shell-results-xyz.json ")
        shell = {
            "command": "bash ./scripts/add_two_numbers.sh X=12 X=13",
            "creates": "./scripts/hello.txt",
        }
        shell_results = ansible_service.run_shell_playbook(shell)
        assert isinstance(shell_results, dict)

    @staticmethod
    @mock.patch.object(AnsibleController, "run_playbook", run_playbook)
    def test_run_script_playbook(ansible_service, script):
        setattr(ansible_service, "uid", "xyz")
        os.system("cp ../assets/script-results-xyz.json ./")
        script_results = ansible_service.run_script_playbook(script)
        assert isinstance(script_results, dict)

    @staticmethod
    def test_build_ans_extra_args_with_script(ansible_service, script):
        res = ansible_service.build_ans_extra_args(script)
        assert "creates" in res

    @staticmethod
    def test_build_ans_extra_args_with_ans_options(ansible_service, script):
        ansible_service.options = {"extra_args": "executable=python"}
        res = ansible_service.build_ans_extra_args(script)
        assert "executable" in res

    @staticmethod
    def test_build_ans_extra_args_params_in_ans_options(ansible_service):
        """extra_args with params with '='"""
        script = {
            "name": "./scripts/add_two_numbers.sh ",
            "creates": "./scripts/hello.txt",
        }
        ansible_service.options = {"extra_args": "x=10" " executable=python"}
        res = ansible_service.build_ans_extra_args(script)
        assert "x=10" in script["name"]
        assert "executable" in res

    @staticmethod
    def test_build_ans_extra_args_params_in_ans_options_1(ansible_service):
        """extra_args with params without '='"""
        script = {
            "name": "./scripts/add_two_numbers.sh ",
            "creates": "./scripts/hello.txt",
        }
        ansible_service.options = {"extra_args": "-x 10" " executable=python"}
        res = ansible_service.build_ans_extra_args(script)
        assert "-x 10" in script["name"]
        assert "executable" in res

    @staticmethod
    def test_build_run_options(ansible_service):
        ansible_service.options = {"become_user": "root"}
        res = ansible_service.build_run_options()
        assert res == ansible_service.options

    @staticmethod
    def test_convert_run_options(ansible_service):
        res = ansible_service.convert_run_options({"become_user": "root"})
        assert res == "become_user: root\n"

    @staticmethod
    def test_build_extra_vars(ansible_service):
        ansible_service.options = {
            "extra_vars": {"baseurl": "abc", "file": "hello.txt"}
        }
        res = ansible_service.build_extra_vars()
        assert res == {"baseurl": "abc", "file": "hello.txt", "localhost": False}

    @staticmethod
    def test_group_hosts_equals_string_pass_thru(ansible_service):
        group = ansible_service.create_inv_group()
        assert group == "host_0"

    @staticmethod
    def test_group_multi_hosts_equals_string_pass_thru(ansible_service, asset2):
        ansible_service.hosts.append(asset2)
        group = ansible_service.create_inv_group()
        assert group == "host_0, host_1"

    @staticmethod
    def test_download_roles_empty(ansible_service):
        assert ansible_service.download_roles() is None

    @staticmethod
    @mock.patch("teflo.ansible_helpers.file_mgmt")
    @mock.patch("teflo.ansible_helpers.exec_local_cmd_pipe")
    def test_download_roles_valid(exec_local_cmd_pipe, file_mgmt, ansible_service):
        exec_local_cmd_pipe.return_value = mock.Mock()
        exec_local_cmd_pipe.return_value = 0, "pass"
        file_mgmt.return_value = mock.Mock()
        file_mgmt.return_value = {
            "roles": ["role-123"],
            "collections": ["collection-123"],
        }

        ansible_service.galaxy_options = {
            "role_file": "requirements.yml",
            "roles": ["role-123"],
            "collections": ["collection-123"],
        }
        assert ansible_service.download_roles() is None

    @staticmethod
    def test_download_roles_invalid(ansible_service):
        with pytest.raises(AnsibleServiceError):
            ansible_service.download_roles = mock.Mock()
            ansible_service.download_roles.side_effect = AnsibleServiceError("Error")
            ansible_service.download_roles()
