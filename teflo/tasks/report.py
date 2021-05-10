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
    teflo.tasks.report

    Here you add brief description of what this module is about

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..core import TefloTask
from .._compat import string_types
from ..importers import ArtifactImporter


class ReportTask(TefloTask):
    """Report task."""
    __task_name__ = 'report'

    def __init__(self, msg, package, **kwargs):
        """Constructor.

        :param msg: task message
        :type msg: str
        :param kwargs: additional keyword arguments
        :type kwargs: dict
        """
        super(ReportTask, self).__init__(**kwargs)
        self.msg = msg
        self.do_import = True

        # create the artifact importer interface and supply the plugins to this interface
        self.importer = ArtifactImporter(package)

        if not package.do_import:
            self.do_import = False

    def run(self):
        """Run.

        This method is the main entry point to the task.
        """
        self.logger.debug(self.msg)

        try:
            # check if the artifacts are on disk.
            self.importer.validate_artifacts()
        except Exception as ex:
            self.logger.error('Failed to run report %s ' % self.name)
            stackmsg = self.get_formatted_traceback()
            self.logger.error(ex)
            self.logger.error(stackmsg)
            raise

        if self.do_import:
            try:
                # run the configuration with the given importer
                self.importer.import_artifacts()
            except Exception as ex:
                self.logger.error('Failed to run report %s ' % self.name)
                stackmsg = self.get_formatted_traceback()
                self.logger.error(ex)
                self.logger.error(stackmsg)
                raise
