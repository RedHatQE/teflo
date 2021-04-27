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
    teflo._compat

    This is a compatibility module that assists on keeping the Teflo
    Framework compatible with python 2.x and python 3.x.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import sys
import ansible

_ver = sys.version_info

ansible_ver = int(ansible.__version__.split('.')[:2][1])
# Python 2.x?
is_py2 = (_ver[0] == 2)

# Python 3.x?
is_py3 = (_ver[0] == 3)

# Windows
is_win = sys.platform.startswith('win')

try:
    import simplejson as json
except (ImportError, SyntaxError):
    # simplejson does not support Python 3.2, it throws a SyntaxError
    # because of u'...' Unicode literals.
    import json

try:
    import builtins
except ImportError:
    import __builtin__ as builtins

try:
    from ConfigParser import RawConfigParser
except ImportError:
    from configparser import RawConfigParser

try:
    string_types = (str, unicode)
except NameError:
    string_types = (str, )

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

try:
    from ConfigParser import ConfigParser
except Exception:
    from configparser import ConfigParser

try:
    from ansible.parsing.vault import VaultLib
except ImportError:
    from ansible.utils.vault import VaultLib
