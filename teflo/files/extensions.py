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
    Pykwalify extensions module.

    Module containing custom validation functions used for schema checking.

    :copyright: (c) 2022 Red Hat, Inc.
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


def check_provider_present(value, rule_obj, path):
    if value.get('provider'):
        raise AssertionError(
            'Provider key is no longer supported  %s. '
            'Visit https://teflo.readthedocs.io/en/latest/users/definitions/provision.html#provision to see examples '
            'for provisioning assets' % value.get('provider')
        )
    if not value.get('provisioner') and not value.get("ip_address"):
        raise AssertionError(
            'If provisioner is not provided, an ip_address is needed for considering the asset as static'
        )
    return True
