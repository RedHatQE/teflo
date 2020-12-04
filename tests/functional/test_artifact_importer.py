# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Red Hat Inc.
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
    tests.test_artifact_importer

    Unit tests for testing teflo artifact importer class.

    :copyright: (c) 2020 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import mock
import pytest
import os

from teflo.resources import Report, Execute
from teflo.core import ImporterPlugin
from teflo.utils.config import Config
from teflo.importers import ArtifactImporter
from teflo.exceptions import TefloImporterError


@pytest.fixture(scope='class')
def artifact_locations():
    artifacts = {}
    artifacts['artifacts/host01'] = ['test.xml']
    artifacts['artifacts/host02'] = ['sample2.xml']

    return artifacts


@pytest.fixture(scope='class')
def report_config():
    config_file = '../assets/teflo.cfg'
    os.environ['TEFLO_SETTINGS'] = config_file
    config = Config()
    config.load()
    return config


@pytest.fixture(scope='class')
def execute(artifact_locations):
    e = mock.MagicMock(spec=Execute, name='pytest',
                       artifact_locations=artifact_locations)
    e.all_hosts = ['client_a']
    return e


@pytest.fixture(scope='class')
def default_report_params(execute):
    params = dict(description='description', executes=[execute],
                  provider=dict(name='polarion',
                                credential='polarion'
                                ))
    return params


@pytest.fixture(scope='class')
def default_profile_params():
    params = dict(data_folder='/tmp/.results',
                  workspace='/tmp',
                  provider_credentials = dict(polarion_url='https://test.com/polarion',
                                              username='testuser',
                                              password='testpassword'))
    return params


@pytest.fixture(scope='class')
def plugin():
    pg = mock.MagicMock(spec=ImporterPlugin,
                        __plugin_name__='polarion')
    pg.profile = dict(name='test.xml')
    pg.import_artifacts = mock.MagicMock(return_value='Import Success')
    return pg


@pytest.fixture(scope='class')
def report(default_report_params, plugin, report_config,
           default_profile_params, execute):
    report = mock.MagicMock(spec=Report, name='report',
                            config=report_config)

    report.name = 'test.xml'
    report.importer_plugin = plugin
    report.parameters = default_report_params
    report.do_import = True
    report.executes = [execute]
    report.profile.return_value = default_profile_params

    return report


@pytest.fixture(scope='class')
def artifact_importer(report):
    importer = ArtifactImporter(report)
    return importer


class TestArtifactImporter(object):

    @staticmethod
    def test_artifact_importer_constructor(artifact_importer):
        assert isinstance(artifact_importer, ArtifactImporter)

    @staticmethod
    @mock.patch('teflo.importers.artifact_importer.find_artifacts_on_disk')
    def test_artifact_importer_validate_no_artifact_location(mock_find_disks, artifact_importer,
                                                             plugin, artifact_locations, execute):

        locations = [os.path.join(dir, f)
                     for dir, files in artifact_locations.items()
                     for f in files]
        mock_find_disks.return_value = [os.path.join('/tmp', dir)
                                        for dir in locations]
        execute.artifact_locations = []
        artifact_importer.plugin = plugin
        artifact_importer.validate_artifacts()

    @staticmethod
    @mock.patch('teflo.importers.artifact_importer.find_artifacts_on_disk')
    def test_artifact_importer_validate_artifact_locations_artifact_on_disk(mock_find_disks, artifact_importer,
                                                                            plugin, artifact_locations, execute):

        locations = [os.path.join(dir, f)
                     for dir, files in artifact_locations.items()
                     for f in files]
        mock_find_disks.return_value = [os.path.join('/tmp', dir)
                                        for dir in locations]
        artifact_locations['artifacts/host01'] = ['test.xml']
        execute.artifact_locations = artifact_locations
        artifact_importer.plugin = plugin
        artifact_importer.validate_artifacts()

    @staticmethod
    @mock.patch('teflo.importers.artifact_importer.find_artifacts_on_disk')
    def test_artifact_importer_validate_no_execute_artifacts_on_disk(mock_find_disks, plugin, report,
                                                                     artifact_locations):

        locations = [os.path.join(dir, f)
                     for dir, files in artifact_locations.items()
                     for f in files]
        mock_find_disks.return_value = [os.path.join('/tmp', dir)
                                        for dir in locations]

        report.executes = []
        report.all_hosts = ['host_01', 'host_02']
        artifact_importer = ArtifactImporter(report=report)
        artifact_importer.plugin = plugin
        artifact_importer.validate_artifacts()


    @staticmethod
    @mock.patch('teflo.importers.artifact_importer.find_artifacts_on_disk')
    def test_artifact_importer_validate_no_artifact_on_disk(mock_find_disks, artifact_importer,
                                                            plugin, execute, report):

        execute.artifact_locations = []
        mock_find_disks.return_value = []
        report.name = 'test.xml'
        artifact_importer.artifact_paths = []
        with pytest.raises(TefloImporterError):
            artifact_importer.plugin = plugin
            artifact_importer.validate_artifacts()


    @staticmethod
    @mock.patch('teflo.importers.artifact_importer.find_artifacts_on_disk')
    def test_artifact_importer_import_artifacts(mock_find_disks, artifact_importer,
                                                plugin, artifact_locations, execute):

        locations = [os.path.join(dir, f)
                     for dir, files in artifact_locations.items()
                     for f in files]
        mock_find_disks.return_value = [os.path.join('/tmp', dir)
                                        for dir in locations]
        artifact_locations['artifacts/host01'] = ['test.xml']
        execute.artifact_locations = artifact_locations
        artifact_importer.plugin = plugin
        artifact_importer.import_artifacts()
        plugin.import_artifacts.assert_called()

    @staticmethod
    @mock.patch('teflo.importers.artifact_importer.find_artifacts_on_disk')
    def test_artifact_importer_import_artifacts_failure(mock_find_disks, artifact_importer,
                                                        plugin, artifact_locations):

        locations = [os.path.join(dir, f)
                     for dir, files in artifact_locations.items()
                     for f in files]
        mock_find_disks.return_value = [os.path.join('/tmp', dir)
                                        for dir in locations]
        plugin.import_artifacts.side_effect = TefloImporterError('Test Failure')
        plugin.import_results = dict(import_result='Test Failure')
        artifact_importer.plugin = plugin
        with pytest.raises(TefloImporterError):
            artifact_importer.import_artifacts()
            plugin.import_artifacts.assert_called()
