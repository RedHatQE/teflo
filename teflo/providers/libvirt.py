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
    teflo.providers.libvirt

    Teflo's openstack provider module which contains all the necessary
    classes and functions to process provider validation and requests.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from ..core import TefloProvider
from ..exceptions import TefloProviderError
from collections import OrderedDict


class LibvirtProvider(TefloProvider):

    """Libvirt Provider class."""
    __provider_name__ = 'libvirt'

    def __init__(self):
        """Constructor.

        Sets the following attributes:
            - required provider parameters
            - optional provider parameters
            - required provider credential parameters
            - optional provider credential parameters

        Each attribute is a list of tuples. Within the tuple index 0 is the
        parameter name and the index 1 is the data type for the parameter.
        """
        super(LibvirtProvider, self).__init__()

        self._supported_roles = [
            'libvirt_node',
            'libvirt_network',
            'libvirt_storage'
        ]

        self.req_params = [
            ('role', [str])
        ]

        self.req_node_params = [
            ('vcpus', [int]),
            ('memory', [int])
        ]

        self.opt_node_params = [
            ('hostname', [str]),
            ('ip_address', [str]),
            ('node_id', [str]),
            ('name_separator', [str]),
            ('cpu_mode', [str]),
            ('uri', [str]),
            ('driver', [str]),
            ('image_src', [str]),
            ('arch', [str]),
            ('remote_user', [str]),
            ('boot_dev', [str]),
            ('additional_storage', [str]),
            ('disk_cache', [str]),
            ('disk_type', [str]),
            ('network_bridge', [str]),
            ('ssh_key', [str]),
            ('xml', [str]),
            ('cloud_config', [dict]),
            ('networks', [list]),
            ('storage', [list]),
            ('libvirt_image_path', [str]),
            ('libvirt_user', [str]),
            ('libvirt_become', [bool]),
            ('count', [int]),
            ('domain', [str]),
        ]

        self.opt_network_params = [
            ('uri', [str]),
            ('ip', [str]),
            ('prefix', [str]),
            ('dhcp_start', [str]),
            ('dhcp_end', [str]),
            ('bridge', [str]),
            ('domain', [str]),
            ('forward_mode', [str]),
            ('netmask', [str]),
            ('forward_dev', [str]),
            ('delete_on_destroy', [bool]),
            ('dns', [dict])
        ]

        self.req_storage_params = [
            ('size', [str]),
            ('path', [str])
        ]

        self.opt_storage_params = [
            ('uri', [str]),
        ]

        self.opt_credential_params = [
            ('username', [str]),
            ('password', [str])
        ]

        self.req_credential_params = [
            ('create_creds', [str])
        ]

    def validate_req_params(self, resource):

        """Validate the required parameters exists in the host resource.

        :param resource: host resource
        :type resource: object
        """
        name = getattr(resource, 'name')
        provider_params = getattr(resource, 'provider_params')

        for item in self.req_params:
            param, param_type = item[0], item[1]
            msg = "Resource %s : required param '%s' " % (name, param)
            try:

                param_value = provider_params[param]
                self.logger.info(msg + 'exists.')
                found_req_param = True

                if not type(param_value) in param_type:
                    self.logger.error(
                        '    - Type=%s, Required Type=%s. (ERROR)' %
                        (type(param_value), param_type))
                    raise TefloProviderError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % name
                    )
                if param_value and param_value in self._supported_roles and param_value == self._supported_roles[0]:
                    self.validate_req_node_params(provider_params, name)
                    break

                if param_value and param_value in self._supported_roles and param_value == self._supported_roles[2]:
                    self.validate_req_storage_params(provider_params, name)
                    break

            except KeyError:
                msg += ' does not exist.'
                self.logger.error(msg)
                raise TefloProviderError('A required provider parameter was not specified.')

    def validate_opt_params(self, resource):

        """Validate the optional parameters exists in the host resource.

        :param resource: host resource
        :type resource: object
        """
        name = getattr(resource, 'name')
        provider_params = getattr(resource, 'provider_params')

        for item in self.req_params:
            param, param_type = item[0], item[1]
            try:

                param_value = provider_params[param]
                if param_value and param_value in self._supported_roles and param_value == self._supported_roles[0]:
                    self.validate_opt_node_params(provider_params, name)
                    break

                if param_value and param_value in self._supported_roles and param_value == self._supported_roles[1]:
                    self.validate_opt_network_params(provider_params, name)
                    break

                if param_value and param_value in self._supported_roles and param_value == self._supported_roles[2]:
                    self.validate_opt_storage_params(provider_params, name)
                    break

            except KeyError:
                pass

    def validate_req_node_params(self, param_value, name):

        for item in self.req_node_params:
            rnp, rnt = item[0], item[1]
            msg = "Resource %s : required param '%s' " % (name, rnp)

            try:
                val = param_value[rnp]
                if not type(val) in rnt:
                    self.logger.error(
                        '    - Type=%s, Required Type=%s. (ERROR)' %
                        (type(val), rnt))
                    raise TefloProviderError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % name
                    )
                self.logger.info(msg + 'exists.')
            except KeyError:
                msg = msg + 'does not exist.'
                self.logger.error(msg)
                raise TefloProviderError(msg)

    def validate_opt_node_params(self, param_value, name):

        for item in self.opt_node_params:
            onp, ont = item[0], item[1]
            msg = "Resource %s : optional param '%s' " % (name, onp)

            try:
                val = param_value[onp]
                if not type(val) in ont:
                    self.logger.error(
                        '    - Type=%s, Optional Type=%s. (ERROR)' %
                        (type(val), ont))
                    raise TefloProviderError(
                        'Error occurred while validating optional provider '
                        'parameters for resource %s' % name
                    )
                self.logger.info(msg + 'exists.')
            except KeyError:
                self.logger.warning(msg + 'is undefined for resource.')

    def validate_opt_network_params(self, param_value, name):

        for item in self.opt_network_params:
            onp, ont = item[0], item[1]
            msg = "Resource %s : optional param '%s' " % (name, onp)

            try:
                val = param_value[onp]
                if not type(val) in ont:
                    self.logger.error(
                        '    - Type=%s, Optional Type=%s. (ERROR)' %
                        (type(val), ont))
                    raise TefloProviderError(
                        'Error occurred while validating optional provider '
                        'parameters for resource %s' % name
                    )
                self.logger.info(msg + 'exists.')
            except KeyError:
                self.logger.warning(msg + 'is undefined for resource.')

    def validate_req_storage_params(self, param_value, name):

        for item in self.req_node_params:
            rsp, rst = item[0], item[1]
            msg = "Resource %s : required param '%s' " % (name, rsp)

            try:
                val = param_value[rsp]
                if not type(val) in rst:
                    self.logger.error(
                        '    - Type=%s, Required Type=%s. (ERROR)' %
                        (type(val), rst))
                    raise TefloProviderError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % name
                    )
                self.logger.info(msg + 'exists.')
            except KeyError:
                msg = msg + 'does not exist.'
                self.logger.error(msg)
                raise TefloProviderError(msg)

    def validate_opt_storage_params(self, param_value, name):

        for item in self.opt_storage_params:
            osp, ost = item[0], item[1]
            msg = "Resource %s : optional param '%s' " % (name, osp)

            try:
                val = param_value[osp]
                if not type(val) in ost:
                    self.logger.error(
                        '    - Type=%s, Optional Type=%s. (ERROR)' %
                        (type(val), ost))
                    raise TefloProviderError(
                        'Error occurred while validating optional provider '
                        'parameters for resource %s' % name
                    )
                self.logger.info(msg + 'exists.')
            except KeyError:
                self.logger.warning(msg + 'is undefined for resource.')
