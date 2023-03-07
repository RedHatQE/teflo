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
    tests.conftest

    Module containing hooks used by all tests.

    :copyright: (c) 2022 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from fixtures import action1
from fixtures import action2
from fixtures import action_resource
from fixtures import action_resource_cleanup
from fixtures import asset1
from fixtures import asset2
from fixtures import asset3
from fixtures import basic_scenario_graph_with_provision_only
from fixtures import config
from fixtures import default_host_params
from fixtures import default_note_params
from fixtures import execute1
from fixtures import execute2
from fixtures import execute3
from fixtures import execute_resource
from fixtures import host
from fixtures import master_child_scenario
from fixtures import notification_default_resource
from fixtures import notification_on_demand_resource
from fixtures import notification_on_failure_resource
from fixtures import notification_on_start_resource
from fixtures import notification_on_success_resource
from fixtures import report_resource
from fixtures import scenario
from fixtures import scenario1
from fixtures import scenario_graph
from fixtures import scenario_graph1
from fixtures import scenario_labels
from fixtures import scenario_resource
from fixtures import scenario_resource1
from fixtures import timeout_param_execute
from fixtures import timeout_param_orchestrate
from fixtures import timeout_param_provision
from fixtures import timeout_param_report

__all__ = [
    basic_scenario_graph_with_provision_only,
    action_resource,
    action_resource_cleanup,
    config,
    default_host_params,
    execute_resource,
    execute1,
    execute2,
    execute3,
    host,
    asset1,
    asset2,
    asset3,
    action1,
    action2,
    report_resource,
    scenario,
    scenario1,
    scenario_resource,
    scenario_resource1,
    scenario_labels,
    scenario_graph,
    master_child_scenario,
    notification_default_resource,
    notification_on_start_resource,
    notification_on_demand_resource,
    notification_on_success_resource,
    notification_on_failure_resource,
    default_note_params,
    timeout_param_provision,
    timeout_param_execute,
    timeout_param_report,
    timeout_param_orchestrate,
    scenario_graph1,
]
