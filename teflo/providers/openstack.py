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
    teflo.providers.openstack

    Teflo's openstack provider module which contains all the necessary
    classes and functions to process provider validation and requests.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from ..core import CloudProvider
from ..exceptions import TefloProviderError


class OpenstackProvider(CloudProvider):
    """OpenStack Provider class."""
    __provider_name__ = 'openstack'

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
        super(OpenstackProvider, self).__init__()

        self.comm_opt_params = [
            ('keypair', [str])
        ]

        self.teflo_comm_opt_params = [
            ('floating_ip_pool', [str])
        ]

        self.linchpin_comm_opt_params = [
            ('fip_pool', [str])
        ]

        self.linchpin_only_opt_params = [
            ('security_groups', [str]),
            ('auto_ip', [bool]),
            ('userdata', [str]),
            ('boot_from_volume', [bool]),
            ('volume_size', [str]),
            ('boot_volume', [str]),
            ('availability_zone', [str]),
            ('config_drive', [str]),
            ('delete_fip', [str]),
            ('flavor_include', [str]),
            ('flavor_ram', [str]),
            ('floating_ips', [list]),
            ('image_exclude', [str]),
            ('interface', [str]),
            ('additional_volumes', [list]),
            ('tx_id', [int]),
            ('unique', [bool]),
            ('count', [int])
        ]

        self.req_credential_params = [
            ('auth_url', [str]),
            ('tenant_name', [str]),
            ('username', [str]),
            ('password', [str])
        ]

        self.opt_credential_params = [
            ('region', [str]),
            ('domain_name', [str])
        ]

    def validate_opt_params(self, host):
        """Validate the optional parameters exists in the host resource.

        :param host: host resource
        :type host: object
        """
        if getattr(host, 'provisioner_plugin') is not None:
            provisioner_name = getattr(host, 'provisioner_plugin').__plugin_name__
        else:
            provisioner_name = getattr(host, 'provisioner').__provisioner_name__
        name = getattr(host, 'name')
        param_values = getattr(host, 'provider_params')
        self.validate_common_opt_params(name, provisioner_name, param_values)
        self.validate_opt_linchpin_params(name, provisioner_name, param_values)

    def validate_common_opt_params(self, resource_name, provisioner_name, params):

        for item in self.comm_opt_params:
            param, param_type = item[0], item[1]
            msg = "Resource %s : optional param '%s' " % (resource_name, param)
            try:
                param_value = params[param]
                self.logger.info(msg + 'exists.')

                if not type(param_value) in param_type:
                    self.logger.error(
                        '    - Type=%s, Optional Type=%s. (ERROR)' %
                        (type(param_value), param_type))
                    raise TefloProviderError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % resource_name
                    )
            except KeyError:
                self.logger.warning(msg + 'is undefined for resource.')

        for item in self.linchpin_comm_opt_params:
            param, param_type = item[0], item[1]
            msg = "Resource %s : optional param '%s' " % (resource_name, param)
            err_msg = "Resource %s : optional param '%s' or it's value type is " \
                      "not support by the openstack-libcloud provisioner" % (resource_name, param)
            try:
                param_value = params[param]
                if 'linchpin' not in provisioner_name:
                    self.logger.error(msg)
                    raise TefloProviderError(err_msg)
                else:
                    self.logger.info(msg + 'exists.')

                if not type(param_value) in param_type:
                    self.logger.error(
                        '    - Type=%s, Optional Type=%s. (ERROR)' %
                        (type(param_value), param_type))
                    raise TefloProviderError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % resource_name
                    )
            except KeyError:
                self.logger.warning(msg + 'is undefined for resource.')

        for item in self.teflo_comm_opt_params:
            param, param_type = item[0], item[1]
            msg = "Resource %s : optional param '%s' " % (resource_name, param)
            try:
                param_value = params[param]
                if 'linchpin' in provisioner_name:
                    self.logger.warning(
                        msg + 'is forward compatible with the linchpin provisioner. It will be translated '
                              'to be in proper format for linchpin.')
                    if not type(param_value) in param_type:
                        self.logger.warning(
                            '    - Type=%s, Optional Type=%s. (WARNING)' %
                            (type(param_value), param_type))
                else:
                    self.logger.info(msg + 'exists.')

                if 'linchpin' in provisioner_name:
                    if not type(param_value) in param_type:
                        self.logger.warning(
                            '    - Type=%s, Optional Type=%s. (WARNING)' %
                            (type(param_value), param_type))
                else:

                    if not type(param_value) in param_type:
                        self.logger.error(
                            '    - Type=%s, Optional Type=%s. (ERROR)' %
                            (type(param_value), param_type))
                        raise TefloProviderError(
                            'Error occurred while validating required provider '
                            'parameters for resource %s' % resource_name
                        )

            except KeyError:
                self.logger.warning(msg + 'is undefined for resource.')

    def validate_opt_linchpin_params(self, resource_name, provisioner_name, params):

        if 'linchpin' in provisioner_name:
            for item in self.linchpin_only_opt_params:
                param, param_type = item[0], item[1]
                msg = "Resource %s : optional param '%s' " % (resource_name, param)
                try:
                    param_value = params[param]
                    self.logger.info(msg + 'exists.')

                    if not type(param_value) in param_type:
                        self.logger.error(
                            '    - Type=%s, Optional Type=%s. (ERROR)' %
                            (type(param_value), param_type))
                        raise TefloProviderError(
                            'Error occurred while validating required provider '
                            'parameters for resource %s' % resource_name
                        )
                except KeyError:
                    self.logger.warning(msg + 'is undefined for resource.')
        else:
            for item in self.linchpin_only_opt_params:
                param, param_type = item[0], item[1]
                msg = "Resource %s : optional param '%s' is " \
                      "not support by the openstack-libcloud provisioner" % (resource_name, param)
                try:
                    if params[param]:
                        raise TefloProviderError(msg)
                except KeyError:
                    pass
