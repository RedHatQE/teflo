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
    tests.test_config_class

    Unit tests for testing teflo config class.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import copy
import os

import pytest

from teflo.utils.config import Config


@pytest.fixture(scope='class')
def config():
    return Config()


class TestConfig(object):
    @staticmethod
    def test_del_parser(config):
        with pytest.raises(AttributeError):
            dummy_config = copy.copy(config)
            dummy_config.__del_parser__()
            print(dummy_config.parser)

    @staticmethod
    def test_load_missing_config(config):
        config.load()

    @staticmethod
    def test_load_config_by_env_var(config):
        os.environ['TEFLO_SETTINGS'] = '../assets/teflo.cfg'
        config.load()
