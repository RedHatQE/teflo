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
    tests.test_misc

    Unit tests for testing misc code.

    :copyright: (c) 2022 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from teflo._compat import string_types
from teflo.static.playbooks import GIT_CLONE_PLAYBOOK
from teflo.static.playbooks import SYNCHRONIZE_PLAYBOOK


def test_import_synchronize_pb():
    assert isinstance(SYNCHRONIZE_PLAYBOOK, string_types)


def test_import_git_clone_pb():
    assert isinstance(GIT_CLONE_PLAYBOOK, string_types)
