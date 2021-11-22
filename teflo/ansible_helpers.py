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
    teflo.ansible_helpers

    Module containing helper classes and methods which will be used by the classes and methods in
    orchestrate and execute modules

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import collections
import os
import copy
import json
from string import Template
from logging import getLogger
from ruamel.yaml import YAML
from collections import namedtuple
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from shutil import copyfile
from ansible.config.manager import ConfigManager
from ._compat import string_types
from .helpers import ssh_retry, exec_local_cmd_pipe, DataInjector, get_ans_verbosity, is_host_localhost, file_mgmt, \
    gen_random_str, check_for_var_file
from .static.playbooks import GIT_CLONE_PLAYBOOK, SYNCHRONIZE_PLAYBOOK, \
    ADHOC_SHELL_PLAYBOOK, ADHOC_SCRIPT_PLAYBOOK
from .exceptions import AnsibleServiceError
from ansible.parsing.vault import VaultSecret
from .exceptions import AnsibleVaultError
from ._compat import RawConfigParser, VaultLib, ansible_ver, is_py2

LOG = getLogger(__name__)


class AnsibleController(object):
    """Ansible controller.

    The primary responsibility is for driving the execution of either modules
    or playbooks to configure/manage remote machines.
    """

    def __init__(self, inventory):
        """Constructor.

        Primarily used for initializing attributes used by module/playbook
        execution.

        :param inventory: inventory file
        """
        self.loader = DataLoader()
        self.ansible_inventory = inventory
        self.inventory = None
        self.variable_manager = None

        # module options
        self.module_options = namedtuple(
            'Options', ['connection',
                        'module_path',
                        'forks',
                        'become',
                        'become_method',
                        'become_user',
                        'check',
                        'remote_user',
                        'private_key_file',
                        'diff']
        )

    def set_inventory(self):
        """Create the ansible inventory object with the supplied inventory."""
        self.variable_manager = VariableManager(loader=self.loader)
        self.inventory = InventoryManager(
            loader=self.loader,
            sources=self.ansible_inventory
        )
        self.variable_manager.set_inventory(self.inventory)

    @ssh_retry
    def run_module(self, module, logger, script=None, run_options={},
                   extra_args=None, extra_vars=None, ans_verbosity=None):
        """

        :param module: Name of the ansible module to run.
        :type module: str
        :param logger: Logger object.
        :type logger: logger object
        :param script: Absolute path a script, if using the script module.
        :type script: str
        :param run_options: additional ansible run options
        :type run_options: dict
        :param extra_args: module arguments
        :type extra_args: str
        :param extra_vars: used to determine where to run the module against
        :type extra_vars: dict
        :param ans_verbosity: verbosity to use for the ansible call.
        :type ans_verbosity: str
        :return: A tuple (rc, sterr)
        """

        if "localhost" in extra_vars and extra_vars["localhost"]:
            module_call = "ansible localhost -m %s" % (module)
        else:
            module_call = "ansible -i %s %s -m %s" % \
                          (self.ansible_inventory, extra_vars["hosts"], module)

        # add extra arguments
        if module == "script" or module == "shell":
            if extra_args:
                module_call += " -a '%s %s'" % (script, extra_args)
            else:
                module_call += " -a '%s'" % script
        elif extra_args:
            module_call += " -a '%s'" % extra_args

        if run_options:
            for key in run_options:
                if key == "remote_user":
                    module_call += " --user %s" % run_options[key]
                elif key == "become":
                    if run_options[key]:
                        module_call += " --%s" % key
                elif key == "tags":
                    taglist = ','.join(run_options[key])
                    module_call += " --tags %s" % taglist
                else:
                    module_call += " --%s %s" % (key.replace('_', '-'), run_options[key])

        if ans_verbosity:
            module_call += " -%s" % ans_verbosity

        # Set the connection if localhost
        if "localhost" in extra_vars and extra_vars["localhost"]:
            module_call += " -c local"

        logger.debug(module_call)
        output = exec_local_cmd_pipe(module_call, logger)
        return output

    @ssh_retry
    def run_playbook(self, playbook, logger, extra_vars=None, run_options=None,
                     ans_verbosity=None, env_var=None):
        """Run an Ansible playbook.

        :param playbook: Playbook to call
        :type playbook: str
        :param extra_vars: Additional variables for playbook
        :type extra_vars: dict
        :param run_options: playbook run options
        :type run_options: dict
        :param ans_verbosity: ansible verbosity settings
        :param env_var: dict of env variables to be passed
        :type: env_var: dict
        :type ans_verbosity: str
        :return: A tuple (rc, sterr)
        """

        playbook_call = "ansible-playbook -i %s %s" % \
                        (self.ansible_inventory, playbook)
        if extra_vars is not None:
            for key in extra_vars:
                if not isinstance(extra_vars[key], string_types) and key != 'file':
                    extra_var_dict = dict()
                    extra_var_dict[key] = extra_vars[key]
                    playbook_call += ' -e "%s" ' % extra_var_dict
                elif key == "file":
                    # check to see if file is a list
                    if isinstance(extra_vars[key], list):
                        for item in extra_vars[key]:
                            playbook_call += ' -e "@%s" ' % item
                    else:
                        playbook_call += ' -e "@%s" ' % extra_vars[key]
                else:
                    playbook_call += " -e %s=\"'%s'\"" % (key, extra_vars[key])

        if run_options:
            for key in run_options:
                if key == "remote_user":
                    playbook_call += " --user %s" % run_options[key]
                elif key == "become":
                    if run_options[key]:
                        playbook_call += " --%s" % key
                elif key == "tags":
                    taglist = ','.join(run_options[key])
                    playbook_call += " --tags %s" % taglist
                elif key == "skip_tags":
                    taglist = ','.join(run_options[key])
                    playbook_call += " --skip-tags %s" % taglist
                elif key == "vault-password-file":
                    taglist = ','.join(run_options[key])
                    playbook_call += " --vault-password-file %s" % taglist
                else:
                    playbook_call += " --%s %s" % (key.replace('_', '-'), run_options[key])

        if ans_verbosity:
            playbook_call += " -%s" % ans_verbosity

        logger.debug(playbook_call)
        output = exec_local_cmd_pipe(playbook_call, logger, env_var=env_var)
        return output


class AnsibleService(object):

    user_run_vals = ["become", "become_method", "become_user", "remote_user",
                     "connection", "forks", "tags", 'skip_tags', 'vault-password-file']

    playbook_name = Template("cbn_execute_$type$uid.yml")

    def __init__(self, config, hosts, all_hosts, ansible_options, galaxy_options=None, concurrency=None, env_var={}):
        self.hosts = hosts
        self.all_hosts = all_hosts
        self.config = config
        self.options = ansible_options
        self.galaxy_options = galaxy_options
        self.injector = DataInjector(self.all_hosts)
        self.logger = LOG
        # uuid that we can append to playbook and results file in case
        # execute/orchestrate tasks run concurrently
        self.uid = gen_random_str(5)
        # setting the env variables for ansible with the os.environ
        self.env_var = os.environ
        if env_var:
            # Adding any user defined env var to the os.environ
            self.env_var = self.env_var.update(env_var)

        self.ans_log_path = ''

        # Setting ANSIBLE_LOG_PATH env variable when running actions concurrently, so each action logs gets
        # collected in a separate file
        if concurrency == 'true':
            ans_log = 'ansible_' + self.uid + '.log'
            self.ans_log_path = os.path.join(self.config['WORKSPACE'], ans_log)
            self.env_var.update({'ANSIBLE_LOG_PATH': self.ans_log_path})

        # passing the teflo's inventory directory to the Ansible Controller
        self.ans_controller = AnsibleController(os.path.abspath(self.config['INVENTORY_FOLDER']))

        # pass the uid as an extra variable to the playbooks so they can save
        # output uniquely to disk in case of concurrent execution
        self.ans_extra_vars = collections.OrderedDict(hosts=self.create_inv_group(), uuid=self.uid)
        self.ans_verbosity = get_ans_verbosity(self.config)

    def create_inv_group(self):
        """This method creates the host group for the action object to be passed as extra_vars"""

        # defines the custom group to run the play against
        # This is what handles the core of the logic now to pass
        # to the ansible-playbook command the -e hosts=<hosts>
        group = 'hosts'
        if self.hosts:
            join = False
            for host in self.hosts:
                if isinstance(host, string_types):
                    if len(self.hosts) > 1:
                        if join:
                            group += ', %s' % host
                        else:
                            group = host
                            join = True
                        continue
                    else:
                        group = host
                        continue
                else:
                    # If the hosts are Asset objects
                    if len(self.hosts) > 1:
                        if join:
                            group += ', %s' % host.name
                        else:
                            group = host.name
                            join = True
                        continue
                    else:
                        group = host.name
                    continue
        return group

    def build_ans_extra_args(self, attr):
        """Build ansible extra arguments for ansible ad hoc commands.
        ansible extra_args are the parameters that are needed by the ansible modules (script and shell)
        They can be provided in two ways:

        method 1
        as a part of ansible_options in the SDF

        method 2
        as a part of the script/shell dictionary

        :param attr: key/values defined by task input
        :type attr: dict
        :return: extra args
        :rtype: str
        """
        # here the assumption is the extra_args can contain the params used by ansible shell/script module and/or
        # The parameters provided for the shell command/script to run

        # list of params taken by the ansible script and shell module
        params = ['chdir', 'creates', 'decrypt', 'executable', 'removes', 'warn', 'stdin', 'stdin_add_newline']

        extra_args = "args:"
        for item in params:
            if item in attr and attr[item]:
                extra_args += '\n        %s: %s' % (item, attr[item])

        if self.options and 'extra_args' in self.options and self.options['extra_args']:
            self.logger.warning('Deprecated way of providing extra_args under ansible_options is being used')

            # inject extra_args string with any data that might require data pass-thru
            self.options['extra_args'] = self.injector.inject(self.options['extra_args'])

            arg_list = self.options['extra_args'].split()
            for item in arg_list:
                if '=' in item:
                    param, val = item.split('=')
                    if param in params:
                        extra_args += '\n        %s: %s' % (param, val)
                    else:
                        attr['name'] = attr['name'] + ' ' + item
                        self.logger.debug('Using deprecated way of assigning script params using extra args with in '
                                          'ansible_options. Appending it to the script name to be used as '
                                          'script params %s' % attr['name'])
                else:
                    attr['name'] = attr['name'] + ' ' + item
                    self.logger.debug('Using deprecated way of assigning script params using extra args with in '
                                      'ansible_options. Appending it to the script name to be used as '
                                      'script params %s' % attr['name'])
        return extra_args

    def build_run_options(self):
        """Build ansible run options for ansible ad hoc commands.

        :return: run_options
        :rtype: dict

        """

        run_options = {}

        # override ansible options (user passed in vals for specific action)
        for val in self.user_run_vals:
            if self.options and val in self.options and self.options[val]:
                run_options[val] = self.options[val]
        self.logger.info("Ansible options used: " + str(run_options))

        return run_options

    def convert_run_options(self, run_options, block_options=False):
        """Convert run options dict to string for task in playbook.

        :param run_options: run options dictionary
        :type run_options: dict
        :param block_options: whether building options in an ansible block
        :type block_options: bool
        :return: run options string
        :rtype: str

        """
        run_options_str = ''

        first = True
        for opt in run_options:
            if first:
                run_options_str += '%s: %s\n' % (opt, run_options[opt])
                first = False
            else:
                if block_options:
                    run_options_str += '          %s: %s\n' % (opt, run_options[opt])
                else:
                    run_options_str += '      %s: %s\n' % (opt, run_options[opt])

        return run_options_str

    def build_extra_vars(self):
        """Build ansible extra vars for ansible ad hoc commands.

        :return: extra args
        :rtype: str
        """

        extra_vars = {}
        if self.options and 'extra_vars' in self.options and self.options['extra_vars']:
            extra_vars.update(self.options['extra_vars'])
            # inject data into extra_vars
            extra_vars = self.injector.inject_dictionary(extra_vars)
        extra_vars['localhost'] = False
        if self.hosts:
            for h in self.hosts:
                if not isinstance(h, string_types) and hasattr(h, 'ip_address'):
                    if is_host_localhost(h.ip_address):
                        extra_vars['localhost'] = True
                elif isinstance(h, string_types) and h == 'localhost':
                    extra_vars['localhost'] = True
        # Looking for all the variable files that teflo finds and add them as extra_vars for the ansible playbooks
        if self.config.get('ANSIBLE_EXTRA_VARS_FILES') and \
                self.config.get('ANSIBLE_EXTRA_VARS_FILES').lower() == 'true':
            var_files_list = self.config.get('EXTRA_VARS_FILES')
            file = extra_vars.get('file')
            if file:
                if not isinstance(file, str):
                    extra_vars['file'].extend(var_files_list)
                else:
                    var_files_list.append(file)
                    extra_vars['file'] = var_files_list
            else:
                extra_vars['file'] = var_files_list

        return extra_vars

    def evaluate_string(self, command):
        """Perform string evaluation by injecting data.

        :param command: command to inject data into
        :type command: str
        :return: updated command
        :rtype: str
        """
        return self.injector.inject(command)

    def update_playbook_str(self, playbook_str, search_str, replace_str):
        return playbook_str.replace(search_str, replace_str)

    @staticmethod
    def create_playbook(playbook, playbook_str):
        """Create the playbook on disk from string.

        :param playbook: playbook name
        :type playbook: str
        :param playbook_str: playbook content
        :type playbook_str: str
        """
        yaml = YAML()
        yaml.default_flow_style = False
        with open(playbook, 'w') as f:
            yaml.dump(yaml.load(playbook_str), f)

    def download_roles(self):
        """Download ansible roles and collections defined for the given action."""
        flag = 0

        if self.galaxy_options is None:
            return

        if 'role_file' in self.galaxy_options:
            flag += 1

            f = os.path.join(self.config['WORKSPACE'],
                             self.galaxy_options['role_file'])
            file_output = file_mgmt('r', f)
            if isinstance(file_output, list):
                cmd = 'ansible-galaxy role install -r %s' % f
                self.logger.info('Installing roles using req. file: %s' % f)
                results = exec_local_cmd_pipe(cmd, self.logger)
                if results[0] != 0:
                    raise AnsibleServiceError(
                        'A problem occurred while installing roles using req. file'
                        ' %s' % f)
                self.logger.info('Roles installed successfully from: %s!' % f)
            elif isinstance(file_output, dict):
                if 'roles' in file_output:
                    cmd = 'ansible-galaxy role install -r %s' % f
                    self.logger.info('Installing roles using req. file: %s' % f)
                    results = exec_local_cmd_pipe(cmd, self.logger)
                    if results[0] != 0:
                        raise AnsibleServiceError(
                            'A problem occurred while installing roles using req. file'
                            ' %s' % f)
                    self.logger.info('Roles installed successfully from: %s!' % f)
                if 'collections' in file_output:
                    cmd = 'ansible-galaxy collection install -r %s' % f
                    self.logger.info('Installing collections using req. file: %s' % f)
                    results = exec_local_cmd_pipe(cmd, self.logger)
                    if results[0] != 0:
                        raise AnsibleServiceError(
                            'A problem occurred while installing collections using req. file'
                            ' %s' % f)
                    self.logger.info('Collections installed successfully from: %s!' % f)

        if 'roles' in self.galaxy_options:
            if flag >= 1:
                self.logger.warning('FYI roles were already installed using a'
                                    ' requirements file. Problems may occur.')

            for item in self.galaxy_options['roles']:
                cmd = 'ansible-galaxy install %s' % item
                results = exec_local_cmd_pipe(cmd, self.logger)

                if results[0] != 0:
                    raise AnsibleServiceError(
                        'A problem occurred while installing role: %s' % item
                    )
                self.logger.info('Role: %s successfully installed!' % item)

        if 'collections' in self.galaxy_options:
            if flag >= 1:
                self.logger.warning('FYI collections were already installed using a'
                                    ' requirements file. Problems may occur.')

            for item in self.galaxy_options['collections']:
                cmd = 'ansible-galaxy collection install %s' % item
                results = exec_local_cmd_pipe(cmd, self.logger)

                if results[0] != 0:
                    raise AnsibleServiceError(
                        'A problem occurred while installing collection: %s' % item
                    )
                self.logger.info('Collection: %s successfully installed!' % item)

    def get_default_config(self, key=None):
        """getting the default configuration defined by ansible.cfg
        (Uses default values if there is no ansible.cfg).

        :param key: get a value of a specific key of the ansible.cfg file
        :type key: str

        :return: key/values of the default ansible configuration or
                 a specifc value of the config
        :rtype: dict if key not defined or string if defined
        """
        returndict = {}
        acm = ConfigManager()
        a_settings = acm.data.get_settings()
        if key:
            for setting in a_settings:
                if setting.name == key:
                    return setting.value
            return None
        else:
            for setting in a_settings:
                if setting.name == "CONFIG_FILE":
                    self.logger.debug("Using %s for default configuration" % setting.value)
                elif setting.name == "DEFAULT_BECOME":
                    returndict["become"] = setting.value
                elif setting.name == "DEFAULT_BECOME_METHOD":
                    returndict["become_method"] = setting.value
                elif setting.name == "DEFAULT_BECOME_USER":
                    returndict["become_user"] = setting.value
                elif setting.name == "DEFAULT_REMOTE_USER":
                    returndict["remote_user"] = setting.value
                elif setting.name == "DEFAULT_FORKS":
                    returndict["forks"] = setting.value
                elif setting.name == 'DEFAULT_TRANSPORT':
                    returndict["connection"] = setting.value
            return returndict

    def alog_update(self, folder_name=None):
        """move ansible logs to data folder/folder_name(if provided)
        :param folder_name: name of the folder under data folder to move the ansible logs
        :type folder_name: str
        """
        ans_logfile = self.ans_log_path if self.ans_log_path else self.get_default_config(key="DEFAULT_LOG_PATH")
        self.logger.debug("The ansible log file being used is : %s" % ans_logfile)
        if ans_logfile:
            if folder_name:
                # Putting ansible logs in specific folders
                log_folder = 'logs/' + folder_name
                if not os.path.isdir(os.path.join(self.config['DATA_FOLDER'], log_folder)):
                    os.makedirs(os.path.abspath(os.path.join(self.config['DATA_FOLDER'], log_folder)))
                dest = os.path.join(self.config['DATA_FOLDER'], log_folder, "ansible.log")
            else:
                dest = os.path.join(self.config['DATA_FOLDER'], 'logs', "ansible.log")
            # if user wishes to keep the ansible log copy the log file
            if os.path.isfile(dest) and not self.config["ANSIBLE_LOG_REMOVE"]:
                copyfile(ans_logfile, dest)
            # if user wants to delete the log file (default)
            elif os.path.isfile(dest):
                with open(dest, "a") as destfile:
                    with open(ans_logfile) as logfile:
                        for line in logfile:
                            destfile.write(line)
            else:
                copyfile(ans_logfile, dest)
            # remove ansible log (default)
            if os.path.isfile(ans_logfile) and self.config["ANSIBLE_LOG_REMOVE"]:
                os.remove(ans_logfile)
            self.logger.debug("ansible logging moved to: %s" % dest)

    def run_playbook(self, playbook, extra_vars=None, run_options=None):
        """Execute the playbook supplied."""

        if isinstance(playbook, dict):
            # This is when orchestrator/executor send the playbook dict
            playbook_name = playbook.get('name')
            # update extra vars
            self.ans_extra_vars.update(self.build_extra_vars())
            extra_vars = copy.deepcopy(self.ans_extra_vars)
            # build run options
            run_options = self.build_run_options()
        elif isinstance(playbook, str):
            playbook_name = playbook
        else:
            raise AnsibleServiceError('Playbook parameter can be a string or dictionary')

        self.logger.info('Executing playbook : %s' % playbook_name)

        # Calling ansible controller run playbook method
        results = self.ans_controller.run_playbook(
            playbook=playbook_name,
            logger=self.logger,
            extra_vars=extra_vars,
            run_options=run_options,
            ans_verbosity=self.ans_verbosity,
            env_var=self.env_var
        )
        return results

    def run_artifact_playbook(self, destination, artifacts):
        """Create playbook string for collecting artifacts"""

        # update and set extra vars
        self.ans_extra_vars.update(self.build_extra_vars())
        extra_vars = copy.deepcopy(self.ans_extra_vars)
        extra_vars['dest'] = destination
        extra_vars['artifacts'] = artifacts

        # dynamic playbook
        playbook = self.playbook_name.safe_substitute(type='synchronize_', uid=self.uid)

        # build run options
        run_options = self.build_run_options()
        run_options_str = self.convert_run_options(run_options)
        run_block_options_str = self.convert_run_options(run_options, block_options=True)

        # update dynamic playbook synchronize task with options
        playbook_str = self.update_playbook_str(SYNCHRONIZE_PLAYBOOK, "{{ options }}", run_options_str)

        # update dynamic playbook synchronize task with options in the block
        playbook_str = self.update_playbook_str(playbook_str, "{{ block_options }}", run_block_options_str)

        # create dynamic playbook
        self.create_playbook(playbook, playbook_str)

        # run playbook
        results = self.run_playbook(playbook, extra_vars)

        # remove dynamic playbook
        os.remove(playbook)

        return results

    def run_shell_playbook(self, shell):
        """Execute the shell command supplied."""

        # dynamic playbook
        playbook = self.playbook_name.safe_substitute(type='shell_', uid=self.uid)

        shell['command'] = self.evaluate_string(shell['command'])

        self.logger.info('Executing shell command %s' % (shell['command']))

        extra_args = self.build_ans_extra_args(shell)

        # build run options
        run_options = self.build_run_options()
        run_options_str = self.convert_run_options(run_options)

        # update extra vars
        self.ans_extra_vars.update(self.build_extra_vars())

        # set playbook variables
        extra_vars = copy.deepcopy(self.ans_extra_vars)
        extra_vars['xcmd'] = shell['command']

        # update dynamic playbook shell task with extra args
        playbook_str = self.update_playbook_str(ADHOC_SHELL_PLAYBOOK, "{{ args }}", extra_args)

        # update dynamic playbook shell task with options
        playbook_str = self.update_playbook_str(playbook_str, "{{ options }}", run_options_str)

        # create dynamic playbook
        self.create_playbook(playbook, playbook_str)

        results = self.run_playbook(playbook, extra_vars)

        # remove dynamic playbook
        os.remove(playbook)

        # Get results from the json file and build results in sh_results
        try:
            sh_results = dict()
            with open('shell-results-' + self.uid + '.json') as f:

                my_json = json.load(f)
                for item in my_json:
                    sh_results['host'] = item['host_name']
                    sh_results['rc'] = int(item['rc'])
                    sh_results['err'] = item['err']
        except (IOError, OSError) as ex:
            self.logger.error(ex)
            raise AnsibleServiceError('Failed to find the shell-results.json file '
                                      'which means there was an uncaught failure running '
                                      'the dynamic playbook. Please enable verbose Ansible '
                                      'logging in the teflo.cfg file and try again.')

        # remove Shell Results file
        os.remove('shell-results-' + self.uid + '.json')

        return sh_results

    def run_git_playbook(self, git_dict):
        """Clone git repositories.

        This method takes a string formatted playbook, writes it to disk,
        provides the git details to the playbook and runs it. The result is
        on the targeted remote hosts will have the defined gits cloned for
        test execution.
        """

        # dynamic playbook
        playbook = self.playbook_name.safe_substitute(type='clone_', uid=self.uid)

        self.logger.info('Cloning git repositories.')

        # set playbook variables
        extra_vars = copy.deepcopy(self.ans_extra_vars)
        extra_vars['gits'] = git_dict

        # build run options
        run_options = self.build_run_options()
        run_options_str = self.convert_run_options(run_options)

        # update dynamic playbook git task with options
        playbook_str = self.update_playbook_str(GIT_CLONE_PLAYBOOK, "{{ options }}", run_options_str)

        # create dynamic playbook
        self.create_playbook(playbook, playbook_str)

        # run playbook
        results = self.run_playbook(playbook, extra_vars)

        # remove dynamic playbook
        os.remove(playbook)

        return results[0]

    def run_script_playbook(self, script):
        """Execute the script supplied."""

        # dynamic playbook
        playbook = self.playbook_name.safe_substitute(type='script_', uid=self.uid)

        self.logger.info('Executing script %s:' % script['name'])

        extra_args = self.build_ans_extra_args(script)

        # update extra vars
        self.ans_extra_vars.update(self.build_extra_vars())

        # build run options
        run_options = self.build_run_options()
        run_options_str = self.convert_run_options(run_options)

        # set playbook variables
        extra_vars = copy.deepcopy(self.ans_extra_vars)
        extra_vars['xscript'] = script['name']

        # update dynamic playbook shell task with args
        playbook_str = self.update_playbook_str(ADHOC_SCRIPT_PLAYBOOK, "{{ args }}", extra_args)

        # update dynamic playbook shell task with options
        playbook_str = self.update_playbook_str(playbook_str, "{{ options }}", run_options_str)

        # create dynamic playbook
        self.create_playbook(playbook, playbook_str)

        # run playbook
        results = self.run_playbook(playbook, extra_vars)

        # remove dynamic playbook
        os.remove(playbook)

        # Get results from the json file and build results in script_results
        script_results = dict()
        try:
            with open('script-results-' + self.uid + '.json') as f:
                my_json = json.load(f)

                for item in my_json:
                    script_results['host'] = item['host_name']
                    script_results['rc'] = int(item['rc'])
                    script_results['err'] = item['err']
        except (IOError, OSError) as ex:
            self.logger.error(ex)
            raise AnsibleServiceError('Failed to find the script-results.json file '
                                      'which means there was an uncaught failure running '
                                      'the dynamic playbook. Please enable verbose Ansible '
                                      'logging in the teflo.cfg file and try again.')

        # remove Script Results file
        os.remove('script-results-' + self.uid + '.json')
        return script_results


class AnsibleCredentialManager(object):
    """Ansible Credential Manager

    The primary responsibility is managing all credential related stuff for ansible
    """

    def __init__(self, config):
        super(AnsibleCredentialManager, self).__init__()
        self.__config = config

    @property
    def config(self):
        """Config object
        :return: Config object
        """
        return self.__config

    @config.setter
    def config(self, value):
        raise ValueError("you cannot set the Config object")

    def populate_credetials(self, config, credentials_path, vaultpass):
        if ansible_ver < 4 or is_py2:
            secret = [("default", VaultSecret(bytes(vaultpass.encode('utf-8'))))]
            vault = VaultLib(secret)
            cred = open(credentials_path, "rb").read()
            cred = vault.decrypt(cred)
            ret_str = ""
            for asc in cred:
                ret_str += asc
            tmpf = open("tmppass", 'w')
            tmpf.write(ret_str)
            tmpf.close()
            tmpparser = RawConfigParser()
            tmpparser.read("tmppass")
            os.remove("tmppass")
        else:
            secret = [("default", VaultSecret(bytes(vaultpass, "utf-8")))]
            vault = VaultLib(secret)
            cred = open(credentials_path, "rb").read()
            cred = vault.decrypt(cred)
            ret_str = ""
            for asc in cred:
                ret_str += (chr(int(asc)))
            tmpparser = RawConfigParser()
            tmpparser.read_string(ret_str)
        config.__set_credentials__(parser=tmpparser)

    def populate_teflo_cfg_credentials(self):
        if not self.__config.get("CREDENTIALS") and self.__config.get("CREDENTIAL_PATH"):
            if os.getenv("VAULTPASS"):
                vaultpass = os.getenv("VAULTPASS")
            else:
                vaultpass = self.__config.get("VAULTPASS", "")
            if vaultpass == "":
                raise AnsibleVaultError('No vaultpass was found, please set the \
                vaultpass in teflo.cfg or in environment variable.')
            self.populate_credetials(self.__config, self.__config["CREDENTIAL_PATH"], vaultpass)
