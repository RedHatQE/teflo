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
    Pykwalify extensions module.

    Module containing custom validation functions used for schema checking.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from teflo.constants import PROVISIONERS
from teflo.helpers import get_executor_plugin_class, get_executors_plugin_list, get_orchestrators_plugin_list


def type_str_list(value, rule_obj, path):
    """Verify a key's value is either a string or list."""
    if not isinstance(value, (str, list)):
        raise AssertionError(
            '%s must be either a string or list.' % path.split('/')[-1]
        )
    return True


def valid_orchestrator(value, rule_obj, path):
    """Verify the given orchestrator is a valid selection by teflo."""

    orchestrators = get_orchestrators_plugin_list()
    if value.lower() not in orchestrators:
        raise AssertionError(
            'Orchestrator %s is invalid.\n'
            'Available orchestrators %s' % (value, orchestrators)
        )
    return True


def valid_executor(value, rule_obj, path):
    """Verify the given executor is a valid selection by teflo."""
    executors = get_executors_plugin_list()
    if value.lower() not in executors:
        raise AssertionError(
            'Executor %s is invalid.\n'
            'Available executors %s' % (value, executors)
        )
    return True


def valid_asset_provider_params(value, rule_obj, path):
    """ Verify that the specified provider has a provisioner mapped to it."""
    provisioner = value['provisioner']
    provider = value['provider']
    if provider['name'] in PROVISIONERS:
        if provisioner:
            for plugins in PROVISIONERS[provider]:
                if isinstance(plugins, list):
                    for plugin in plugins:
                        if plugin != provisioner:
                            continue
                        else:
                            plugin.validate(provider)
                            break
                else:
                    plugins.validate(provider)
        else:
            for plugins in PROVISIONERS[provider]:
                if isinstance(plugins, list):
                    for plugin in plugins:
                        if plugin.startswith(provider['name']):
                            plugin.validate(provider)
                            break
                else:
                    plugins.validate(provider)
    return True
