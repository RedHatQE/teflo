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

from ..core import LoggerMixin, TimeMixin
from ..exceptions import TefloImporterError
from ..helpers import find_artifacts_on_disk, DataInjector


class ArtifactImporter(LoggerMixin, TimeMixin):

    __importer_name__ = 'artifact-importer'

    def __init__(self, report):

        self.report = report
        self.artifact_paths = []
        self.plugin = getattr(self.report, 'importer_plugin')(report)

        # check if user specified data pass-through injection
        if self.report.executes:
            # report.executes exist then look for host_list
            host_list = [host for execute in self.report.executes for host in execute.all_hosts]
            self.injector = DataInjector(host_list)
        else:
            # Assume no executes is assigned, so the helper
            # method fetch_executes added an attribute 'all_hosts'
            # to the report object
            self.injector = DataInjector(self.report.all_hosts)

        self.report_name = self.injector.inject(self.report.name)

    def validate_artifacts(self):

        # Check report has any executes associated. If not, proceed
        # to walk the data directory on disk.
        art_paths = []
        self.logger.debug(self.report_name)
        if getattr(self.report, 'executes'):
            for execute in getattr(self.report, 'executes'):
                # check that the execute object collected artifacts
                if not execute.artifact_locations:
                    self.logger.warning('The specified execute, %s, does not have any artifacts '
                                        'with it.' % execute.name)
                    self.artifact_paths.extend(find_artifacts_on_disk
                                               (data_folder=self.report.config.get('RESULTS_FOLDER'),
                                                report_name=self.report_name))
                else:
                    self.artifact_paths.extend(find_artifacts_on_disk
                                               (data_folder=self.report.config.get('RESULTS_FOLDER'),
                                                report_name=self.report_name,
                                                art_location=self.injector.inject_list(execute.artifact_locations)
                                                )
                                               )
        else:
            self.artifact_paths.extend(find_artifacts_on_disk(data_folder=self.report.config.get('RESULTS_FOLDER'),
                                                              report_name=self.report_name))
        if not self.artifact_paths:
            raise TefloImporterError('No artifact could be found on the Teflo controller data folder.')

    def import_artifacts(self):
        self.plugin.artifacts = self.artifact_paths
        try:
            results = self.plugin.import_artifacts()
            if results:
                setattr(self.report, 'import_results', results)
        except Exception as ex:
            self.logger.error(ex)
            if getattr(self.plugin, 'import_results') == [None]:
                setattr(self.report, 'import_results', [])
            else:
                setattr(self.report, 'import_results', getattr(self.plugin, 'import_results'))
            raise TefloImporterError('Failed to import artifact %s' % self.report.name)

    def validate(self):
        """
        validate the params provided are supported by the plugin
        :return:
        """
        try:
            self.plugin.validate()
        except Exception:
            raise
        else:
            self.logger.info('successfully validated scenario Report against the schema!')
