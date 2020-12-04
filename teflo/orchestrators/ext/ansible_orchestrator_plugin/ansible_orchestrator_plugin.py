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

    Teflo's ansible orchestrator plugin which contains all the necessary
    methods to process ansible actions defined within the scenario descriptor
    file.

    :copyright: (c) 2020 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import os
import time
from teflo.core import OrchestratorPlugin
from teflo.exceptions import TefloOrchestratorError, AnsibleServiceError
from teflo.helpers import schema_validator
from teflo.ansible_helpers import AnsibleService


class AnsibleOrchestratorPlugin(OrchestratorPlugin):
    """Ansible orchestrator Plugin.

    This class primary responsibility is for processing teflo actions.
    These actions for the ansible orchestrator plugin could be in the form of a
    playbook or module call.
    """
    __plugin_name__ = 'ansible'
    __schema_file_path__ = os.path.abspath(os.path.join(os.path.dirname(__file__), "files/schema.yml"))
    __schema_ext_path__ = os.path.abspath(os.path.join(os.path.dirname(__file__), "files/extensions.py"))

    def __init__(self, package):
        """Constructor.

        :param package: action resource
        :type package: object
        """
        super(AnsibleOrchestratorPlugin, self).__init__(package)

        self.options = getattr(package, 'ansible_options', None)
        self.galaxy_options = getattr(package, 'ansible_galaxy_options', None)
        self.playbook = getattr(package, 'ansible_playbook', None)
        self.script = getattr(package, 'ansible_script', None)
        self.shell = getattr(package, 'ansible_shell', None)
        self.all_hosts = getattr(package, 'all_hosts', [])

        # calling the method to do a backward compatibility check in case user is defining name field as a path for
        # script or playbook
        # TODO delete this if we want to remove backward compatibility for later releases
        self.backwards_compat_check()

        # ansible service object
        self.ans_service = AnsibleService(self.config, self.hosts, self.all_hosts,
                                          self.options, self.galaxy_options,
                                          concurrency=self.config['TASK_CONCURRENCY']['ORCHESTRATE'].lower())

    def backwards_compat_check(self):
        """ This method does the check if name field is a script/playbook path or name of the orchestrator task by
            checking is '/' i spresent in the string.
            If it is a path then it checks if ansible_script field is a boolean and is True . If so
            a new dictionary is created with key=name and the value= script path. This is then assigned to
            ansible_script.
            If the ansible_script is not present then it is understood that the path belongs to a playbook.
             a new dictionary is created with key=name and the value= playbook path. This is then assigned to
            ansible_playbook.
            """

        if os.sep in self.action_name:
            self.logger.warning('Using name field to provide ansible_script/ansible_playbook path')

            self.logger.debug('Joining current workspace %s to the ansible_script/playbook path %s'
                              % (self.workspace, self.action_name))
            new_item = {'name': os.path.join(self.workspace, self.action_name)}

            self.logger.debug('Converting ansible_script/playbook path to dictionary %s' % new_item)
            if isinstance(self.script, bool) and self.script:
                self.script = new_item
            elif not self.script:
                self.playbook = new_item
            else:
                raise TefloOrchestratorError('Error in defining the orchestrate name/ansible_script/ansible_playbook'
                                              ' fields')

    def validate(self):
        """Validate that script/playbook path is valid and exists."""

        # schema validation for ansible_orchestrate schema
        schema_validator(schema_data=self.build_profile(self.action), schema_files=[self.__schema_file_path__],
                         schema_ext_files=[self.__schema_ext_path__])

        # verifying when script or playbook is present in the orchestrate task, the name key provides a path that exist
        if self.script:
            if os.path.exists(self.script.get('name').split(' ', 1)[0]):
                self.logger.debug('Found Action resource script %s' % self.script.get('name'))
            else:
                raise TefloOrchestratorError('Cannot find Action resource script %s' % self.script.get('name'))
        elif self.playbook:
            if os.path.exists(self.playbook.get('name').split(' ', 1)[0]):
                self.logger.debug('Found Action resource playbook %s' % self.playbook.get('name'))
            else:
                raise TefloOrchestratorError('Cannot find Action resource playbook %s' % self.playbook.get('name'))

    def __playbook__(self):
        self.logger.info('Executing playbook:')
        results = self.ans_service.run_playbook(self.playbook)
        if results[0] != 0:
            raise TefloOrchestratorError('Playbook %s failed to run successfully!' % self.playbook['name'])
        else:
            self.logger.info('Successfully completed playbook : %s' % self.playbook['name'])

    def __script__(self):
        self.logger.info('Executing script:')

        result = self.ans_service.run_script_playbook(self.script)
        if result['rc'] != 0:
            raise TefloOrchestratorError('Script %s failed. Host=%s rc=%d Error: %s'
                                          % (self.script['name'], result['host'], result['rc'], result['err']))
        else:
            self.logger.info('Successfully completed script : %s' % self.script['name'])

    def __shell__(self):
        self.logger.info('Executing shell command:')
        for shell in self.shell:
            result = self.ans_service.run_shell_playbook(shell)
            if result['rc'] != 0:
                raise TefloOrchestratorError('Command %s failed. Host=%s rc=%d Error: %s'
                                               % (shell['command'], result['host'], result['rc'], result['err']))
            else:
                self.logger.info('Successfully completed command : %s' % shell['command'])

    def run(self):
        """Run method for orchestrator.
        """
        # Orchestrate supports only one action_types( playbook, script or shell) per task
        # if more than one action types are declared then the first action_type found will be executed

        flag = 0
        res = self.action.status
        for item in ['playbook', 'script', 'shell']:
            # Orchestrate supports only one action_types( playbook, script or shell) per task
            # if more than one action types are declared then the first action_type found will be executed
            if getattr(self, item):
                flag += 1
                # Download ansible roles (if applicable)
                if flag == 1:
                    try:
                        self.ans_service.download_roles()
                    except (TefloOrchestratorError, AnsibleServiceError):
                        if 'retry' in self.galaxy_options and self.galaxy_options['retry']:
                            self.logger.Info("Download failed.  Sleeping 5 seconds and \
                                              trying again")
                            time.sleep(5)
                            self.ans_service.download_roles()

                    try:
                        getattr(self, '__%s__' % item)()
                        # If every script/playbook/shell command within the each orchestrate has passed,
                        # mark that task as successful
                        self.logger.debug("Successful completion of orchestrate task %s with return value %s"
                                          % (self.action_name, res))
                        res = 0
                    except (TefloOrchestratorError, AnsibleServiceError, Exception) as e:
                        res = 1
                        self.logger.error("Orchestration failed : %s" % e)
                        break
                    finally:
                        # get ansible logs as needed
                        # providing folder_name as 'ansible_orchestrator' so all ansible logs wil be under this folder
                        self.ans_service.alog_update(folder_name='ansible_orchestrator')
                else:
                    self.logger.warning('Found more than one action types (ansible_playbook, ansible_script ,'
                                        'ansible_shell )in the orchestrate task, only the first found'
                                        ' action type was executed, the rest are skipped.')
                    break
        return res
