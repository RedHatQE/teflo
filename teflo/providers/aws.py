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
    teflo.providers.aws

    Teflo's openstack provider module which contains all the necessary
    classes and functions to process provider validation and requests.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from ..core import TefloProvider
from ..exceptions import TefloProviderError
from collections import OrderedDict


class AwsProvider(TefloProvider):

    """AWS Provider class."""
    __provider_name__ = 'aws'

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
        super(AwsProvider, self).__init__()

        self._supported_roles = [self.__provider_name__ + '_' + suffix
                                 for suffix in ['ec2', 'sg',
                                                's3', 'ec2_key',
                                                'cfn', 'ec2_eip',
                                                'ec2_vpc_net', 'ec2_vpc_subnet',
                                                'ec2_vpc_routeable', 'ec2_vpc_endpoint',
                                                'ec2_elb_lb', 'ec2_vpc_nat_gateway',
                                                'ec2_vpc_internet_gateway']
                                 ]

        self.req_params = [
            ('role', [str])
        ]

        self.req_ec2_params = [
            ('flavor', [str]),
        ]

        self.opt_ec2_params = [
            ('region', [str]),
            ('node_id', [str]),
            ('image', [str]),
            ('count', [int]),
            ('keypair', [str]),
            ('security_group', [list]),
            ('vpc_subnet_id', [str]),
            ('assign_public_ip', [bool]),
            ('instance_tags', [OrderedDict, dict]),
            ('wait_timeout', [int])
        ]

        self.req_sg_params = [
            ('description', [str]),
            ('rules', [list])
        ]

        self.opt_sg_params = [
            ('region', [str]),
            ('vpc_id', [str])
        ]

        self.req_s3_params = [
            ('region', [str]),
        ]

        self.opt_s3_params = [
            ('debug_botocore_endpoint_logs', [bool]),
            ('dest', [str]),
            ('dualstack', [bool]),
            ('encrypt', [bool]),
            ('encryption_kms_key_id', [str]),
            ('encryption_mode', [str]),
            ('expiration', [int]),
            ('headers', [str]),
            ('ignore_nonexistent_bucket', [bool]),
            ('marker', [str]),
            ('max_keys', [int]),
            ('metadata', [str]),
            ('mode', [str]),
            ('object', [str]),
            ('overwrite', [str]),
            ('prefix', [str]),
            ('profile', [str]),
            ('retries', [int]),
            ('rgw', [bool]),
            ('s3_url', [str]),
            ('src', [str]),
            ('validate_certs', [bool]),
            ('version', [str]),
            ('permission', [str])

        ]

        self.opt_ec2_key_params = [
            ('region', [str]),
        ]

        self.opt_cfn_params = [
            ('region', [str]),
            ('template_path', [str]),
        ]

        self.req_ec2_eip_params = [
            ('region', [str])
        ]

        self.opt_ec2_eip_params = [
            ('allow_association', [str]),
            ('device_id', [str]),
            ('ec2_url', [str]),
            ('in_vpc', [str]),
            ('private_ip_address', [str]),
            ('public_ip_address', [str]),
            ('release_on_disassociation', [str]),
            ('reuse_existing_ip_allowed', [str]),
        ]

        self.req_ec2_vpc_net_params = [
            ('region', [str]),
            ('cidr_block', [str]),
        ]

        self.opt_ec2_vpc_net_params = [
            ('dhcp_opts_id', [str]),
            ('dns_hostnames', [bool]),
            ('dns_support', [bool]),
            ('ec2_url', [str]),
            ('multi_ok', [bool]),
            ('purge_cidrs', [bool]),
            ('tags', [OrderedDict, dict]),
            ('tenancy', [str]),
            ('validate_certs', [bool])
        ]

        self.req_ec2_vpc_subnet_params = [
            ('region', [str]),
        ]

        self.opt_ec2_vpc_subnet_params = [
            ('assign_instances_ipv6', [bool]),
            ('vpc_name', [str]),
            ('vpc_id', [str]),
            ('az', [str]),
            ('cidr', [str]),
            ('ec2_url', [str]),
            ('ipv6_cidr', [str]),
            ('map_public', [bool]),
            ('purge_tags', [bool]),
            ('tags', [OrderedDict, dict]),
            ('validate_certs', [bool])
        ]

        self.req_ec2_vpc_routeable_params = [
            ('region', [str]),
        ]

        self.opt_ec2_vpc_routeable_params = [
            ('propogating_vgw_ids', [str]),
            ('purge_routes', [bool]),
            ('purge_subnets', [bool]),
            ('purge_tags', [bool]),
            ('route_table_id', [str]),
            ('routes', [list]),
            ('subnets', [list]),
            ('tags', [OrderedDict, dict]),
            ('vpc_id', [str]),
            ('vpc_name', [str]),
            ('validate_certs', [bool])
        ]

        self.req_ec2_vpc_endpoint_params = [
            ('region', [str]),
        ]

        self.opt_ec2_vpc_endpoint_params = [
            ('service', [str]),
            ('vpc_endpoint_id', [str]),
            ('vpc_id', [str]),
            ('policy', [str]),
            ('policy_file', [str]),
            ('route_table_ids', [list]),
            ('route_table_name', [str]),
            ('vpc_id', [str]),
            ('vpc_name', [str]),
            ('validate_certs', [bool])
        ]

        self.req_ec2_elb_lb_params = [
            ('region', [str]),
        ]

        self.opt_ec2_elb_lb_params = [
            ('access_logs', [OrderedDict, dict]),
            ('connection_draining_timeout', [int]),
            ('cross_az_load_balancing', [bool]),
            ('ec2_url', [str]),
            ('health_check', [OrderedDict, dict]),
            ('tags', [OrderedDict, dict]),
            ('zones', [list]),
            ('subnets', [list]),
            ('idle_timeout', [int]),
            ('instance_ids', [list]),
            ('stickiness', [OrderedDict, dict]),
            ('security_group_ids', [list]),
            ('security_group_names', [list]),
            ('listeners', [list]),
            ('purge_instance_ids', [bool]),
            ('purge_listeners', [bool]),
            ('purge_subnets', [bool]),
            ('purge_zones', [bool])
        ]

        self.req_ec2_vpc_nat_gateway_params = [
            ('region', [str]),
            ('vpc_id', [str])
        ]

        self.opt_ec2_vpc_nat_gateway_params = [
            ('profile', [str]),
            ('release_eip', [bool]),
            ('eip_address', [str]),
            ('client_token', [str]),
            ('subnet_id', [str]),
            ('subnet_filters', [OrderedDict, dict]),
            ('force', [bool]),
            ('wait', [bool]),
            ('allocation_id', [str]),
            ('ec2_url', [str]),
            ('wait_timeout', [int])
        ]

        self.req_ec2_vpc_internet_gateway_params = [
            ('region', [str]),
            ('vpc_id', [str])
        ]

        self.opt_ec2_vpc_internet_gateway_params = [
            ('ec2_url', [str]),
            ('debug_botocore_endpoint_logs', [bool]),
            ('profile', [str]),
            ('state', [str]),
            ('tags', [OrderedDict, dict]),
            ('validate_certs', [bool])
        ]

        self.opt_credential_params = [
            ('aws_access_key_id', [str]),
            ('aws_secret_access_key', [str]),
            ('aws_security_token', [str])

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

                if not type(param_value) in param_type:
                    self.logger.error(
                        '    - Type=%s, Required Type=%s. (ERROR)' %
                        (type(param_value), param_type))
                    raise TefloProviderError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % name
                    )
                if param_value and param_value in self._supported_roles:
                    getattr(self, 'validate_req_%s_params' % param_value[4:])(provider_params, name)
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
                if param_value and param_value in self._supported_roles:
                    getattr(self, 'validate_opt_%s_params' % param_value[4:])(provider_params, name)
                    break

            except KeyError:
                pass

    def validate_req_ec2_params(self, param_value, name):

        for item in getattr(self, 'req_%s_params' % param_value['role'][4:]):
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

    def validate_opt_ec2_params(self, param_value, name):

        for item in getattr(self, 'opt_%s_params' % param_value['role'][4:]):
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

    def validate_req_sg_params(self, param_value, name):

        for item in getattr(self, 'req_%s_params' % param_value['role'][4:]):
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

    def validate_opt_sg_params(self, param_value, name):

        for item in getattr(self, 'opt_%s_params' % param_value['role'][4:]):
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

    def validate_req_s3_params(self, param_value, name):

        for item in getattr(self, 'req_%s_params' % param_value['role'][4:], []):
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

    def validate_opt_s3_params(self, param_value, name):

        for item in getattr(self, 'opt_%s_params' % param_value['role'][4:]):
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

    def validate_req_ec2_key_params(self, param_value, name):

        for item in getattr(self, 'req_%s_params' % param_value['role'][4:], []):
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

    def validate_opt_ec2_key_params(self, param_value, name):

        for item in getattr(self, 'opt_%s_params' % param_value['role'][4:]):
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

    def validate_req_cfn_params(self, param_value, name):

        for item in getattr(self, 'req_%s_params' % param_value['role'][4:], []):
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

    def validate_opt_cfn_params(self, param_value, name):

        for item in getattr(self, 'opt_%s_params' % param_value['role'][4:]):
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

    def validate_req_ec2_eip_params(self, param_value, name):

        for item in getattr(self, 'req_%s_params' % param_value['role'][4:]):
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

    def validate_opt_ec2_eip_params(self, param_value, name):

        for item in getattr(self, 'opt_%s_params' % param_value['role'][4:]):
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

    def validate_req_ec2_vpc_net_params(self, param_value, name):

        for item in getattr(self, 'req_%s_params' % param_value['role'][4:]):
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

    def validate_opt_ec2_vpc_net_params(self, param_value, name):

        for item in getattr(self, 'opt_%s_params' % param_value['role'][4:]):
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

    def validate_req_ec2_vpc_sunbet_params(self, param_value, name):

        for item in getattr(self, 'req_%s_params' % param_value['role'][4:]):
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

    def validate_opt_ec2_vpc_subnet_params(self, param_value, name):

        for item in getattr(self, 'opt_%s_params' % param_value['role'][4:]):
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

    def validate_req_ec2_vpc_routeable_params(self, param_value, name):

        for item in getattr(self, 'req_%s_params' % param_value['role'][4:]):
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

    def validate_opt_ec2_vpc_routeable_params(self, param_value, name):

        for item in getattr(self, 'opt_%s_params' % param_value['role'][4:]):
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

    def validate_req_ec2_vpc_endpoint_params(self, param_value, name):

        for item in getattr(self, 'req_%s_params' % param_value['role'][4:]):
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

    def validate_opt_ec2_vpc_endpoint_params(self, param_value, name):

        for item in getattr(self, 'opt_%s_params' % param_value['role'][4:]):
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

    def validate_req_ec2_elb_lb_params(self, param_value, name):

        for item in getattr(self, 'req_%s_params' % param_value['role'][4:]):
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

    def validate_opt_ec2_elb_lb_params(self, param_value, name):

        for item in getattr(self, 'opt_%s_params' % param_value['role'][4:]):
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

    def validate_req_ec2_vpc_nat_gateway_params(self, param_value, name):

        for item in self.getattr(self, 'req_%s_params' % param_value['role'][4:]):
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

    def validate_opt_ec2_vpc_nat_gateway_params(self, param_value, name):

        for item in getattr(self, 'opt_%s_params' % param_value['role'][4:]):
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

    def validate_req_ec2_vpc_internet_gateway_params(self, param_value, name):

        for item in getattr(self, 'req_%s_params' % param_value['role'][4:]):
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

    def validate_opt_ec2_vpc_internet_gateway_params(self, param_value, name):

        for item in getattr(self, 'opt_%s_params' % param_value['role'][4:]):
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
