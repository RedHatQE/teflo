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
    teflo.providers.beaker

    Teflo's beaker provider module which contains all the necessary
    classes and functions to process provider validation and requests.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from ..core import PhysicalProvider
from ..exceptions import TefloProviderError
import re


class BeakerProvider(PhysicalProvider):
    """Beaker provider class."""
    __provider_name__ = 'beaker'

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
        super(BeakerProvider, self).__init__()

        self.req_params = [
            ('name', [str]),
            ('arch', [str]),
            ('variant', [str])
        ]

        self.comm_opt_params = [
            ('distro', [str]),
            ('family', [str]),
            ('whiteboard', [str]),
            ('kickstart', [str]),
            ('taskparam', [list])

        ]

        self.linchpin_comm_opt_params = [
            ('kernel_options', [str]),
            ('kernel_options_post', [str]),
            ('hostrequires', [list]),
            ('tags', [list]),
            ('ks_meta', [str]),
            ('job_group', [str]),
            ('keyvalue', [list]),
            ('ssh_key', [list])
        ]

        self.linchpin_only_opt_params = [
            ('max_attempts', [int]),
            ('attempt_wait_time', [int]),
            ('cancel_message', [str]),
            ('ids', [list]),
            ('reserve_duration', [int]),
            ('repos', [list]),
            ('install', [list]),
            ('ks_append', [list]),
            ('partitions', [list]),
            ('tx_id', [int]),
            ('count', [int])
        ]

        self.teflo_comm_opt_params = [
            ('kernel_options', [list]),
            ('kernel_post_options', [list]),
            ('host_requires_options', [list]),
            ('tag', [str]),
            ('ksmeta', [list]),
            ('jobgroup', [str]),
            ('key_values', [list]),
            ('ssh_key', [str])
        ]

        self.teflo_only_opt_params = [
            ('distro_requires_options', [list]),
            ('virtual_machine', [bool]),
            ('virt_capable', [bool]),
            ('retention_tag', [str]),
            ('priority', [str]),
            ('timeout', [int]),
            ('username', [str]),
            ('password', [str]),
            ('ignore_panic', [str])
        ]

        self.opt_params = [
            ('distro', [str]),
            ('family', [str]),
            ('whiteboard', [str]),
            ('kernel_options', [list]),
            ('kernel_post_options', [list]),
            ('host_requires_options', [list]),
            ('distro_requires_options', [list]),
            ('virtual_machine', [bool]),
            ('virt_capable', [bool]),
            ('retention_tag', [str]),
            ('tag', [str]),
            ('priority', [str]),
            ('jobgroup', [str]),
            ('key_values', [list]),
            ('timeout', [int]),
            ('hostname', [str]),
            ('ip_address', [str]),
            ('job_id', [str]),
            ('ssh_key', [str]),
            ('username', [str]),
            ('password', [str]),
            ('taskparam', [list]),
            ('ignore_panic', [str]),
            ('kickstart', [str]),
            ('ksmeta', [list])
        ]

        self.req_credential_params = [
            ('hub_url', [str])
        ]

        self.opt_credential_params = [
            ('keytab_principal', [str]),
            ('keytab', [str]),
            ('username', [str]),
            ('password', [str]),
            ('ca_cert', [str]),
            ('realm', [str]),
            ('service', [str]),
            ('ccache', [str])
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
        self.validate_opt_teflo_params(name, provisioner_name, param_values)

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
                        'Error occurred while validating common optional provider '
                        'parameters for resource %s' % resource_name
                    )
            except KeyError:
                self.logger.warning(msg + 'is undefined for resource.')

        for item in ['ssh_key', 'kernel_options']:
            msg = "Resource %s : optional param '%s' " % (resource_name, item)
            err_msg = "Resource %s : optional param '%s' or it's value type is " \
                      "not support by the bkr-client provisioner" % (resource_name, item)
            try:
                param_value = params[item]
                if item == 'ssh_key':
                    if 'linchpin' in provisioner_name:
                        if isinstance(param_value, list):
                            self.logger.info(msg + 'exists.')
                        elif isinstance(param_value, str):
                            self.logger.warning(msg + 'is forward compatible '
                                                      'with the linchpin provisioner. It will be translated '
                                                      'to be in proper format for linchpin.')
                            self.logger.warning(
                                    '    - Type=%s, Optional Type=%s. (WARNING)' %
                                    (type(param_value), list))
                        else:
                            self.logger.error(
                                '    - Type=%s, Optional Type=%s. (ERROR)' %
                                (type(param_value), str))
                            raise TefloProviderError(
                                'Error occurred while validating common optional provider '
                                'parameters for resource %s' % resource_name
                            )

                    if 'linchpin' not in provisioner_name:
                        if not isinstance(param_value, str):
                            self.logger.error(
                                '    - Type=%s, Optional Type=%s. (ERROR)' %
                                (type(param_value), str))
                            raise TefloProviderError(err_msg)
                        else:
                            self.logger.info(msg + 'exists.')
                if item == 'kernel_options':
                    if 'linchpin' in provisioner_name:
                        if isinstance(param_value, str):
                            self.logger.info(msg + 'exists.')
                        if isinstance(param_value, list):
                            self.logger.warning(msg + 'is forward compatible '
                                                      'with the linchpin provisioner. It will be translated '
                                                      'to be in proper format for linchpin.')
                            self.logger.warning(
                                '    - Type=%s, Optional Type=%s. (WARNING)' %
                                (type(param_value), str))
                        else:
                            self.logger.error(
                                '    - Type=%s, Optional Type=%s. (ERROR)' %
                                (type(param_value), str))
                            raise TefloProviderError(
                                'Error occurred while validating common optional provider '
                                'parameters for resource %s' % resource_name)

                    if 'linchpin' not in provisioner_name:
                        if not isinstance(param_value, str):
                            self.logger.error(
                                '    - Type=%s, Optional Type=%s. (ERROR)' %
                                (type(param_value), str))
                            raise TefloProviderError(err_msg)
                        else:
                            self.logger.info(msg + 'exists.')

            except KeyError:
                self.logger.warning(msg + 'is undefined for resource.')

        for item in self.linchpin_comm_opt_params:
            param, param_type = item[0], item[1]
            msg = "Resource %s : optional param '%s' " % (resource_name, param)
            err_msg = "Resource %s : optional param '%s' or it's value type is " \
                      "not support by the bkr-client provisioner" % (resource_name, param)
            try:
                param_value = params[param]
                if param in ['ssh_key', 'kernel_options']:
                    continue
                if 'linchpin' not in provisioner_name:
                    raise TefloProviderError(err_msg)
                self.logger.info(msg + 'exists.')

                if not type(param_value) in param_type:
                    self.logger.error(
                        '    - Type=%s, Optional Type=%s. (ERROR)' %
                        (type(param_value), param_type))
                    raise TefloProviderError(
                        'Error occurred while validating common optional provider '
                        'parameters for resource %s' % resource_name
                    )
            except KeyError:
                self.logger.warning(msg + 'is undefined for resource.')

        for item in self.teflo_comm_opt_params:
            param, param_type = item[0], item[1]
            msg = "Resource %s : optional param '%s' " % (resource_name, param)
            try:
                param_value = params[param]
                if param in ['ssh_key', 'kernel_options']:
                    continue
                if 'linchpin' in provisioner_name:
                    self.logger.warning(msg + 'is forward compatible '
                                              'with the linchpin provisioner. It will be translated '
                                              'to be in proper format for linchpin.')
                    for lp, lt in self.linchpin_comm_opt_params:
                        if all('post' in p for p in [lp, param]):
                            if not type(param_value) in lt:
                                self.logger.warning(
                                    '    - Type=%s, Optional Type=%s. (WARNING)' %
                                    (type(param_value), lt))
                        if all('tag' in p for p in [lp, param]):
                            if not type(param_value) in lt:
                                self.logger.warning(
                                    '    - Type=%s, Optional Type=%s. (WARNING)' %
                                    (type(param_value), lt))
                        if all('values' in p for p in [lp, param]):
                            if not type(param_value) in lt:
                                self.logger.warning(
                                    '    - Type=%s, Optional Type=%s. (WARNING)' %
                                    (type(param_value), lt))
                else:
                    self.logger.info(msg + 'exists.')
                    if not type(param_value) in param_type:
                        self.logger.error(
                            '    - Type=%s, Optional Type=%s. (ERROR)' %
                            (type(param_value), param_type))
                        raise TefloProviderError(
                            'Error occurred while validating common optional provider '
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
                            'Error occurred while validating linchpin optional provider '
                            'parameters for resource %s' % resource_name
                        )
                except KeyError:
                    self.logger.warning(msg + 'is undefined for resource.')
        else:
            for item in self.linchpin_only_opt_params:
                param, param_type = item[0], item[1]
                msg = "Resource %s : optional param '%s' is " \
                      "not support by the bkr-client provisioner" % (resource_name, param)
                try:
                    if params[param]:
                        raise TefloProviderError(msg)
                except KeyError:
                    pass

    def validate_opt_teflo_params(self, resource_name, provisioner_name, params):

        if 'linchpin' not in provisioner_name:
            for item in self.teflo_only_opt_params:
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
                            'Error occurred while validating teflo optional provider '
                            'parameters for resource %s' % resource_name
                        )
                except KeyError:
                    self.logger.warning(msg + 'is undefined for resource.')
        else:
            for item in self.teflo_only_opt_params:
                param, param_type = item[0], item[1]
                msg = "Resource %s : optional param '%s' is " \
                      "not support by the linchpin-wrapper provisioner" % (resource_name, param)
                try:
                    if params[param]:
                        raise TefloProviderError(msg)
                except KeyError:
                    pass
