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
    tests.test_asset_provisioner

    Unit tests for testing teflo asset provisioner class.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import mock
import pytest

from teflo.resources import Asset
from teflo.core import ProvisionerPlugin
from teflo.provisioners import AssetProvisioner


@pytest.fixture(scope='class')
def default_host_params():
    params = dict(description='description',
                  provider=dict(name='openstack',
                                credential='openstack'
                                ))
    return params

@pytest.fixture(scope='class')
def default_no_provider_host_params():
    params = dict(description='description',
                  provisioner='openstack-libcloud')
    return params


@pytest.fixture(scope='class')
def default_profile_params():
    params = dict(data_folder='/tmp/.results',
                  workspace='/tmp',
                  provider=dict(name='openstack',
                                credential='openstack'
                                ),
                  name='dummy',
                  ip_address='',
                  )
    return params

@pytest.fixture(scope='class')
def default_no_provider_profile_params():
    params = dict(data_folder='/tmp/.results',
                  workspace='/tmp',
                  name='dummy',
                  ip_address='',
                  )
    return params


@pytest.fixture(scope='class')
def plugin():
    pg = mock.MagicMock(spec=ProvisionerPlugin,
                        __plugin_name__='openstack-libcloud')
    pg.create = mock.MagicMock(return_value=[])
    pg.delete = mock.MagicMock(return_value=[])
    pg.validate = mock.MagicMock(return_value=[])
    return pg


@pytest.fixture(scope='class')
def host(plugin, default_host_params):
    host = mock.MagicMock(spec=Asset, name='Test-Asset', provider_params=dict(param1='value1'),
                          provider_credentials=dict(token='token'))
    plugin.asset = host
    plugin.provider_params = host.provider_params
    plugin.provider_credentials = host.provider_credentials
    host.provisioner = plugin
    return host


@pytest.fixture(scope='class')
def host_provisioner(host):
    hp = AssetProvisioner(host)
    return hp


class TestAssetProvisioner(object):

    @staticmethod
    def test_asset_provisioner_constructor(host_provisioner):
        assert isinstance(host_provisioner, AssetProvisioner)

    @staticmethod
    def test_asset_provisioner_create(plugin, host_provisioner):
        host_provisioner.plugin = plugin
        host_provisioner.create()
        plugin.create.assert_called()

    @staticmethod
    @mock.patch('copy.deepcopy')
    def test_asset_provisioner_create_multi_resources(mock_copy, plugin, host_provisioner, default_profile_params):
        mock_copy.return_value = default_profile_params
        res1=dict(tx_id=1, name='dummy_0', ip='2.4.6.8', asset_id='222')
        res2=dict(tx_id=1, name='dummy_1', ip='1.3.5.7', asset_id='223')
        plugin.create = mock.MagicMock(return_value=[res1, res2])
        host_provisioner.plugin = plugin
        host_provisioner.create()
        plugin.create.assert_called()

    @staticmethod
    @mock.patch('copy.deepcopy')
    def test_asset_provisioner_create_multi_resources_no_provider(mock_copy, plugin, host_provisioner,
                                                                  default_no_provider_profile_params):
        mock_copy.return_value = default_no_provider_profile_params
        res1=dict(tx_id=1, name='dummy_0', ip='2.4.6.8', asset_id='222')
        res2=dict(tx_id=1, name='dummy_1', ip='1.3.5.7', asset_id='223')
        plugin.create = mock.MagicMock(return_value=[res1, res2])
        host_provisioner.plugin = plugin
        host_provisioner.create()
        plugin.create.assert_called()

    @staticmethod
    @mock.patch('copy.deepcopy')
    def test_asset_provisioner_create_single_resource(mock_copy, plugin, host_provisioner, default_profile_params):
        mock_copy.return_value = default_profile_params
        res1=dict(tx_id=1, hostname='dummy_0', ip='2.4.6.8', asset_id='222')
        plugin.create = mock.MagicMock(return_value=[res1])
        host_provisioner.plugin = plugin
        host_provisioner.create()
        plugin.create.assert_called()

    @staticmethod
    @mock.patch('copy.deepcopy')
    def test_asset_provisioner_create_single_resource_no_provider(mock_copy, plugin, host_provisioner,
                                                                  default_no_provider_profile_params):
        mock_copy.return_value = default_no_provider_profile_params
        res1=dict(tx_id=1, hostname='dummy_0', ip='2.4.6.8', asset_id='222')
        plugin.create = mock.MagicMock(return_value=[res1])
        host_provisioner.plugin = plugin
        host_provisioner.create()
        plugin.create.assert_called()

    @staticmethod
    def test_asset_provisioner_delete(plugin, host_provisioner):
        host_provisioner.plugin = plugin
        host_provisioner.delete()
        plugin.delete.assert_called()

    @staticmethod
    def test_asset_provisioner_validate(plugin, host_provisioner):
        host_provisioner.plugin = plugin
        host_provisioner.validate()
        plugin.validate.assert_called()

    @staticmethod
    @mock.patch.object(AssetProvisioner, 'logger')
    def test_asset_provisioner_print_common_attributes(mock_logger, plugin, host_provisioner):
        mock_logger.debug = mock.MagicMock()
        host_provisioner.print_commonly_used_attributes()
        mock_logger.debug.assert_called()

    @staticmethod
    def test_asset_provisioner_create_exception(plugin, host_provisioner):
        plugin.create.side_effect = Exception('Mock Create Failure')
        with pytest.raises(Exception):
            host_provisioner.create()

    @staticmethod
    def test_asset_provisioner_delete_exception(plugin, host_provisioner):
        plugin.delete.side_effect = Exception('Mock Delete Failure')
        with pytest.raises(Exception):
            host_provisioner.delete()
