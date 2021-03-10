# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Red Hat, Inc.
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
    tests.test_cli

    Unit tests for testing teflo cli.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import mock
import pytest
import yaml
import json
from teflo import Teflo
from teflo.cli import print_header, teflo
from click.testing import CliRunner
from teflo.exceptions import TefloError


@pytest.fixture(scope='class')
def runner():
    return CliRunner()


class TestCli(object):
    @staticmethod
    def test_print_header():
        assert print_header() is None

    @staticmethod
    def test_teflo_create(runner):
        results = runner.invoke(teflo, ['-v', 'create'])
        assert results.exit_code != 0

    @staticmethod
    def test_invalid_validate(runner):
        results = runner.invoke(teflo, ['validate', '-s', 'cdf.yml'])
        assert 'You have to provide a valid scenario file.' in results.output

    @staticmethod
    @mock.patch.object(Teflo, 'run')
    def test_valid_validate(mock_method, runner):
        mock_method.return_value = 0
        results = runner.invoke(
            teflo, ['validate', '-s', '../assets/common.yml',
                     '-d', '/tmp']
        )
        assert results.exit_code == 0

    @staticmethod
    def test_invalid_run(runner):
        results = runner.invoke(teflo, ['run', '-s', 'cdf.yml'])
        assert 'You have to provide a valid scenario file.' in results.output

    @staticmethod
    @mock.patch.object(Teflo, 'run')
    def test_valid_run(mock_method, runner):
        mock_method.return_value = 0
        results = runner.invoke(
            teflo, ['run', '-s', '../assets/common.yml', '-d', '/tmp']
        )
        assert results.exit_code == 0

    @staticmethod
    @mock.patch.object(Teflo, 'run')
    def test_valid_run_set_task(mock_method, runner):
        mock_method.return_value = 0
        results = runner.invoke(
            teflo, ['run', '-t', 'validate', '-s', '../assets/common.yml',
                     '-d', '/tmp']
        )
        assert results.exit_code == 0

    @staticmethod
    @mock.patch.object(yaml, 'safe_load')
    def test_invalid_run_malformed_input(mock_method, runner):
        mock_method.side_effect = yaml.YAMLError('error')
        results = runner.invoke(
            teflo, ['run', '-s', '../assets/descriptor.yml', '-d', '/tmp']
        )
        assert 'Error loading updated scenario data!' in results.output
        assert results.exit_code != 0

    @staticmethod
    @mock.patch.object(yaml, 'safe_load')
    def test_invalid_run_malformed_include(mock_method, runner):
        mock_method.side_effect = TefloError('Error loading updated included scenario data!')
        results = runner.invoke(
            teflo, ['run', '-s', '../assets/descriptor.yml']
        )
        assert 'Error loading updated included scenario data!' in results.output
        assert results.exit_code != 0

    @staticmethod
    def test_empty_include_section(runner):
        results = runner.invoke(teflo, ['run', '-s', '../assets/empty_include.yml'])
        assert 'Included File is invalid or Include section is empty.You have to provide valid scenario files ' \
               'to be included.' in results.output
        assert results.exit_code != 0

    @staticmethod
    def test_invalid_include_section(runner):
        results = runner.invoke(teflo, ['run', '-s', '../assets/wrong_include_descriptor.yml'])
        assert 'Included File is invalid or Include section is empty.You have to provide valid scenario files ' \
               'to be included.' in results.output
        assert results.exit_code != 0

    @staticmethod
    @mock.patch.object(Teflo, 'run')
    def test_valid_run_var_file(mock_method, runner):
        mock_method.return_value = 0
        results = runner.invoke(
            teflo, ['run', '-t', 'validate', '-s', '../assets/single_template.yml',
                     '-d', '/tmp', '--vars-data', '../assets/vars_data.yml']
        )
        assert results.exit_code == 0
        assert 'unit_test' in results.output

    @staticmethod
    @mock.patch.object(Teflo, 'run')
    def test_valid_run_var_raw_json(mock_method, runner):
        mock_method.return_value = 0
        results = runner.invoke(
            teflo, ['run', '-t', 'validate', '-s', '../assets/single_template.yml',
                     '-d', '/tmp', '--vars-data', json.dumps(dict(asset_name='unit_test'))]
        )
        assert results.exit_code == 0
        assert 'unit_test' in results.output

    @staticmethod
    def test_run_mutually_exclusive_label_skiplabel_option(runner):
        """ this tests if cli exits in case both labels and skip labels are present during teflo run"""
        results = runner.invoke(teflo, ['run', '-s', '../assets/common.yml', '-l', 'label1', '-sl', 'label2'])
        assert 'Labels and skip_labels are mutually exclusive. Only one of them can be used' in results.output

    @staticmethod
    def test_validate_mutually_exclusive_label_skiplabel_option(runner):
        """ this tests if cli exits in case both labels and skip labels are present during teflo validate"""
        results = runner.invoke(teflo, ['validate', '-s', '../assets/common.yml', '-l', 'label1', '-sl', 'label2'])
        assert 'Labels and skip_labels are mutually exclusive. Only one of them can be used' in results.output

    @staticmethod
    @mock.patch.object(Teflo, 'run')
    def test_run_label_option(mock_method, runner):
        """This is for testing use of label option with teflo run"""
        mock_method.return_value = 0
        results = runner.invoke(
            teflo, ['run', '-s', '../assets/descriptor.yml', '-t', 'validate', '-l', 'label1', '-d', '/tmp']
        )
        assert results.exit_code == 1
        assert isinstance(results.exception, TefloError)
        assert 'No resources were found corresponding to' in results.exception.message

    @staticmethod
    @mock.patch.object(Teflo, 'run')
    def test_run_skiplabel_option(mock_method, runner):
        """This is for testing use of skip_label option with teflo run"""
        mock_method.return_value = 0
        results = runner.invoke(
            teflo, ['run', '-s', '../assets/descriptor.yml', '-t', 'validate', '-sl', 'label1', '-d', '/tmp']
        )
        assert results.exit_code == 1
        assert isinstance(results.exception, TefloError)
        assert 'No resources were found corresponding to' in results.exception.message

    @staticmethod
    @mock.patch.object(Teflo, 'run')
    def test_run_skip_notify(mock_method, runner):
        """This is for testing use of skip_label option with teflo validate"""
        mock_method.return_value = 0
        results = runner.invoke(
            teflo, ['run', '-s', '../assets/descriptor.yml', '-d', '/tmp', '-sn', 'test_note_02']
        )
        assert results.exit_code == 0

    @staticmethod
    @mock.patch.object(Teflo, 'run')
    def test_run_no_notify(mock_method, runner):
        """This is for testing use of skip_label option with teflo validate"""
        mock_method.return_value = 0
        results = runner.invoke(
            teflo, ['run', '-s', '../assets/descriptor.yml', '-d', '/tmp', '-nn']
        )
        assert results.exit_code == 0


    @staticmethod
    @mock.patch.object(Teflo, 'run')
    def test_validate_label_option(mock_method, runner):
        """This is for testing use of label option with teflo validate"""
        mock_method.return_value = 0
        results = runner.invoke(
            teflo, ['validate', '-s', '../assets/descriptor.yml', '-l', 'label1', '-d', '/tmp']
        )
        assert results.exit_code == 1
        assert isinstance(results.exception, TefloError)
        assert 'No resources were found corresponding to' in results.exception.message

    @staticmethod
    @mock.patch.object(Teflo, 'run')
    def test_validate_skiplabel_option(mock_method, runner):
        """This is for testing use of skip_label option with teflo validate"""
        mock_method.return_value = 0
        results = runner.invoke(
            teflo, ['validate', '-s', '../assets/descriptor.yml', '-sl', 'label1', '-d', '/tmp']
        )
        assert results.exit_code == 1
        assert isinstance(results.exception, TefloError)
        assert 'No resources were found corresponding to' in results.exception.message

    @staticmethod

    def test_invalid_show(runner):
        results = runner.invoke(teflo, ['show', '-s', 'cdf.yml'])
        assert 'You have to provide a valid scenario file.' in results.output

    @staticmethod
    def test_valid_show(runner):
        results = runner.invoke(
            teflo, ['show', '-s', '../assets/no_include.yml']
        )
        assert "An option needs to be given. See help" in results.output

    @staticmethod
    @mock.patch.object(Teflo, 'list_labels')
    def test_valid_show_list_labels(mock_method, runner):
        """This test when --list-labels option is used correct method is called"""
        results = runner.invoke(
            teflo, ['show', '-s', '../assets/no_include.yml', '--list-labels']
        )
        assert mock_method.called

    @staticmethod
    @mock.patch.object(Teflo, 'notify')
    def test_notify(mock_method, runner):
        """This is for testing use of skip_label option with teflo validate"""
        mock_method.return_value = 0
        results = runner.invoke(
            teflo, ['notify', '-s', '../assets/descriptor.yml', '-d', '/tmp']
        )
        assert results.exit_code == 0

    @staticmethod
    @mock.patch.object(Teflo, 'notify')
    def test_notify_no_notify(mock_method, runner):
        """This is for testing use of skip_label option with teflo validate"""
        mock_method.return_value = 0
        results = runner.invoke(
            teflo, ['notify', '-s', '../assets/descriptor.yml', '-d', '/tmp', '-nn']
        )
        assert results.exit_code == 0

    @staticmethod
    @mock.patch.object(Teflo, 'notify')
    def test_notify_skip_notify(mock_method, runner):
        """This is for testing use of skip_label option with teflo validate"""
        mock_method.return_value = 0
        results = runner.invoke(
            teflo, ['notify', '-s', '../assets/descriptor.yml', '-d', '/tmp', '-sn', 'test_note_02']
        )
        assert results.exit_code == 0
