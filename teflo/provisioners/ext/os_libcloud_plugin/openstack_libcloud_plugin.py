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
    teflo.provisioners.openstack_libcloud

    Teflo's own OpenStack provisioner. This module handles everything from
    authentication to creating/deleting resources in OpenStack.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import random
import time
import os

import libcloud.security
import urllib3
from libcloud.compute.providers import get_driver
from libcloud.compute.types import InvalidCredsError, Provider

from teflo._compat import string_types
from teflo.core import ProvisionerPlugin
from teflo.exceptions import OpenstackProviderError
from teflo.helpers import gen_random_str, filter_host_name, schema_validator

MAX_WAIT_TIME = 100
MAX_ATTEMPTS = 3


class OpenstackLibCloudProvisionerPlugin(ProvisionerPlugin):
    """Teflo's openstack apache libcloud provisioner plugin implementation.

    This class is a base which calls openstack provider methods to perform
    the actions to create and delete resources.
    """
    __plugin_name__ = 'openstack-libcloud'
    __schema_file_path__ = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                        "schema.yml"))

    def __init__(self, asset):
        """Constructor.

        :param asset: The asset object.
        """
        super(OpenstackLibCloudProvisionerPlugin, self).__init__(asset)

        # object place holders
        self._driver = object
        self._node = object
        self._image = object
        self._size = object
        self._network = object
        self._floating_ip_pool = object
        self._floating_ip = object
        self._key_pair = object

    def authenticate(self):
        """Openstack authentication.

        This method will create a driver object with libcloud provider class.
        Once driver object is created, it will verify the authentication with
        openstack endpoint is valid. If invalid, an exception will be raised.

        Apache libcloud recommends to test authentication to test calling a
        method to perform some request against openstack. Checking the
        networks is quick to determine if authentication is good. FAQ:
            - http://libcloud.readthedocs.io/en/latest/faq.html
        """
        # ignore SSL
        libcloud.security.VERIFY_SSL_CERT = False

        # suppress insecure request warning messages
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        credentials = self.provider_credentials

        # determine region
        try:
            if not credentials['region']:
                # set default region if no region is defined
                credentials['region'] = 'regionOne'
        except KeyError:
            credentials['region'] = 'regionOne'

        # determine domain
        try:
            if not credentials['domain_name']:
                # set the default domain if no domain is defined
                credentials['domain_name'] = 'default'
        except KeyError:
            credentials['domain_name'] = 'default'

        # create libcloud driver object
        self._driver = get_driver(Provider.OPENSTACK)(
            credentials['username'],
            credentials['password'],
            ex_tenant_name=credentials['tenant_name'],
            ex_force_auth_url=credentials['auth_url'].split('/v')[0],
            ex_force_auth_version='3.x_password',
            ex_domain_name=credentials['domain_name'],
            ex_force_service_region=credentials['region']
        )
        # test authentication
        try:
            self._driver.ex_list_networks()
        except InvalidCredsError as ex:
            raise OpenstackProviderError(
                'Authentication failed: %s' % ex
            )

    def unset_driver(self):
        """Unset libcloud driver object.

        This method is needed by teflo framework when it runs in parallel.
        We are unable to store objects which have an established connection
        to a provider in a multiprocessing queue. The framework will hang. To
        handle this we need to drop the connection before adding the provider
        object back into the queue. This code exists in openstack v1 module.
        """
        self.driver = object

    @property
    def driver(self):
        """Return driver object."""
        self.authenticate()
        return self._driver

    @driver.setter
    def driver(self, value):
        """Set driver object.

        :param value: Driver instance.
        :type value: object
        """
        self._driver = value

    @property
    def nodes(self):
        """Return list of nodes."""
        return self.driver.list_nodes()

    @property
    def images(self):
        """Return list of images."""
        return self.driver.list_images()

    @property
    def sizes(self):
        """Return list of sizes."""
        return self.driver.list_sizes()

    @property
    def networks(self):
        """Return list of networks."""
        return self.driver.ex_list_networks()

    @property
    def floating_ip_pools(self):
        """Return list of floating ip pools."""
        return self.driver.ex_list_floating_ip_pools()

    @property
    def key_pairs(self):
        """Return list of key pairs."""
        return self.driver.list_key_pairs()

    def image_lookup(self, name):
        """Get the libcloud image object based on the image provided.

        This method will fetch all images using libcloud and return the
        image object matching the image given. If no image is found, an
        exception will be raised.

        :param name: Image name.
        :type name: str
        :return: Image object.
        :rtype: object
        """
        # collect images
        _images = self.images

        # filter images
        by_name = list(filter(lambda elm: elm.name == name, _images))
        by_id = list(filter(lambda elm: elm.id == name, _images))

        # process results
        if len(by_name) != 0:
            return by_name[0]
        elif len(by_id) != 0:
            return by_id[0]
        else:
            raise OpenstackProviderError('Image %s not found!' % name)

    def size_lookup(self, name):
        """Get the libcloud size object based on the size provided.

        This method will fetch all sizes (flavors) using libcloud and return
        the size object matching the size (flavor) given. If no size is found,
        an exception will be raised.

        :param name: Image name.
        :type name: str
        :return: Size object.
        :rtype: object
        """
        # collect sizes
        _sizes = self.sizes

        # filter sizes
        by_name = list(filter(lambda elm: elm.name == name, _sizes))
        by_id = list()
        for size in _sizes:
            try:
                if name == int(size.id):
                    by_id.append(size)
                    break
            except ValueError:
                # base 10
                continue

        # process results
        if len(by_name) != 0:
            return by_name[0]
        elif len(by_id) != 0:
            return by_id[0]
        else:
            raise OpenstackProviderError('Flavor %s not found!' % name)

    def network_lookup(self, name):
        """Get the libcloud network object based on the network provided.

        This method will fetch all networks using libcloud and return the
        network object matching the network given. If no network is found, an
        exception will be raised.

        :param name: Network name.
        :type name: str or list
        :return: Network object.
        :rtype: object
        """
        # collect networks
        _networks = self.networks

        # filter networks
        nets = list()
        if isinstance(name, string_types):
            nets = list(filter(lambda elm: elm.name == name, _networks))
        elif isinstance(name, list):
            for net in name:
                data = list(filter(lambda elm: elm.name == net, _networks))
                if len(data) != 0:
                    nets.append(data)

        # process results
        if len(nets) == 0:
            raise OpenstackProviderError('Network(s) %s not found!' % name)
        else:
            return nets[0]

    def node_lookup(self, name):
        """Get the libcloud node object based on the node name provided.

        This method will fetch all nodes using libcloud and return the node
        object matching the node name given. If no node is found, an exception
        will be raised.

        :param name: Node name.
        :type name: str
        :return: Node object.
        :rtype: object
        """
        # filter nodes
        data = list(filter(lambda elm: elm.name == name, self.nodes))

        # process results
        if len(data) == 0:
            raise OpenstackProviderError('Node %s not found!' % name)
        else:
            return data[0]

    def floating_ip_pool_lookup(self, name):
        """Get the libcloud fip object based on the fip provided.

        This method will fetch all floating ip pools using libcloud and
        return the floating ip pool object matching the floating ip pool name
        given. If no floating ip pool is found, an exception will be raised.

        :param name: Floating ip pool name.
        :type name: str
        :return: Floating ip pool object.
        :rtype: object
        """
        # filter floating ip pools
        data = list(filter(lambda elm: elm.name == name,
                           self.floating_ip_pools))

        # process results
        if len(data) == 0:
            raise OpenstackProviderError('FIP %s not found!' % name)
        else:
            return data[0]

    def key_pair_lookup(self, name):
        """Get the libcloud key pair object based on the key pair provided.

        This method will fetch all key pairs using libcloud and return the
        key pair object matching the key pair name given. If no key pair is
        found, an exception will be raised.

        :param name: Key pair name.
        :type name: str
        :return: Key pair object.
        :rtype: object
        """
        # filter key pairs
        data = list(filter(lambda elm: elm.name == name, self.key_pairs))

        # process results
        if len(data) == 0:
            raise OpenstackProviderError('Keypair %s not found!' % name)
        else:
            return data[0]

    def floating_ip_lookup(self, node):
        """Get the floating ip object based on the node provided.

        This method will return the foating ip address for the node given. If
        no floating ip is found, an exception will be raised.

        :param node: Node object.
        :type node: object
        :return: Floating ip object.
        :rtype: object
        """
        for key in node.extra['addresses']:
            for network in node.extra['addresses'][key]:
                # skip if network is not type floating
                if network['OS-EXT-IPS:type'] != 'floating':
                    continue
                return network['addr']

        raise OpenstackProviderError('Unable to get FIP for node!')

    def create_node(self, name, image, size, network, key_pair, metadata):
        """Create node.

        This method will create a new node in openstack. The node will be
        created based on the resource specifications provided. At any point if
        the creation gets an exception, it will wait and retry creating the
        node. If maximum attempts are reached, an exception will be raised.

        :param name: Node name.
        :type name: str
        :param image: Image name.
        :type image: str
        :param size: Size name.
        :type size: str
        :param network: Network name.
        :type network: str
        :param key_pair: Key pair to inject into node.
        :type key_pair: str
        :param metadata: Metadata for the node.
        :type metadata: Dict[str, str]
        :return: Node object.
        :rtype: object
        """
        attempt = 1

        self.logger.debug('Creating node %s.' % name)
        self.logger.debug('Node details:\n * keypair=%s\n * image=%s\n '
                          '* flavor=%s\n * networks=%s\n * metadata=%s' %
                          (key_pair, image, size, network, metadata))

        # cache image object
        _image = self.image_lookup(image)

        # cache size object
        _size = self.size_lookup(size)

        # network object
        _network = self.network_lookup(network)

        # create node
        while attempt <= MAX_ATTEMPTS:
            try:
                node = self.driver.create_node(
                    name=name,
                    image=_image,
                    size=_size,
                    networks=_network,
                    ex_keyname=key_pair,
                    ex_metadata=metadata
                )
                self.logger.info('Successfully booted node %s.' % name)
                return node
            except Exception as ex:
                self.logger.error(ex)
                wait_time = random.randint(10, MAX_WAIT_TIME)
                self.logger.info('Attempt %s of %s: retrying in %s seconds' %
                                 (attempt, MAX_ATTEMPTS, wait_time))
                time.sleep(wait_time)
                attempt += 1
            finally:
                self.unset_driver()

        # reach this point, maximum attempts to create node reached
        raise OpenstackProviderError(
            'Maximum attempts reached to boot node %s.' % name
        )

    def delete_node(self, node):
        """Delete node.

        This method will delete an existing node in openstack. At any point if
        the deletion gets an exception, it will wait and retry creating the
        node. If maximum attempts are reached, an exception will be raised.

        :param node: Node object.
        :type node: object
        """
        attempt = 1

        # delete node
        while attempt <= MAX_ATTEMPTS:
            try:
                self.driver.destroy_node(node)
                self.logger.info('Successfully deleted node %s.' % node.name)
                return
            except Exception as ex:
                self.logger.error(ex)
                wait_time = random.randint(10, MAX_WAIT_TIME)
                self.logger.info('Attempt %s of %s: retrying in %s seconds' %
                                 (attempt, MAX_ATTEMPTS, wait_time))
                time.sleep(wait_time)
                attempt += 1
            finally:
                self.unset_driver()

        # reach this point, maximum attempts to delete node reached
        raise OpenstackProviderError(
            'Maximum attempts reached to delete node %s.' % node.name
        )

    def _create(self, name, image, size, network, key_pair, fip, metadata):
        """Create.

        This method will create a resource (node) in openstack. It will
        create the node, wait for the node to finish building and optionally
        attach a floating ip address. At any point if an exception is raised
        trying to wait for the node to finish building or a floating ip
        cannot be attached. It will clean up the resource (node).

        :param name: Node name.
        :type name: str
        :param image: Image name.
        :type image: str
        :param size: Size name.
        :type size: str
        :param network: Network name.
        :type network: str
        :param key_pair: Key pair to inject into node.
        :type key_pair: str
        :param fip: Floating ip pool.
        :type fip: str
        :param metadata: Metadata for the node.
        :type metadata: Dict[str, str]
        :return: Node fip. id.
        :rtype: str(s)
        """
        self.logger.info('Provisioning node %s.' % name)

        # create node
        try:
            node = self.create_node(name, image, size, network, key_pair, metadata)
        except Exception:
            self.logger.error("Failed to create node %s " % name)
            raise

        # wait for node to complete building
        try:
            self.wait_for_building_finish(node)
        except Exception as ex:
            self.logger.error(ex)
            self.logger.error('Node %s did not finish building.' % node.name)
            self.delete_node(node)
            raise OpenstackProviderError('Node did not finish building.')

        # attach floating ip to node
        try:
            ip = self.attach_floating_ip(node, fip)
        except Exception as ex:
            self.logger.error(ex)
            self.logger.error('Failed to attach fip to node %s.' % node.name)
            self.delete_node(node)
            raise OpenstackProviderError('Failed to attach fip.')

        self.logger.info('Successfully provisioned node %s.' % name)

        # if no floating ip is assigned get updated node details and look for private_ip
        # TODO: This might need more logic if we support a use case for more than one network specified
        if ip is None:
            node = self.driver.ex_get_node_details(node.id)
            ip = node.private_ips[-1]
        return ip, node.id

    def _delete(self, name):
        """Delete.

        This method will delete a resource (node) in openstack. It will check
        if the node exists, optionally detach a floating ip address and then
        delete the resource (node).

        :param name: Node name.
        :type name: str
        """
        self.logger.info('Tearing down node %s.' % name)

        try:
            # cache node
            _node = self.node_lookup(name)

            # detach floating ip
            self.detach_floating_ip(_node)

            # delete node
            self.delete_node(_node)
        except Exception as ex:
            self.logger.error(ex)
            raise OpenstackProviderError('Unable to delete node %s' % ex)
        finally:
            self.unset_driver()

        self.logger.info('Successfully teared down node %s.' % name)

    def wait_for_building_finish(self, node):
        """Wait until a node is finished building.

        :param node: node object
        """
        self.logger.info('Wait for node %s to finish building.' % node.name)

        status = 0
        attempt = 1
        while attempt <= 30:
            node = self.driver.ex_get_node_details(node.id)
            state = getattr(node, 'state')
            msg = '%s. VM %s, STATE=%s' % (attempt, node.name, state)

            if state.lower() == 'error':
                self.logger.info(msg)
                self.logger.error('VM %s got an into an error state!' %
                                  node.name)
                break
            elif state.lower() == 'running':
                self.logger.info(msg)
                self.logger.info('VM %s successfully finished building!' %
                                 node.name)
                status = 1
                break
            else:
                self.logger.info('%s, rechecking in 20 seconds.', msg)
                time.sleep(20)

        self.unset_driver()
        if status:
            self.logger.info('Node %s successfully finished building.' %
                             node.name)
        else:
            raise OpenstackProviderError('Node was unable to build, %s' %
                                         node.name)

    def attach_floating_ip(self, node, fip):
        """Attach a floating ip address to a node.

        This method will get the floating ip pool object, create a floating
        ip within that pool and attach to the node provided.

        :param node: Node object.
        :type node: object
        :param fip: Floating ip pool.
        :type fip: str
        """
        # do not attach floating ip if variable has None value
        if not fip:
            self.logger.warning('Node %s does not require fip.' % node.name)
            return

        self.logger.info('Attaching fip to node %s.' % node.name)

        try:
            # cache floating ip pool object
            _pool = self.floating_ip_pool_lookup(fip)

            # create floating ip
            _ip = _pool.create_floating_ip()

            # attach ip to node
            self.driver.ex_attach_floating_ip_to_node(node, _ip)
        except Exception as ex:
            self.logger.error(ex)
            raise OpenstackProviderError('Unable to attach FIP to %s' % node)
        finally:
            self.unset_driver()

        self.logger.info('FIP %s successfully attached to node %s.' %
                         (_ip.ip_address, node.name))
        return _ip.ip_address

    def detach_floating_ip(self, node):
        """Detach floating ip from a given node.

        This method will get the floating ip from the node provided, get the
        floating ip object, detach the floating ip from the node and delete
        the floating ip (free up resources).

        :param node: Node object.
        :type node: object
        """
        try:
            # cache floating ip
            _fip = self.floating_ip_lookup(node)

            # get floating ip object
            _fip_obj = self.driver.ex_get_floating_ip(_fip)

            # detach ip from node
            self.driver.ex_detach_floating_ip_from_node(node, _fip_obj)

            # delete ip
            self.driver.ex_delete_floating_ip(_fip_obj)
        except OpenstackProviderError:
            self.logger.warning('Node %s does not have fip.' % node.name)
        except Exception as ex:
            self.logger.error(ex)
            raise OpenstackProviderError('Unable to detach FIP from %s' % node)
        finally:
            self.unset_driver()

    def create(self):
        """Create a node in openstack.

        This method will call the openstack provider create method. The
        provider class handles all interactions with the provider.
        """
        self.logger.info('Provisioning machines from %s', self.__class__)

        # ignore if count is given as provider parameter
        try:
            if self.provider_params.get('count', False):
                self.logger.warn('Count parameter is found for host %s '
                                 'Count is not supported with openstack_libcloud as provisioner and will be ignored.'
                                 % getattr(self.asset, 'name'))
        except KeyError:
            pass

        # determine hostname for the host
        hostname = self.provider_params.get('hostname', None)
        if not hostname:
            hostname = filter_host_name(getattr(self.asset, 'name')) + '_%s' % gen_random_str(5)

        _ip, _id = self._create(
            hostname,
            self.provider_params.get('image'),
            self.provider_params.get('flavor'),
            self.provider_params.get('networks'),
            self.provider_params.get('keypair'),
            self.provider_params.get('floating_ip_pool', None),
            self.provider_params.get('server_metadata', {})
        )

        return [dict(hostname=hostname, asset_id=_id, ip=_ip)]

    def delete(self):
        """Delete a node in openstack.

        This method will call the openstack provider delete method. The
        provider class handles all interactions with the provider.
        """
        self.logger.info('Tearing down machines from %s', self.__class__)
        # using hostname attribute of the asset to perform delete operation
        self._delete(getattr(self.asset, 'hostname', None))

    def validate(self):

        schema_validator(schema_data=self.build_profile(self.asset), schema_files=[self.__schema_file_path__])
