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
    tests.test_teflo

    Unit tests for testing teflo module.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import os
import sys
from teflo.utils.scenario_graph import ScenarioGraph

import mock
import pytest
import yaml

from teflo import Teflo
from teflo.constants import RESULTS_FILE
from teflo.exceptions import TefloError
from teflo.helpers import template_render
from click.testing import CliRunner
from teflo.cli import teflo


@pytest.fixture()
def runner():
    return CliRunner()


class TestTeflo(object):

    @staticmethod
    def test_create_teflo_instance_01():
        teflo = Teflo(data_folder='/tmp')
        assert isinstance(teflo, Teflo)

    @staticmethod
    def test_create_teflo_instance_02():
        teflo = Teflo(log_level='info', data_folder='/tmp')
        assert teflo.config['LOG_LEVEL'] == 'info'

    @staticmethod
    def test_create_teflo_instance_03():
        """verifies teflo instance is created when data folder and workspace is provided and kwargs in none"""
        teflo = Teflo(data_folder='/tmp', workspace='/tmp')
        assert '/tmp' in teflo.config['DATA_FOLDER']
        assert teflo.workspace == '/tmp'
        assert teflo.teflo_options == {}

    @staticmethod
    def test_create_teflo_instance_with_labels():
        """this test is to verify teflo instance gets created when labels/skip_labels are passed"""
        teflo = Teflo(data_folder='/tmp', workspace='/tmp', labels=('lab1', 'lab2'), skip_labels=('lab3',))
        assert teflo.teflo_options['labels'] == ('lab1', 'lab2')
        assert teflo.teflo_options['skip_labels'] == ('lab3', )

    @staticmethod
    @mock.patch.object(os, 'makedirs')
    @pytest.mark.filterwarnings('ignore::DeprecationWarning')
    def test_create_teflo_instance_04(mock_method):
        with pytest.raises(TefloError):
            mock_method.side_effect = IOError()
            Teflo(data_folder='/tmp', workspace='/tmp')

    @staticmethod
    @mock.patch.object(os, 'makedirs')
    def test_create_teflo_instance_05(mock_method):
        with pytest.raises(TefloError):
            mock_method.side_effect = IOError()
            mock_method.side_effect.errno = 13
            Teflo(data_folder='/tmp', workspace='/tmp')

    @staticmethod
    def test_data_folder_property():
        teflo = Teflo(data_folder='/tmp')
        assert teflo.data_folder == teflo.config['DATA_FOLDER']

    @staticmethod
    def test_results_file_property():
        teflo = Teflo(data_folder='/tmp')
        assert teflo.results_file == os.path.join(
            teflo.data_folder, RESULTS_FILE)

    @staticmethod
    def test_artifacts_folder_created():
        teflo = Teflo(data_folder='/tmp')
        assert (os.path.exists(os.path.join(teflo.config['RESULTS_FOLDER'], 'artifacts')))

    @staticmethod
    @mock.patch.object(yaml, 'safe_load')
    def test_teflo_load_from_yaml_01(mock_method, basic_scenario_graph_with_provision_only: ScenarioGraph):
        mock_method.return_value = {}
        teflo = Teflo(data_folder='/tmp')
        teflo.load_from_yaml(basic_scenario_graph_with_provision_only)

# TODO: Scenario Graph related
# REFACTOR the tests below with scenario graph
# We should either write some new tests with scenario graph
# or reuse below tests

    # @staticmethod
    # def test_teflo_load_from_yaml_02():
    #     data = list()
    #     data.append(template_render('../assets/descriptor.yml', os.environ))
    #     teflo = Teflo(data_folder='/tmp')
    #     teflo.load_from_yaml(data)

    # @staticmethod
    # def test_teflo_load_from_yaml_03():
    #     data = list()
    #     data.append(template_render('../assets/descriptor.yml', os.environ))
    #     teflo = Teflo(data_folder='/tmp')
    #     teflo.config['CREDENTIALS'] = [{'name': 'provider'}]
    #     teflo.load_from_yaml(data)

    # @staticmethod
    # def test_teflo_load_from_yaml_04():
    #     data = list()
    #     data.append(template_render('../assets/descriptor.yml', os.environ))
    #     teflo = Teflo(data_folder='/tmp')
    #     teflo.load_from_yaml(data)

    # @staticmethod
    # def test_teflo_load_from_yaml_05():
    #     data = list()
    #     data.append(template_render('../assets/correct_include_descriptor.yml', os.environ))
    #     data.append(template_render('../assets/common.yml', os.environ))
    #     teflo = Teflo(data_folder='/tmp')
    #     teflo.load_from_yaml(data)
    #     assert teflo.scenario.child_scenarios

    @staticmethod
    def test_name_property_01():
        teflo = Teflo(data_folder='/tmp')
        assert teflo.name == 'teflo'

    @staticmethod
    def test_name_property_02():
        teflo = Teflo(import_name='__main__', data_folder='/tmp')
        assert teflo.name != 'teflo'

    @staticmethod
    def test_name_property_03():
        sys.modules['__main__'].__file__ = None
        teflo = Teflo(import_name='__main__', data_folder='/tmp')
        assert teflo.name == '__main__'

    @staticmethod
    def test_static_inventory_folder():
        teflo = Teflo(import_name='__main__', data_folder='/tmp')
        assert teflo.static_inv_dir
        assert teflo.config['INVENTORY_FOLDER'] == '/tmp'

    @staticmethod
    def test_validate_labels_01(scenario_labels):
        """ this test verifies validate_labels throws error when wrong labels is provided"""
        teflo = Teflo(data_folder='/tmp', workspace='/tmp', labels=('lab1',))
        teflo.scenario = scenario_labels
        with pytest.raises(TefloError) as ex:
            teflo._validate_labels()
        assert "No resources were found corresponding to the label/skip_label lab1. " \
               "Please check the labels provided during the run match the ones in "\
               "scenario descriptor file" in ex.value.args[0]

    @staticmethod
    def test_validate_labels_02(scenario_labels):
        """ this test verifies validate_labels throws error when wrong skip_labels is provided"""
        teflo = Teflo(data_folder='/tmp', workspace='/tmp', skip_labels=('lab1', 'label2'))
        with pytest.raises(TefloError) as ex:
            teflo._validate_labels()
        assert "No resources were found corresponding to the label/skip_label lab1. " \
               "Please check the labels provided during the run match the ones in "\
               "scenario descriptor file" in ex.value.args[0]

    @staticmethod
    def test_collect_final_passed_failed_tasks_status(runner):
        """This test is to verify if there are failed tasks they are not seen in passed task list"""
        results = runner.invoke(teflo, ['notify', '-s', '../assets/scenario_graph_basic_test/sdf8.yml',
                                        '-w', '../assets/scenario_graph_basic_test/']
                                )

        assert results.exit_code == 0
        assert "* Passed Tasks                   : ['provision']" in results.output
        assert "* Failed Tasks                   : ['execute']" in results.output

    @staticmethod
    def test_generic_notify_not_in_info_log_level(runner):
        """
        This test ensures there are no generic notifications
        when there is no notification block in sdf
        """
        results = runner.invoke(teflo,
                                ['notify', '--log-level', 'info', '-s', '../assets/scenario_graph_basic_test/sdf8.yml',
                                 '-w', '../assets/scenario_graph_basic_test/']
                                )
        assert results.exit_code == 0
        assert "Starting tasks on pipeline: notify" not in results.stdout

    @staticmethod
    def test_generic_notify_in_debug_log_level(runner):
        """
        This test ensures the generic notifications are present in debug log
        level when there is no notification block in sdf
        """
        results = runner.invoke(teflo,
                                ['notify', '--log-level', 'debug', '-s', '../assets/scenario_graph_basic_test/sdf8.yml',
                                 '-w', '../assets/scenario_graph_basic_test/']
                                )
        assert results.exit_code == 0
        assert "Starting tasks on pipeline: notify" in results.output
