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
    Pykwalify extensions module for ansible executor plugin

    Module containing custom validation functions used for ansible executor schema checking.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""


def valid_execute_types(value, rule_obj, path):
    """ Verify if only one execute type is set for a execute task"""
    match = list()

    types = ['script', 'playbook', 'shell']

    for item in types:
        if item in value.keys() and value[item]:
            match.append(item)

    if match.__len__() > 1:
        raise AssertionError(
            'Only one execute type can be set for executor ~ %s.\n'
            'Available types: %s\n'
            'Set types: %s' % (value['executor'], types, match)
        )
    return True


def type_int_list(value, rule_obj, path):
    """Verfiy a key's value is either a int or list."""
    if not isinstance(value, (int, list)):
        raise AssertionError(
            '%s must be either a integer or list of integers.' % path.split('/')[-1]
        )
    if isinstance(value, list):
        for x in value:
            if not isinstance(x, int):
                raise AssertionError(
                    '%s must be either a integer or list of integers.' % path.split('/')[-1]
                )
    return True
