# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Red Hat, Inc.
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
    Pykwalify extensions module for ansible orchestrator plugin

    Module containing custom validation functions used for ansible orchestrator schema checking.

    :copyright: (c) 2020 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""


def valid_action_types(value, rule_obj, path):
    """ Verify if only one action type is set for a orchestrate task"""
    match = list()

    types = ['ansible_script', 'ansible_playbook', 'ansible_shell']

    for item in types:
        if item in value.keys() and value[item]:
            match.append(item)

    if match.__len__() > 1:
        raise AssertionError(
            'Only one action type can be set for orchestrator ~ %s.\n'
            'Available types: %s\n'
            'Set types: %s' % (value['orchestrator'], types, match)
        )
    return True


def valid_ansible_script_type(value, rule_obj, path):

    """ Verify if ansible_script type is either a boolean or a dictionary
        and extra_args are from the given list and name key is required
    """
    extra_args = ['name', 'creates', 'decrypt', 'executable', 'removes', 'warn', 'stdin', 'stdin_add_newline']
    if isinstance(value, bool):
        return True
    elif isinstance(value, dict):
        if True in [keys in extra_args and isinstance(values, str) for keys, values in value.items()] \
                and value.get('name'):
            return True
        else:
            raise AssertionError('ansible_script is missing "name" key '
                                 'or is using a key not present in this list %s' % extra_args)
    else:
        return False
