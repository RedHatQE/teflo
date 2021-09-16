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
    teflo.exceptions

    Module containing all custom exceptions used by teflo.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from termcolor import colored


class TefloError(Exception):
    """Teflo's base Exception class"""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(TefloError, self).__init__(colored(message, "red"))
        self.message = colored(message, "red")


class TefloTaskError(TefloError):
    """Teflo's task base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(TefloTaskError, self).__init__(message)


class TefloScenarioFailure(TefloError):
    """Teflo's scenario failure Error."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(TefloScenarioFailure, self).__init__(message)


class TefloResourceError(TefloError):
    """Teflo's resource base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(TefloResourceError, self).__init__(message)


class AnsibleVaultError(TefloError):
    """Teflo's AnsibleVaultError exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(AnsibleVaultError, self).__init__(message)


class TefloProvisionerError(TefloError):
    """Teflo's provisioner base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(TefloProvisionerError, self).__init__(message)


class TefloProviderError(TefloError):
    """Teflo's provider base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(TefloProviderError, self).__init__(message)


class TefloOrchestratorError(TefloError):
    """Teflo's orchestrator base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(TefloOrchestratorError, self).__init__(message)


class HelpersError(Exception):
    """Base class for teflo helpers exceptions."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(HelpersError, self).__init__(colored(message, "red"))


class LoggerMixinError(TefloError):
    """Teflo's logger mixin base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(LoggerMixinError, self).__init__(message)


class TefloActionError(TefloResourceError):
    """Action's base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(TefloActionError, self).__init__(message)


class TefloExecuteError(TefloResourceError):
    """Execute's base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(TefloExecuteError, self).__init__(message)


class TefloHostError(TefloResourceError):
    """Asset's base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(TefloHostError, self).__init__(message)


class TefloReportError(TefloResourceError):
    """Report base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(TefloReportError, self).__init__(message)


class ScenarioError(TefloResourceError):
    """Scenario's base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(ScenarioError, self).__init__(message)


class BeakerProvisionerError(TefloProvisionerError):
    """Base class for Beaker provisioner exceptions."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(BeakerProvisionerError, self).__init__(message)


class OpenshiftProvisionerError(TefloProvisionerError):
    """Base class for openshift provisioner exceptions."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(OpenshiftProvisionerError, self).__init__(message)


class OpenstackProviderError(TefloProviderError):
    """Base class for openstack provider exceptions."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(OpenstackProviderError, self).__init__(message)


class ArchiveArtifactsError(TefloError):
    """Base class for when you always want to archive artifacts (pass|fail)."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(ArchiveArtifactsError, self).__init__(message)


class AnsibleServiceError(TefloError):
    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(AnsibleServiceError, self).__init__(message)


class TefloImporterError(TefloError):
    """Base class for the artifact importer exceptions."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(TefloImporterError, self).__init__(message)


class PolarionImporterError(TefloImporterError):
    """Base class for the Polarion importer exceptions."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(PolarionImporterError, self).__init__(message)


class ReportPortalImporterError(TefloImporterError):
    """Base class for the Report Portal importer exceptions."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(ReportPortalImporterError, self).__init__(message)


class TefloNotifierError(TefloResourceError):
    """Notifier's base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: error message
        :type message: str
        """
        super(TefloNotifierError, self).__init__(message)
