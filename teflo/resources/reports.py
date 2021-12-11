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
    teflo.resources.actions

    Module used for building teflo report compounds. A report's main goal is
    to handle reporting results to external resources.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import sys
from collections import OrderedDict
from ..core import TefloResource
from ..tasks import ReportTask, ValidateTask
from ..exceptions import TefloReportError
from ..importers import ArtifactImporter
from ..helpers import get_importer_plugin_class, get_importers_plugin_list
from .._compat import string_types


class Report(TefloResource):
    """
    The report resource class.
    """

    _valid_tasks_types = ['validate', 'report']
    _fields = ['name', 'description', 'importer', 'executes',
                    'import_results', 'labels', 'report_timeout', "validate_timeout"]

    def __init__(self,
                 config=None,
                 name=None,
                 importer=None,
                 parameters={},
                 validate_task_cls=ValidateTask,
                 report_task_cls=ReportTask,
                 **kwargs):
        """Constructor.

        :param config: teflo configuration
        :type config: dict
        :param name: report resource name
        :type name: str
        :param parameters: content which makes up the report resource
        :type parameters: dict
        :param validate_task_cls: teflos validate task class
        :type validate_task_cls: object
        :param report_task_cls: teflos report task class
        :type report_task_cls: object
        :param kwargs: additional key:value(s)
        :type kwargs: dict
        """
        super(Report, self).__init__(config=config, name=name, **kwargs)

        # set the timeout for VALIDATE
        try:
            if parameters.get('validate_timeout') is not None:
                self._validate_timeout = parameters.pop("validate_timeout")
            else:
                self._validate_timeout = config["TIMEOUT"]["VALIDATE"]
        except TypeError:
            self.logger.error("No teflo.cfg found,  so no timeout will be set")
            self._validate_timeout = 0

        # set the timeout for report
        try:
            if parameters.get('report_timeout') is not None:
                self._report_timeout = parameters.pop("report_timeout")
            else:
                self._report_timeout = config["TIMEOUT"]["REPORT"]
        except TypeError:
            self.logger.error("No teflo.cfg found,  so no timeout will be set")
            self._report_timeout = 0

        # set the report resource name
        if name is None:
            self._name = parameters.pop('name', None)
            if self._name is None:
                raise TefloReportError('Unable to build report object. Name'
                                        ' field missing!')
        else:
            self._name = name

        # set the report description
        self._description = parameters.pop('description', None)

        # set the execute that collected the artifacts
        self._executes = parameters.pop('executes', [])

        # convert the executes into list format if executes defined as str format
        if self._executes is not None and isinstance(self._executes, string_types):
            self._executes = [val.strip() for val in self._executes.split(',')]

        importer_name = parameters.pop('importer', importer)

        parameters = self.__set_provider_attr__(parameters)

        # Finally check and load external plugin implementation
        # if provider key was provided and importer_name was not provided , provider_name is used as importer name and
        # external importer plugins are searched used this name
        # if provider is not used importer name is must
        if importer_name is None:
            if self.has_provider:
                importer_name = self.provider
            else:
                raise TefloReportError('Importer or Provider name has to be provided')

        found_name = False
        for name in get_importers_plugin_list():
            if name.startswith(importer_name):
                found_name = True
        if found_name:
            self._importer_plugin = get_importer_plugin_class(importer_name)
            self.do_import = True
        else:
            self.logger.error('Importer %s for report artifacts %s is invalid.'
                              % (importer_name, self.name))
            sys.exit(1)

        self._import_results = parameters.pop('import_results', [])

        # set labels
        setattr(self, 'labels', parameters.pop('labels', []))

        # set the teflo task classes for the resource
        self._validate_task_cls = validate_task_cls
        self._report_task_cls = report_task_cls

        # reload construct task methods
        self.reload_tasks()

        # load the parameters into the object itself
        if parameters:
            self.load(parameters)

    def __set_provider_attr__(self, parameters):
        """Configure the report provider attributes.

        :param parameters: content which makes up the report resource
        :type parameters: dict
        :return: updated parameters
        :rtype: dict"""

        # this is for backward compatibility, in case the provider key is used in the SDF
        self._provider = {}
        if parameters.get('provider', False):
            creds = parameters.get('provider').pop('credential', None)
            for p, v in parameters.pop('provider').items():
                if p == 'name':
                    self._provider = v
                    continue
                setattr(self, p, v)
            self.has_provider = True
        else:
            # set no provider object
            creds = parameters.pop('credential', None)
            for p, v in parameters.items():
                setattr(self, p, v)
            del self.provider
            self.has_provider = False

        # lets set the credentials if any
        if creds:
            for item in self.config['CREDENTIALS']:
                if item['name'] == creds:
                    self._credential = item
                    break
        return parameters

    def validate(self):
        """Validate the report."""
        getattr(ArtifactImporter(self), 'validate')()

    @property
    def importer_plugin(self):
        """Importer plugin property.

        :return: importer plugin class
        :rtype: object
        """
        return self._importer_plugin

    @importer_plugin.setter
    def importer_plugin(self, value):
        """Set importer plugin property."""
        raise AttributeError('You cannot set the report importer plugin after report '
                             'class is instantiated.')

    @property
    def importer_plugin_name(self):
        """Importer plugin name property.

        :return: importer plugin name
        :rtype: object
        """
        return self._importer_plugin.__plugin_name__

    @importer_plugin_name.setter
    def importer_plugin_name(self, value):
        """Set importer plugin name property."""
        raise AttributeError('You cannot set the importer plugin name after report '
                             'class is instantiated.')

    @property
    def provider(self):
        """Provider property.

        :return: provider class
        :rtype: object
        """
        return self._provider

    @provider.setter
    def provider(self, value):
        """Set provider property."""
        raise AttributeError('You cannot set the report provider after report '
                             'class is instantiated.')

    @provider.deleter
    def provider(self):
        """delete Provider property.

        :return: provider class
        :rtype: string
        """
        del self._provider

    @property
    def executes(self):
        """Execute resource property.

        :return: execute class
        :rtype: object
        """
        return self._executes

    @executes.setter
    def executes(self, value):
        """Set execute object property."""
        self._executes = value

    @property
    def import_results(self):
        """import_results resource property.

        :return: import results
        :rtype: list
        """
        return self._import_results

    @import_results.setter
    def import_results(self, value):
        """Set the import_results property."""
        self._import_results = value

    @property
    def credential(self):
        """Report credential property.

        :return: credential
        :rtype: dict
        """
        return self._credential

    @credential.setter
    def credential(self, value):
        """Set credential property."""
        raise AttributeError('You cannot set the report credential after report '
                             'class is instantiated.')

    @credential.deleter
    def credential(self):
        """
        delete the credential property
        :return:
        """
        del self._credential

    def profile(self):
        """Builds a profile for the report resource.

        :return: the report profile
        :rtype: OrderedDict
        """
        filtered_attr = {k: v for k, v in vars(self).items() if not k.startswith('_') and k not in
                         ['do_import', 'has_provider', 'all_hosts']}
        profile = OrderedDict()
        profile['name'] = self.name
        profile['description'] = self.description
        if not isinstance(self.importer_plugin, string_types):
            profile['importer'] = getattr(
                           self.importer_plugin, '__plugin_name__')
        else:
            profile['importer'] = self.importer_plugin
        if hasattr(self, 'provider') and len(getattr(self, 'provider', {})) != 0:
            profile.update(OrderedDict(provider={}))
            profile.get('provider').update(name=self.provider)
            profile.get('provider').update(credential=self.credential.get('name'))
            profile.get('provider').update(filtered_attr)
        else:
            profile.update(credential=self.credential.get('name'))
            profile.update(filtered_attr)

        # set the labels for report resource
        profile['labels'] = self.labels

        # set the report's executes
        if all(isinstance(item, string_types) for item in self.executes):
            profile.update(executes=[execute for execute in self.executes])
        else:
            profile.update(dict(executes=[execute.name for execute in self.executes]))

        # set the report's import results
        profile.update({'import_results': self.import_results})

        return profile

    def _construct_validate_task(self):
        """Constructs the validate task associated to the report resource.

        :return: validate task definition
        :rtype: dict
        """
        task = {
            'task': self._validate_task_cls,
            'name': str(self.name),
            'resource': self,
            'methods': self._req_tasks_methods,
            "timeout": self._validate_timeout
        }
        return task

    def _construct_report_task(self):
        """Constructs the report task associated to the report resource.

        :return: report task definition
        :rtype: dict
        """
        task = {
            'task': self._report_task_cls,
            'name': str(self.name),
            'package': self,
            'msg': '   reporting %s' % self.name,
            'methods': self._req_tasks_methods,
            "timeout": self._report_timeout
        }
        return task
