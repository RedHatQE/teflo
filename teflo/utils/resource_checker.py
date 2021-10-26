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
    teflo.utils.resource_checker

    Module containing classes and functions for  validating services and other resources before running the teflo
    scenario

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import urllib3
import json
import time
import warnings
import cachetclient.cachet as cachet
from logging import getLogger
from teflo.exceptions import TefloError, AnsibleServiceError
from teflo.ansible_helpers import AnsibleService
from ..helpers import StatusPageHelper

LOG = getLogger(__name__)


class ResourceChecker(object):

    def __init__(self, scenario, config):
        """Constructor.

        :param scenario: teflo scenario object
        :type scenario: object
        :param config: scenario config
        :type config: object
        """
        self.scenario = scenario
        self.config = config

    def validate_resources(self):

        if getattr(self.scenario, 'resource_check').get('monitored_services', None) and \
                self.config['RESOURCE_CHECK_ENDPOINT']:
            # Verify dependency check components are supported/valid
            # TODO Update the link after the link to the proxy server is finalized
            if not self.config['RESOURCE_CHECK_ENDPOINT'].__contains__("https://internal.status.redhat.com/"):
                self.__check_service_statuspage()
            else:
                self.__check_service()
        if getattr(self.scenario, 'resource_check').get('playbook', None) or \
                getattr(self.scenario, 'resource_check').get('script', None):
            self.__check_custom_resource()

    def __check_custom_resource(self):
        # method to run playbook or scripts as a part of resource validation on local hosts before the scenario
        # provisioning is started

        # creating ansible service class object
        self.ans_service = AnsibleService(self.config, hosts=['localhost'], all_hosts=[], ansible_options=None)
        LOG.info("Running validation using user provided playbook/scripts")
        for type in ['playbook', 'script']:
            if not getattr(self.scenario, 'resource_check').get(type, None):
                continue
            for item in getattr(self.scenario, 'resource_check').get(type):
                status = 0
                self.ans_service.options = item.get('ansible_options', None)
                self.ans_service.galaxy_options = item.get('ansible_galaxy_options', None)

                # downloading ansible_roles
                try:
                    self.ans_service.download_roles()
                except (TefloError, AnsibleServiceError):
                    if 'retry' in self.ans_service.galaxy_options and self.ans_service.galaxy_options['retry']:
                        LOG.info("Download failed.  Sleeping 5 seconds and \
                                          trying again")
                        time.sleep(5)
                        self.ans_service.download_roles()

                error_msg = ''
                try:
                    if type == 'script':
                        # running the script
                        result = self.ans_service.run_script_playbook(item)
                        if result['rc'] != 0:
                            status = 1
                            LOG.error('Script %s failed with return code %s and error %s' %
                                      (item['name'], result['rc'], result['err']))
                            error_msg = result['err']
                    else:
                        # running the playbook
                        result = self.ans_service.run_playbook(item)
                        if result[0] != 0:
                            status = 1
                            error_msg = result[1]

                    if status == 1:
                        raise TefloError("Failed to run validation playbook/script %s. ERROR: %s" %
                                          (item['name'], error_msg))
                    else:
                        LOG.info("Successfully completed resource_check validation for playbook/script: %s",
                                  item['name'])
                except TefloError:
                    raise TefloError("Failed to run resource_check validation for playbook/script. ERROR: %s"
                                      % error_msg)

    def __check_service_statuspage(self):
        """
        External Component Dependency Check
        Throws exception if all components are not UP
        """
        LOG.info('Running external resource validation')

        component_names = getattr(self.scenario, 'resource_check').get('monitored_services', None)
        LOG.info(' DEPENDENCY CHECK '.center(64, '-'))
        comp_valid = True
        all_valid = True
        for comp in component_names:
            comp_valid = True
            # TODO Add the default proxy server link here for statuspage.io
            statuspage = StatusPageHelper(proxyserver_url=self.config["RESOURCE_CHECK_ENDPOINT"])
            for attempts in range(1, 6):
                info = statuspage.get_info()
                service_entry = info.get(comp)
                if service_entry is None:
                    LOG.info('{:>40} {:<9} - Can\'t Find Service{}'.format(
                            comp.upper(), 'From Database', attempts))
                    comp_valid = False
                    all_valid = comp_valid and all_valid
                else:
                    LOG.info('{:>40} {:<9} - Attempts {}'.format(
                        comp.upper(), ': UP' if service_entry.get("status") == "operational" else ': DOWN', attempts))
                    all_valid = comp_valid and all_valid
                    break

        if not all_valid:
            LOG.error("ERROR: Not all external resources are available or valid. Not running scenario")
            raise TefloError('Scenario %s will not be run! Not all external resources are available or valid' %
                                getattr(self.scenario, 'name'))

    def __check_service(self):
        """
        External Component Dependency Check
        Throws exception if all components are not UP

        :param scenario: teflo scenario object
        :param config: teflo config object
        """

        # External Dependency Check
        # Available components to check ci-rhos, zabbix-sysops, brew, covscan
        #                             polarion, rpmdiff, umb, errata, rdo-cloud
        #                             gerrit

        # Verify dependency check components are supported/valid then
        # Check status (UP/DOWN)
        # Only check if dependency check endpoint set and components given
        # Else it is ignored

        LOG.info('Running external resource validation')
        if self.config['RESOURCE_CHECK_ENDPOINT']:
            endpoint = self.config['RESOURCE_CHECK_ENDPOINT']
            ext_resources_avail = True
            # component_names = self.scenario.resource_check['service']
            component_names = getattr(self.scenario, 'resource_check').get('monitored_services', None)
            urllib3.disable_warnings()
            components = cachet.Components(endpoint=endpoint, verify=False)
            LOG.info(' DEPENDENCY CHECK '.center(64, '-'))
            for comp in component_names:
                comp_resource_invalid = False
                comp_resource_avail = False
                for attempts in range(1, 6):
                    component_data = components.get(params={'name': comp})
                    if json.loads(component_data)['data']:
                        comp_status = json.loads(component_data)['data'][0]['status']
                        if comp_status == 4:
                            comp_resource_avail = False
                            time.sleep(30)
                            continue
                        else:
                            comp_resource_avail = True
                            break
                    else:
                        comp_resource_invalid = True
                if comp_resource_avail is not True or comp_resource_invalid is True:
                    ext_resources_avail = False
                if comp_resource_invalid:
                    LOG.info('{:>40} {:<9} - Attempts {}'.format(
                        comp.upper(), ': INVALID', attempts))
                else:
                    LOG.info('{:>40} {:<9} - Attempts {}'.format(
                        comp.upper(), ': UP' if comp_resource_avail else ': DOWN', attempts))
            warnings.resetwarnings()
            LOG.info(''.center(64, '-'))

            if ext_resources_avail is not True:
                LOG.error("ERROR: Not all external resources are available or valid. Not running scenario")
                raise TefloError('Scenario %s will not be run! Not all external resources are available or valid' %
                                  getattr(self.scenario, 'name'))
