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
    teflo.provisioners.host_provisioner

    Base provisioner module to be used as an interface for implementing any
    new provisioners within teflo.

    :copyright: (c) 2020 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from pprint import pformat

from teflo.core import LoggerMixin, TimeMixin
from teflo.helpers import mask_credentials_password
import copy
import json


class AssetProvisioner(LoggerMixin, TimeMixin):
    """AssetProvisioner provisioner class.

    This class is the generic iterface that provision and
    cleanup tasks

    """
    __provisioner_name__ = 'asset-provisioner'

    def __init__(self, asset):
        """Constructor.

        Asset resource

        :param asset: teflo asset resource
        :type asset: object
        """

        self.plugin = getattr(asset, 'provisioner')(asset)

    def print_commonly_used_attributes(self):
        """Print commonly used attributes from the class instance."""
        self.logger.debug('Available provider parameters:\n %s'
                          % pformat(getattr(self.plugin, 'provider_params')))
        self.logger.debug('Available provider credentials:\n %s'
                          % pformat(mask_credentials_password(getattr(self.plugin, 'provider_credentials'))))

    def validate(self):
        """

        validate the params provided are supported by the plugin
        :return:
        """
        try:
            self.plugin.validate()
        except Exception:
            raise
        else:
            self.logger.info('successfully validated scenario Asset against the schema!')

    def create(self):
        """Create method. (must implement!)

        Provision the host supplied.
        """
        host = getattr(getattr(self.plugin, 'asset'), 'name')
        self.logger.info('Provisioning asset %s.' % host)
        self.print_commonly_used_attributes()
        try:
            res = self.plugin.create()
            if res is None or len(res) == 0:
                # Plugin used is either beaker_client_plugin or openstack_libcloud_plugin
                # or empty res is libvirt_network was false or resources other than hosts
                # are provisioned . Here no operation is done
                return
            # If res is greater than one , multiple resources have been provisioned
            if len(res) > 1:
                res_profile_list = list()
                for i in range(0, len(res)):
                    # res > 1 when count > 1. This is available when using linchpin plugin, os_client plugin or other
                    # provisioner plugin which supports multiple resources is used.
                    # With linchpin plugin, for beaker and aws resources, linchpin does not return a proper host name
                    # To apply names to the multiple beaker/aws resources Teflo adds a number next to the given asset
                    # name e.g. asset_name_0 , asset_name_1. The below logic is to find out if beaker/aws resources were
                    # provisioned by linchpin plugin.
                    host_profile = copy.deepcopy(getattr(getattr(self.plugin, 'asset'), 'profile')())
                    provisioner_name = ''
                    if host_profile.get('provider'):
                        provisioner_name = host_profile['provider']['name']
                    elif host_profile.get('resource_group_type'):
                        provisioner_name = host_profile.get('resource_group_type')
                    elif host_profile.get('cfgs'):
                        provisioner_name = host_profile.get('cfgs').keys[0]

                    if any(x in provisioner_name for x in ["beaker", "aws"]):
                        host_profile['name'] = host_profile['name'] + '_' + str(i)
                    else:
                        host_profile['name'] = res[i].pop('name')

                    # removing the 'name' key  and its value from the results res if present.
                    # as it can interfere with provider's name key
                    if res[i].get('name'):
                        del res[i]['name']

                    if 'ip' in res[i]:
                        host_profile['ip_address'] = res[i].pop('ip')
                    if host_profile.get('provider', False):
                        host_profile.get('provider').update(res[i])
                    else:
                        host_profile.update(res[i])
                    self.logger.debug(json.dumps(host_profile, indent=4))
                    res_profile_list.append(host_profile)
                self.logger.info('Successfully provisioned %s asset(s) %s with asset_id(s) %s:'
                                 % (len(res_profile_list), [res_profile_list[i]['name'] for i in range(0, len(res))],
                                    [res_profile_list[i]['provider']['asset_id'] if res_profile_list[i].get('provider')
                                     else res_profile_list[i]['asset_id'] for i in range(0, len(res))]))
                return res_profile_list
            else:
                # Single resource has been provisioned
                host_profile = copy.deepcopy(getattr(getattr(self.plugin, 'asset'), 'profile')())
                if res[-1].get('name', False):
                    host_profile['name'] = res[-1].pop('name')
                if 'ip' in res[-1]:
                    host_profile['ip_address'] = res[-1].pop('ip')
                if host_profile.get('provider', False):
                    host_profile.get('provider').update(res[-1])
                else:
                    host_profile.update(res[-1])
                self.logger.info('Successfully provisioned asset %s with asset_id %s.'
                                 % (host, res[-1].get('asset_id')))
                return [host_profile]

        except Exception as ex:
            self.logger.error(ex)
            raise

    def delete(self):
        """Delete method. (must implement!)

        Teardown the host supplied.
        """
        host = getattr(getattr(self.plugin, 'asset'), 'name')
        self.logger.info('Delete asset %s.' % host)
        self.print_commonly_used_attributes()
        try:
            self.plugin.delete()
            self.logger.info('Successfully deleted asset %s with asset_id %s.' %
                             (host, getattr(getattr(self.plugin, 'asset'), 'asset_id')))
        except Exception as ex:
            self.logger.error(ex)
            raise
