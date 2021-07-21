# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Red Hat Inc.
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
    tests.test_execute_manager

    Unit tests for testing teflo task orchestrator class.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import pytest
import mock
from teflo.orchestrators.action_orchestrator import ActionOrchestrator

from teflo.executors.execute_manager import ExecuteManager
from teflo.core import ExecutorPlugin
from teflo.exceptions import TefloExecuteError

from teflo.core import OrchestratorPlugin
from teflo.exceptions import TefloOrchestratorError


@pytest.fixture(scope='class')
def plugin():
    pg = mock.MagicMock(spec=ExecutorPlugin, __plugin_name__='runner')
    pg.execute_name = 'execute1'
    pg.run = mock.MagicMock(return_value=0)
    pg.validate = mock.MagicMock(return_value=[])
    return pg


@pytest.fixture
def execute_manager(execute_resource):
    execute_manager = ExecuteManager(execute_resource)
    return execute_manager


class TestExecuteManager(object):

    @staticmethod
    def test_task_executor_constructor(execute_manager):
        assert isinstance(execute_manager, ExecuteManager)

    @staticmethod
    def test_task_executor_validate(plugin, execute_manager):
        execute_manager.plugin = plugin
        execute_manager.validate()
        plugin.validate.assert_called()

    @staticmethod
    def test_task_executor_run(plugin, execute_manager):
        execute_manager.plugin = plugin
        execute_manager.run()
        plugin.run.assert_called()

    @staticmethod
    def test_task_executor_run_failure(plugin, execute_manager):
        plugin.run.return_value = 1
        execute_manager.plugin = plugin
        with pytest.raises(TefloExecuteError) as ex:
            execute_manager.run()
        assert "Execute stage failed : Failed to perform execute1" in ex.value.args[0]




