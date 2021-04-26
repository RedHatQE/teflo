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
    tests.test_exceptions

    Unit tests for testing teflo custom exceptions.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import pytest

from teflo.exceptions import TefloError, TefloTaskError, \
    TefloResourceError, TefloProvisionerError, TefloProviderError, \
    TefloOrchestratorError, HelpersError, LoggerMixinError, \
    TefloActionError, TefloExecuteError, TefloHostError, TefloReportError, \
    ScenarioError, BeakerProvisionerError, OpenstackProviderError, \
    OpenshiftProvisionerError, ArchiveArtifactsError


def test_teflo_error():
    with pytest.raises(TefloError):
        raise TefloError('error message')


def test_teflo_task_error():
    with pytest.raises(TefloTaskError):
        raise TefloTaskError('error message')


def test_teflo_resource_error():
    with pytest.raises(TefloResourceError):
        raise TefloResourceError('error message')


def test_teflo_provisioner_error():
    with pytest.raises(TefloProvisionerError):
        raise TefloProvisionerError('error message')


def test_teflo_provider_error():
    with pytest.raises(TefloProviderError):
        raise TefloProviderError('error message')


def test_teflo_orchestrator_error():
    with pytest.raises(TefloOrchestratorError):
        raise TefloOrchestratorError('error message')


def test_teflo_helpers_error():
    with pytest.raises(HelpersError):
        raise HelpersError('error message')


def test_teflo_logger_mixin_error():
    with pytest.raises(LoggerMixinError):
        raise LoggerMixinError('error message')


def test_teflo_action_error():
    with pytest.raises(TefloActionError):
        raise TefloActionError('error message')


def test_teflo_execute_error():
    with pytest.raises(TefloExecuteError):
        raise TefloExecuteError('error message')


def test_teflo_host_error():
    with pytest.raises(TefloHostError):
        raise TefloHostError('error message')


def test_teflo_report_error():
    with pytest.raises(TefloReportError):
        raise TefloReportError('error message')


def test_scenario_error():
    with pytest.raises(ScenarioError):
        raise ScenarioError('error message')


def test_beaker_provisioner_error():
    with pytest.raises(BeakerProvisionerError):
        raise BeakerProvisionerError('error message')


def test_openstack_provider_error():
    with pytest.raises(OpenstackProviderError):
        raise OpenstackProviderError('error message')


def test_openshift_provisioner_error():
    with pytest.raises(OpenshiftProvisionerError):
        raise OpenshiftProvisionerError('error message')


def test_archive_artifacts_error():
    with pytest.raises(ArchiveArtifactsError):
        raise ArchiveArtifactsError('error message')
