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
    tests.test_action_orchestrator

    Unit tests for testing teflo task orchestrator class.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import pytest
import mock
from teflo.orchestrators.action_orchestrator import ActionOrchestrator
from teflo.core import OrchestratorPlugin
from teflo.exceptions import TefloOrchestratorError


@pytest.fixture(scope='class')
def plugin():
    pg = mock.MagicMock(spec=OrchestratorPlugin, __plugin_name__='ansible')
    pg.action_name = 'action1'
    pg.run = mock.MagicMock(return_value=0)
    pg.validate = mock.MagicMock(return_value=[])
    return pg


@pytest.fixture
def action_orchestrator(action_resource):
    action_orchestrator = ActionOrchestrator(action_resource)
    return action_orchestrator


class TestActionOrchestrator(object):

    @staticmethod
    def test_task_orchestrator_constructor(action_orchestrator):
        assert isinstance(action_orchestrator, ActionOrchestrator)

    @staticmethod
    def test_task_orchestrator_validate(plugin, action_orchestrator):
        action_orchestrator.plugin = plugin
        action_orchestrator.validate()
        plugin.validate.assert_called()

    @staticmethod
    def test_task_orchestrator_run(plugin, action_orchestrator):
        action_orchestrator.plugin = plugin
        action_orchestrator.run()
        plugin.run.assert_called()

    @staticmethod
    def test_task_orchestrator_run_failure(plugin, action_orchestrator):
        plugin.run.return_value = 1
        action_orchestrator.plugin = plugin
        with pytest.raises(TefloOrchestratorError) as ex:
            action_orchestrator.run()
        assert "Orchestration failed : Failed to perform  action1" in ex.value.args[0]




