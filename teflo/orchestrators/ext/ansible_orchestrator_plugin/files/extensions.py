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
    Pykwalify extensions module for ansible orchestrator plugin

    Module containing custom validation functions used for ansible orchestrator schema checking.

    :copyright: (c) 2021 Red Hat, Inc.
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
            'Only one action type can be set for orchestrator\n'
            'Available action types: %s\n'
            'Set types: %s' % (types, match)
        )
    elif match.__len__() == 0:
        raise AssertionError(
            'At lease one action type should be set for orchestrator \n'
            'Available action types: %s\n' % types
        )
    return True


def valid_ansible_script_type(value, rule_obj, path):

    """ Verify if ansible_script has appropriate keys from the given list
    """
    extra_args = ['name', 'creates', 'decrypt', 'executable', 'removes', 'warn', 'stdin', 'stdin_add_newline']
    if False in [key in extra_args and isinstance(val, str) for key, val in value.items()]:
        raise AssertionError('ansible_script dictionary is using a key not present in this list %s' % extra_args)
    else:
        return True
