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
    tests.test_ansible_vault

    Unit tests for testing teflo asset provisioner class.

    :copyright: (c) 2022 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import mock
import pytest
import os
from teflo._compat import ConfigParser
from teflo.utils.config import Config

@pytest.fixture(scope='class')
def test_vault_config():
    config_file = '../assets/testvault.cfg'
    config = Config()
    os.environ['TEFLO_SETTINGS'] = config_file
    config.load()
    return config

@pytest.fixture
def creds_expected():
    return [{'hub_url': 'null', 'keytab': 'null', 'keytab_principal': 'null', 'name': 'beaker'}]

class TestAnsibleVault(object):

    @staticmethod
    def test_ansible_vault_from_cfg(test_vault_config, creds_expected):
        assert test_vault_config.get("CREDENTIALS") == creds_expected