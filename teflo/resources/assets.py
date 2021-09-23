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
    teflo.resources.host

    Module used for building teflo host compounds. Hosts are the base to a
    scenario object. The remaining compounds that make up a scenario are
    processed against the hosts defined.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from ..core import TefloResource
from ..exceptions import TefloResourceError
from ..provisioners import AssetProvisioner
from ..helpers import gen_random_str
from ..helpers import get_provisioners_plugins_list, get_provisioner_plugin_class, get_default_provisioner_plugin, \
    is_provider_mapped_to_provisioner
from ..tasks import ProvisionTask, CleanupTask, ValidateTask
from .._compat import string_types
from collections import OrderedDict


class Asset(TefloResource):
    """
    The asset resource class. The teflo compound can contain x amount of hosts or
    other asset types (i.e. virtual networks, storage, etc.).
    Their primary responsibility is to define details about the system resource
    to be created in their declared provider. Along with saving information
    such as (ip addresses, etc) for use by the action or execute compounds of
    teflo.
    """

    _valid_tasks_types = ['validate', 'provision', 'cleanup']
    _fields = [
        'name',
        'description',
        'groups',
        'provisioner',
        'credential',
        'hostname',
        'asset_id',
        'ip_address',
        'metadata',
        'ansible_params',
        'labels',
        'cleanup_timeout',
        "provision_timeout",
        "validate_timeout"
    ]

    def __init__(self,
                 config=None,
                 name=None,
                 provisioner=None,
                 parameters={},
                 validate_task_cls=ValidateTask,
                 provision_task_cls=ProvisionTask,
                 cleanup_task_cls=CleanupTask,
                 **kwargs):
        """Constructor.

        :param config: teflo configuration
        :type config: dict
        :param name: host resource name
        :type name: str
        :param provisioner: provisioner name used to create the host in the
            defined provider
        :type provisioner: str
        :param parameters: content which makes up the host resource
        :type parameters: dict
        :param validate_task_cls: teflos validate task class
        :type validate_task_cls: object
        :param provision_task_cls: teflos provision task class
        :type provision_task_cls: object
        :param cleanup_task_cls: teflos cleanup task class
        :type cleanup_task_cls: object
        :param kwargs: additional key:value(s)
        :type kwargs: dict
        """
        super(Asset, self).__init__(config=config, name=name, **kwargs)

        # set the timeout for VALIDATE
        try:
            if parameters.get('validate_timeout') is not None:
                self._validate_timeout = parameters.pop("validate_timeout")
            else:
                self._validate_timeout = config["TIMEOUT"]["VALIDATE"]
        except TypeError:
            self.logger.error("No teflo.cfg found,  so no timeout will be set")
            self._validate_timeout = 0

        # set the timeout for provsion
        try:
            if parameters.get('provision_timeout') is not None:
                self._provision_timeout = parameters.pop("provision_timeout")
            else:
                self._provision_timeout = config["TIMEOUT"]["PROVISION"]
        except TypeError:
            self.logger.error("No teflo.cfg found,  so no timeout will be set")
            self._provision_timeout = 0
        # set the timeout for cleanup
        try:
            if parameters.get('cleanup_timeout') is not None:
                self._cleanup_timeout = parameters.pop("cleanup_timeout")
            else:
                self._cleanup_timeout = config["TIMEOUT"]["CLEANUP"]
        except TypeError:
            self.logger.error("No teflo.cfg found,  so no timeout will be set")
            self._cleanup_timeout = 0

        # set name attribute & apply filter
        if name is None:
            self._name = parameters.pop('name', None)
            if self._name is None:
                self._name = 'hst{0}'.format(gen_random_str(10))
        else:
            self._name = name

        # set description attribute
        self._description = parameters.pop('description', None)

        # check for unsupported role param . This piece is run even before validate
        # this can be removed in later versions when groups has become the new norm
        # this check can then be moved to extensions.py as a part of validating schema
        if parameters.pop('role', None):
            raise TefloResourceError('Role is not supported as a provisioner parameter. '
                                     'Please use groups instead and run the scenario again.'
                                     'Visit https://teflo.readthedocs.io/en/latest/users/definitions/'
                                     'provision.html#groups to see examples')

        # preset groups attribute
        self._groups = None
        try:
            # convert the groups into list format if groups defined as str format
            self._groups = parameters.pop('groups')
            if isinstance(self._groups, string_types):
                self._groups = self._groups.replace(' ', '').split(',')
            if self._name in self._groups:
                raise TefloResourceError('Asset name %s cannot be same as groups name %s' % (self._name, self._groups))
        except KeyError:
            self.logger.warning('Groups parameter was not set for asset %s.' % self.name)
            del self.groups

        # set metadata attribute (data pass-through)
        self._metadata = parameters.pop('metadata', {})

        # set ansible parameters
        self._ansible_params = parameters.pop('ansible_params', {})

        # check if ansible_params and groups is empty
        if not hasattr(self, 'groups') and not self._ansible_params:
            self.no_inventory = True

        # Pop any attributes that aren't needed like data_folder and workspace
        # since that already gets set.
        parameters.pop('workspace', None)
        parameters.pop('data_folder', None)

        setattr(self, 'labels', parameters.pop('labels', []))

        # determine if the host is a static machine already provisioned
        # how? if the ip_address param is defined and provider & provisioner is not defined
        # then we can be safe to say the machine is static
        if 'ip_address' in parameters and 'provider' not in parameters and \
                'provisioner' not in parameters:
            self._ip_address = parameters.pop('ip_address')
            # set flag to control whether the host is static or not
            self.is_static = True
            self._provisioner = None
            del self.provisioner
        else:
            # set flag to control whether the host is static or not
            self.is_static = False

            # lets get the right provisioner to use
            provisioner_name = parameters.pop('provisioner', provisioner)

            # save ip address if one is provided
            self._ip_address = parameters.pop('ip_address', None)

            # delete the ip_addres prop if none provided
            if not self.ip_address:
                del self.ip_address

            # host needs to be provisioned, get the provider parameters
            parameters = self.__set_provider_attr_(parameters)

            # lets setup any feature toggles that we defined in the configuration file
            self.__set_feature_toggles_()

            # TODO remove this , it is additional
            self._provisioner = get_default_provisioner_plugin()

            if provisioner_name is None and self.has_provider:
                try:
                    self._provisioner = get_default_provisioner_plugin(self._provider)
                except KeyError:
                    raise TefloResourceError('Specified provider is not supported by a provisioner.')
            elif provisioner_name:
                found_name = False
                for name in get_provisioners_plugins_list():
                    if name.startswith(provisioner_name):
                        found_name = True
                        break

                if found_name:
                    if self.has_provider and \
                            is_provider_mapped_to_provisioner(self._provider, provisioner_name):
                        self._provisioner = get_provisioner_plugin_class(provisioner_name)
                    else:
                        self._provisioner = get_provisioner_plugin_class(provisioner_name)
                else:
                    self.logger.error('Provisioner %s for asset %s is invalid.'
                                      % (provisioner_name, self.name))
                    raise TefloResourceError('The specified provisioner is not valid for the asset type.')
            else:
                raise TefloResourceError('Could not find a provisioner to satisfy the asset type.')

        # set the teflo task classes for the resource
        self._validate_task_cls = validate_task_cls
        self._provision_task_cls = provision_task_cls
        self._cleanup_task_cls = cleanup_task_cls

        # reload construct task methods
        self.reload_tasks()

        # load the parameters set into the object itself
        if parameters:
            self.load(parameters)

    def __set_feature_toggles_(self):

        self._feature_toggles = None
        for item in self.config['TOGGLES']:
            if item['name'] == 'host':
                self._feature_toggles = item

    def __set_provider_attr_(self, parameters):
        """Configure the host provider attributes.

        :param parameters: content which makes up the host resource
        :type parameters: dict
        :return: updated parameters
        :rtype: dict
        """

        self._provider = {}

        if parameters.get('provider', False):
            creds = parameters.get('provider').pop('credential', None)
            for p, v in parameters.pop('provider').items():
                if p == 'name':
                    self._provider = v
                    continue
                setattr(self, p, v)
            self.has_provider = True
        else:
            # set no provider object
            creds = parameters.pop('credential', None)
            for p, v in parameters.items():
                setattr(self, p, v)
            del self.provider
            self.has_provider = False

        # lets set the credentials if any
        if creds:
            for item in self.config['CREDENTIALS']:
                if item['name'] == creds:
                    self._credential = item
                    break

        return parameters

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        raise AttributeError("Cannot set name of the asset resource")

    @property
    def ip_address(self):
        """IP address property.

        :return: host ip address
        :rtype: str
        """
        return self._ip_address

    @ip_address.setter
    def ip_address(self, value):
        """Set ip address property."""
        self._ip_address = value

    @ip_address.deleter
    def ip_address(self):
        """Set ip address property."""
        del self._ip_address

    @property
    def metadata(self):
        """Metadata property.

        :return: host metadata
        :rtype: dict
        """
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        """Set metadata property."""
        raise AttributeError('You cannot set metadata directly. '
                             'Use function ~Asset.set_metadata')

    def set_metadata(self):
        """Set host metadata.

        This method probably will be helpful when passing data between
        action executions.
        """
        raise NotImplementedError

    @property
    def ansible_params(self):
        """Ansible parameters property.

        :return: ansible parameters for the host resource
        :rtype: dict
        """
        return self._ansible_params

    @ansible_params.setter
    def ansible_params(self, value):
        """Set ansible parameters property."""
        raise AttributeError('You cannot set the ansible parameters directly.'
                             ' This is set one time within the YAML input.')

    @property
    def provider(self):
        """Provider property.

        :return: provider class
        :rtype: object
        """
        return self._provider

    @provider.setter
    def provider(self, value):
        """Set provider property."""
        raise AttributeError('You cannot set the asset provider after asset '
                             'class is instantiated.')

    @provider.deleter
    def provider(self):
        """delete Provider property.

        :return: provider class
        :rtype: string
        """
        del self._provider

    @property
    def provisioner(self):
        """Provisioner plugin property.

        :return: provisioner plugin class
        :rtype: object
        """
        return self._provisioner

    @provisioner.setter
    def provisioner(self, value):
        """Set provisioner plugin property."""
        raise AttributeError('You cannot set the asset provisioner plugin after asset '
                             'class is instantiated.')

    @provisioner.deleter
    def provisioner(self):
        """
        delete the provisioner property
        :return:
        """
        del self._provisioner

    @property
    def groups(self):
        """Groups property.

        :return: groups the host belongs to.
        :rtype: str
        """
        return self._groups

    @groups.setter
    def groups(self, value):
        """Set groups property."""
        raise AttributeError('You cannot set the groups after asset class is '
                             'instantiated.')

    @groups.deleter
    def groups(self):
        """
        delete the groups property
        :return:
        """
        del self._groups

    @property
    def credential(self):
        """Provisioner credential property.

        :return: credential
        :rtype: dict
        """
        return self._credential

    @credential.setter
    def credential(self, value):
        """Set credential property."""
        raise AttributeError('You cannot set the asset credential after asset '
                             'class is instantiated.')

    @credential.deleter
    def credential(self):
        """
        delete the credential property
        :return:
        """
        del self._credential

    @property
    def asset_id(self):
        """Provisioner asset_id property.

        :return: credential
        :rtype: dict
        """
        return self._asset_id

    @asset_id.setter
    def asset_id(self, value):
        """Set asset_id property."""
        self._asset_id = value

    @asset_id.deleter
    def asset_id(self):
        """
        delete the asset_id property
        :return:
        """
        del self._asset_id

    @property
    def hostname(self):
        """Provisioner hostname property.

        :return: hostname
        :rtype: dict
        """
        return self._hostname

    @hostname.setter
    def hostname(self, value):
        """Set hostname property."""
        self._hostname = value

    @hostname.deleter
    def hostname(self):
        """
        delete the hostname property
        :return:
        """
        del self._hostname

    def profile(self):
        """Builds a profile for the host resource.

        :return: the host profile
        :rtype: OrderedDict
        """
        profile = OrderedDict()
        filtered_attr = {k: v for k, v in vars(self).items() if not k.startswith('_') and k not in
                         ['is_static', 'has_provider', 'no_inventory']}

        # update asset fields
        for f in self._fields:
            if f == 'groups' and hasattr(self, f):
                if all(isinstance(item, string_types) for item in self.groups):
                    profile.update(groups=[group for group in self.groups])
                continue
            elif f == 'provisioner' and hasattr(self, f):
                profile.update({'provisioner': getattr(
                    self.provisioner, '__plugin_name__')})
                if hasattr(self, 'provider') and len(getattr(self, 'provider', {})) != 0:
                    profile.update(OrderedDict(provider={}))
                    profile.get('provider').update(name=self.provider)
                    profile.get('provider').update(filtered_attr)
                else:
                    profile.update(filtered_attr)
                continue
            elif f == 'credential' and hasattr(self, f):
                if len(getattr(self, 'provider', {})) == 0:
                    profile.update(credential=self.credential.get('name'))
                else:
                    profile.get('provider').update(credential=self.credential.get('name'))
                continue
            elif f == 'metadata' and hasattr(self, f):
                if len(getattr(self, f)) != 0:
                    profile.update({f: getattr(self, f)})
                continue
            elif hasattr(self, f) and getattr(self, f) is not None:
                profile.update({f: getattr(self, f)})

        return profile

    def validate(self):
        """Validate the host."""
        if self.is_static:
            self.logger.debug('Validation is not required for static hosts!')
            return

        getattr(AssetProvisioner(self), 'validate')()

    def _construct_validate_task(self):
        """Setup the validate task data structure.

        :return: validate task definition
        :rtype: dict
        """
        task = {
            'task': self._validate_task_cls,
            'name': str(self.name),
            'resource': self,
            'methods': self._req_tasks_methods,
            "timeout": self._validate_timeout
        }
        return task

    def _construct_provision_task(self):
        """Setup the provision task data structure.

        :return: provision task definition
        :rtype: dict
        """
        task = {
            'task': self._provision_task_cls,
            'name': str(self.name),
            'asset': self,
            'msg': '   provisioning asset %s' % self.name,
            'methods': self._req_tasks_methods,
            "timeout": self._provision_timeout
        }
        return task

    def _construct_cleanup_task(self):
        """Setup the cleanup task data structure.

        :return: cleanup task definition
        :rtype: dict
        """
        task = {
            'task': self._cleanup_task_cls,
            'name': str(self.name),
            'asset': self,
            'msg': '   cleanup asset %s' % self.name,
            'methods': self._req_tasks_methods,
            "timeout": self._cleanup_timeout
        }
        return task
