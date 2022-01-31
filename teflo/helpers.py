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
    teflo.helpers

    Module containing classes and functions which are generic and used
    throughout the code base.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from copy import deepcopy
import inspect
import json
import os
import pkgutil
import random
import re
import socket
import string
import subprocess
import sys

import time
import click
from logging import getLogger
import fnmatch
import stat
import jinja2
import requests
from paramiko import RSAKey
from ruamel.yaml.comments import CommentedMap as OrderedDict
from collections import OrderedDict
from ruamel.yaml import YAML
import yaml
from paramiko.ssh_exception import SSHException
from ._compat import string_types
from .constants import PROVISIONERS, RULE_HOST_NAMING, TASKLIST, NOTIFYSTATES
from .exceptions import TefloError, HelpersError
from pykwalify.core import Core
from pykwalify.errors import CoreError, SchemaError
from xml.etree import cElementTree as ET
import socket
from ssh.session import Session
from ssh.key import import_privkey_file
from ssh import options
from ssh.exceptions import SSHError, HostKeyNotVerifiable, AuthenticationError, ConnectFailed, ConnectionLost
import pkg_resources
from ruamel.yaml import comments
LOG = getLogger(__name__)

# sentinel
_missing = object()


def get_core_tasks_classes():
    """
    Go through all modules within teflo.tasks package and return
    the list of all tasks classes within it. All tasks within the teflo.tasks
    module are considered valid task class to be added into the pipeline.
    :return: List of all valid tasks classes
    """
    from .core import TefloTask
    from . import tasks

    # all task classes must
    prefix = tasks.__name__ + "."

    tasks_list = []

    # Run through each module within tasks and take the list of
    # classes that are subclass of TefloTask but not TefloTask itself.
    # When you import a class within a module, it becames a member of
    # that class
    for importer, modname, ispkg in pkgutil.iter_modules(tasks.__path__, prefix):
        if str(modname).endswith('.ext'):
            continue
        clsmembers = inspect.getmembers(sys.modules[modname], inspect.isclass)
        for clsname, clsmember in clsmembers:
            if (clsmember is not TefloTask) and issubclass(clsmember, TefloTask):
                tasks_list.append(clsmember)

    return tasks_list


# Using entry point to get the provisioners defined in teflo's setup.py file
def get_provisioners_plugin_classes():
    """Return all provisioner plugin classes discovered by teflo
    :return: The list of provisioner plugin classes
    """
    provisioner_plugin_dict = {}
    for entry_point in pkg_resources.iter_entry_points('provisioner_plugins'):
        provisioner_plugin_dict[entry_point.name] = entry_point.load()
    return provisioner_plugin_dict


def get_default_provisioner_plugin(provider=None):
    """
    Return provisioner plugin class based on the given provider class.
    If provider is None linchpin_wrapper plugin class is returned as the default
    provisioner class.
    :param provider: The provider class
    :return: The provisioner plugin class
    """

    if provider is None:
        return get_provisioner_plugin_class('linchpin')

    if provider is not None and hasattr(provider, '__provider_name__'):
        provisioners = PROVISIONERS[provider.__provider_name__]
    else:
        provisioners = PROVISIONERS[provider]

    if isinstance(provisioners, list):
        return get_provisioner_plugin_class(provisioners[0])
    else:
        return get_provisioner_plugin_class('linchpin')


def get_provisioners_plugins_list():
    """
    Returns a list of all the valid provisioner gateways.
    :return: list of provisioner gateways
    """

    valid_provisioners = []
    for provisioner_gateway_class in get_provisioners_plugin_classes().values():
        valid_provisioners.append(provisioner_gateway_class.__plugin_name__)
    return valid_provisioners


def get_provisioner_plugin_class(name):
    """Return the provisioner gateway class based on the __provisioner_name__ set
    within the class. See ~teflo.core.TefloPlugin for more information.
    :param name: The name of the provisioner
    :return: The provisioner gateway class
    """
    for provisioner in get_provisioners_plugin_classes().values():
        if provisioner.__plugin_name__.startswith(name):
            return provisioner


# Using entry point to get the providers from within teflo as well as the ones coming from the external plugins
def get_provider_plugin_classes():
    """Return all provider plugin classes discovered by teflo
    :return: The list of provider plugin classes
    """
    provider_plugin_dict = {}
    for entry_point in pkg_resources.iter_entry_points('provider_plugins'):
        provider_plugin_dict[entry_point.name] = entry_point.load()
    return provider_plugin_dict


def get_provider_plugin_class(name):
    """
    Return the provider class based on the __provider_name__ set within
    the class.
    :param name: the name of the provider
    :return: the provider class
    """
    for provider in get_provider_plugin_classes().values():
        if provider.__provider_name__ == name:
            return provider


def get_provider_plugin_list():
    """
    Return the list of provider class based on the __provider_name__ set within
    the class.
    :return: list of the the provider names
    """
    return [provider.__provider_name__ for provider in get_provider_plugin_classes().values()]


# Using entry point to get the orchestrators defined in teflo's setup.py file
def get_orchestrators_plugin_classes():
    """Return all orchestrator plugin classes discovered by teflo
    :return: The list of orchestrator plugin classes
    """
    orchestrator_plugin_dict = {}
    for entry_point in pkg_resources.iter_entry_points('orchestrator_plugins'):
        orchestrator_plugin_dict[entry_point.name] = entry_point.load()
    return orchestrator_plugin_dict.values()


def get_orchestrator_plugin_class(name):
    """Return the orchestrator class based on the __orchestrator_name__ set
    within the class.

    :param name: the name of the orchestrator
    :return: the orchestrator class
    """
    for orchestrator in get_orchestrators_plugin_classes():
        if orchestrator.__plugin_name__ == name:
            return orchestrator


def get_orchestrators_plugin_list():
    """Return a list of available orchestrators.

    :return: orchestrators
    """
    return [orchestrator.__plugin_name__ for orchestrator in
            get_orchestrators_plugin_classes()]


# Using entry point to get the executors defined in teflo's setup.py file
def get_executors_plugin_classes():
    """Return all executor plugin classes discovered by teflo
    :return: The list of executor plugin classes
    """
    executor_plugin_dict = {}
    for entry_point in pkg_resources.iter_entry_points('executor_plugins'):
        executor_plugin_dict[entry_point.name] = entry_point.load()
    return executor_plugin_dict.values()


def get_executor_plugin_class(name):
    """Return the executor class based on the __executor_name__ set
    within the class.

    :param name: the name of the executor
    :return: the executor class
    """
    for executor in get_executors_plugin_classes():
        if executor.__executor_name__ == name:
            return executor


def get_executors_plugin_list():
    """Return a list of available executors.

    :return: executors
    """
    return [executor.__executor_name__ for executor in
            get_executors_plugin_classes()]


# Using entry point to get the importers. These methods are being used to get the importer plugins external to teflo
def get_importers_plugin_classes():
    """Return all importer plugin classes discovered by teflo
    :return: The list of importer plugin classes
    """
    ext_plugin_dict = {}
    for entry_point in pkg_resources.iter_entry_points('importer_plugins'):
        ext_plugin_dict[entry_point.name] = entry_point.load()
    return ext_plugin_dict.values()


def get_default_importer_plugin_class(provider):
    """Return the importer class based on the provider name
    :param provider: The provider class
    :return: The importer plugin class
    """
    for plugin_class in get_importers_plugin_classes():
        if plugin_class.__plugin_name__.startswith(provider.__provider_name__):
            return plugin_class


def get_importers_plugin_list():
    """
    Returns a list of all the valid importer gateways.
    :return: list of importer plugin names
    """
    valid_reporters = []
    for reporter_plugin_class in get_importers_plugin_classes():
        valid_reporters.append(reporter_plugin_class.__plugin_name__)
    return valid_reporters


def get_importer_plugin_class(name):
    """Return the importer plugin class based on the __plugin_name__ set
    within the class.
    :param name: The name of the importer
    :return: The importer plugin class
    """
    for reporter in get_importers_plugin_classes():
        if reporter.__plugin_name__.startswith(name):
            return reporter


def is_provider_mapped_to_provisioner(provider, provisioner):
    """
    Given a provider and a provisioner, check if they are supported together.
    :param provider:
    :param provisioner:
    :return:
    """
    if hasattr(provider, '__provider_name__'):
        provider_name = provider.__provider_name__
    else:
        provider_name = provider
    for provider_key, prov_val in PROVISIONERS.items():
        if provider_name == provider_key:
            if isinstance(prov_val, list):
                for p in prov_val:
                    if p == provisioner:
                        return True
            else:
                if prov_val == provisioner:
                    return True
    return False


def get_notification_plugin_list():
    """Return a list of available notifications.

    :return: notifications
    """
    return [notifier.__plugin_name__ for notifier in
            get_notifiers_plugin_classes()]


def get_notifiers_plugin_classes():
    """Return all notification plugin classes discovered by teflo
    :return: The list of notification plugin classes
    """
    notifier_plugin_dict = {}
    for entry_point in pkg_resources.iter_entry_points('notification_plugins'):
        notifier_plugin_dict[entry_point.name] = entry_point.load()
    return notifier_plugin_dict.values()


def get_notifier_plugin_class(name):
    """
    Return the notification class based on the __plugin_name__ set within
    the class.
    :param name: the name of the notification
    :return: the notification class
    """
    for notification in get_notifiers_plugin_classes():
        if notification.__plugin_name__ == name or \
                notification.__plugin_name__.startswith(name):
            return notification


def schema_validator(schema_data, schema_files, schema_creds=None, schema_ext_files=None):
    """

    :param schema_data: the schema dictionary data
    :type dict
    :param schema_files: the yaml schema file for the plugins
    :type list of file paths
    :param schema_creds: optional dictionary creds
    :type dict
    :param schema_ext_files: optional list of extension file paths
    :type: list of file paths
    :return:
    """

    schema = {}

    if schema_creds:
        schema = {k: v for k, v in schema_creds.items() if k != 'name'}
        schema.update({k: v for k, v in schema_data.items() if k != 'credential'})
    else:
        schema.update({k: v for k, v in schema_data.items() if k != 'credential'})
        creds = {k: v for k, v in schema_data.items() if k == 'credential'}
        if creds:
            creds = dict(credential={x: y for k, v in creds.items() for x, y in v.items() if x != 'name'})
            schema.update(creds)

    c = Core(source_data=schema,
             schema_files=schema_files,
             extensions=schema_ext_files)

    try:
        c.validate(raise_exception=True)
    except (CoreError, SchemaError) as ex:
        LOG.error(ex.msg)
        raise


def gen_random_str(char_num=8):
    """
    Generate a string with a specific number of characters, defined
    by `char_num`.

    :param char_num: the number of characters for the random string
    :return: random string
    """
    return ''.join(random.SystemRandom().
                   choice(string.ascii_lowercase + string.digits) for
                   _ in range(char_num))


def file_mgmt(operation, file_path, content=None, cfg_parser=None):
    """A generic function to manage files (read/write).

    :param operation: File operation type to perform
    :type operation: str
    :param file_path: File name including path
    :type file_path: str
    :param content: Data to write to a file
    :type content: object
    :param cfg_parser: Config parser object (Only needed if the file being
        processed is a configuration file parser language)
    :type cfg_parser: bool
    :return: Data that was read from a file
    """
    # to maintain the sequence in the results.yml file with ruamel
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.representer.ignore_aliases = lambda *data: True
    yaml.Representer.add_representer(OrderedDict, yaml.Representer.represent_dict)

    # Determine file extension
    file_ext = os.path.splitext(file_path)[-1]

    if operation in ['r', 'read']:
        # Read
        if os.path.exists(file_path):
            if file_ext == ".json":
                # json
                with open(file_path) as f_raw:
                    return json.load(f_raw)
            elif file_ext in ['.yaml', '.yml']:
                # yaml
                with open(file_path) as f_raw:
                    return yaml.load(f_raw)
            else:
                # text
                with open(file_path) as f_raw:
                    if cfg_parser is not None:
                        # Config parser file
                        return cfg_parser.readfp(f_raw)
                    else:
                        # lets check if it is json
                        data = f_raw.read()
                        try:
                            return json.load(data)
                        except Exception:
                            # it wasn't json, lets try yaml
                            try:
                                return yaml.load(data)
                            except Exception:
                                # it wasn't yaml, lets just return pure string
                                return data
        else:
            raise IOError("%s file not found!" % file_path)
    elif operation in ['w', 'write']:
        # Write
        mode = 'w+' if os.path.exists(file_path) else 'w'
        if file_ext == ".json":
            # json
            with open(file_path, mode) as f_raw:
                json.dump(content, f_raw, indent=4, sort_keys=True)
        elif file_ext in ['.yaml', '.yml']:
            # yaml
            with open(file_path, mode) as f_raw:
                yaml.dump(content, f_raw)
        else:
            # text
            with open(file_path, mode) as f_raw:
                if cfg_parser is not None:
                    # Config parser file
                    cfg_parser.write(f_raw)
                else:
                    f_raw.write(content)
    elif operation in ['d', 'delete']:
        if os.path.exists(file_path):
            os.unlink(file_path)
    else:
        raise HelpersError("Unknown file operation: %s." % operation)


def is_url_valid(url):
    """Check if a url is valid.

    :param url: URL path.
    :type url: str
    :return: True if url exists or false if url does not exist.
    :rtype: bool
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.HTTPError as ex:
        LOG.error(ex)
        return False
    return True


def template_render(filepath, env_dict, toggle_jinja_include=False):
    """
    A function to do jinja templating given a file and a dictionary of key/vars

    :param filepath: path to a file
    :param env_dict: dictionary of key/values used for data substitution
    :return: stream of data with the templating complete
    :rtype: data stream
    """
    path, filename = os.path.split(filepath)
    if toggle_jinja_include:
        return jinja2.Environment(loader=jinja2.FileSystemLoader(
            path), lstrip_blocks=True, trim_blocks=False).get_template(filename).render(env_dict)
    else:
        return jinja2.Environment(loader=jinja2.FileSystemLoader(
            path), lstrip_blocks=True, trim_blocks=True).get_template(filename).render(env_dict)


def exec_local_cmd(cmd, env_var=None):
    """Execute command locally.
    :param cmd: command to run
    :type cmd: str
    :param env_var: a dictionary of environmental variables to pass to the subprocess
    :type env_var: dictionary
    """
    # updating passed env variables with os env variables
    if env_var:
        env_var.update(os.environ)
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env_var
    )
    output = proc.communicate()
    return proc.returncode, output[0].decode('utf-8'), output[1].decode('utf-8')


def exec_local_cmd_pipe(cmd, logger, env_var=None):
    """Execute command locally, and pipe output in real time.

    :param cmd: command to run
    :type cmd: str
    :param env_var: a dictionary of environmental variables to pass to the subprocess
    :type env_var: dictionary
    :param logger: logger object
    :type logger: object
    :return: tuple of rc and error (if there was an error)
    """
    # updating passed env variables with os env variables
    if env_var:
        env_var.update(os.environ)
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=2,
        close_fds=True,
        env=env_var
    )
    while True:
        output, error = ("", "")
        if proc.poll is not None:
            output = proc.stdout.readline().decode('utf-8')
        if output == "" and error == "" and proc.poll() is not None:
            break
        if output:
            logger.info(output.strip())
    rc = proc.poll()
    if rc != 0:
        for line in proc.stderr:
            error = error + line.decode('utf-8')
    return rc, error


class CustomDict(dict):
    """Teflo dictionary to represent a resource from JSON or YAML.

    Initialized a data (loaded JSON or YAML) and creates a
    dict object with attributes to be accessed via dot notation
    or as a dict key-value.

    Deeper parameters within the data that contain its own data
    are also represented as Resource
    """

    def __init__(self, data={}):
        super(CustomDict, self).__init__(data)
        for key, value in data.items():
            if isinstance(value, dict):
                value = CustomDict(value)
            self[key] = value

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)


def filter_actions_on_failed_status(action_list):
    """
    Go through the action_list and return actions with failed status.
    If no action with failed status is found the original list is returned
    :return: List of actions based on its status
    """
    for index, action_item in enumerate(action_list):
        if action_item.status == 1:
            new_list = action_list[index:]
            return new_list
    return action_list


def filter_notifications_to_skip(notify_list, teflo_options):
    """
    Go through the notify_list and return notifications with which were skipped.
    If no notification with on_demand is found the original list is returned
    :return: List of notifications based on_demand
    """

    if teflo_options and teflo_options.get('skip_notify', False):
        return [res for res in notify_list
                if not {getattr(res, 'name')}.intersection(set(teflo_options.get('skip_notify')))]
    else:
        return notify_list


def filter_notifications_on_trigger(state, notify_list, passed_tasks, failed_tasks):
    """
    Go through the notify_list and return notifications with which were skipped.
    If no notification with on_demand is found the original list is returned
    :return: List of notifications based on_demand
    """
    if state == 'on_demand':
        return [res for res in notify_list if getattr(res, 'on_demand')]
    else:
        # filter out all on_demand notifications
        notify_list = [res for res in notify_list if not getattr(res, 'on_demand')]

    if state == 'on_start':
        return [res for res in notify_list if getattr(res, 'on_start') and len(set(getattr(res, 'on_tasks', [])).
                                                                               intersection(passed_tasks)) != 0]
    elif state == 'on_complete':
        ocl = list()

        # filter out all on_start notifications
        nl = [res for res in notify_list if not getattr(res, 'on_start')]

        # not executing if on_success but there are failed tasks
        passed = [nt for nt in nl if getattr(nt, 'on_success') is True and getattr(nt, 'on_failure') is False]
        passed = [nt for nt in passed if len(failed_tasks) == 0 and len(set(getattr(nt, 'on_tasks')).
                                                                        intersection(passed_tasks)) != 0]
        ocl.extend(passed)

        # not executing if on_failure but there are passed tasks
        failed = [nt for nt in nl if getattr(nt, 'on_failure') is True and getattr(nt, 'on_success') is False]
        failed = [nt for nt in failed if len(passed_tasks) == 0 and len(set(getattr(nt, 'on_tasks')).
                                                                        intersection(failed_tasks)) != 0]
        ocl.extend(failed)

        # not executing if on_failure or on_success
        mixed = [nt for nt in nl if getattr(nt, 'on_success') is True and getattr(nt, 'on_failure') is True]
        mixed = [nt for nt in mixed if len(set(getattr(nt, 'on_tasks')).
                                           intersection(failed_tasks)) != 0 or len(set(getattr(nt, 'on_tasks')).
                                                                                   intersection(passed_tasks)) != 0]
        ocl.extend(mixed)

        return ocl


def filter_resources_labels(res_list, teflo_options):
    """ this method filters out the resources which match the labels provided during teflo run
    or skips all the resources which match the skip_labels provided during teflo run
    :param res_list: list of resources
    :type res_list: list
    :param teflo_options: extra options set during teflo run
    :type teflo_options: dict
    :return: filtered resource list
    :rtype: list
    """

    if teflo_options and teflo_options.get('labels', ()):
        return[res for res in res_list if set(getattr(res, 'labels')).intersection(set(teflo_options.get('labels')))]
    elif teflo_options and teflo_options.get('skip_labels', ()):
        return [res for res in res_list
                if not set(getattr(res, 'labels')).intersection(set(teflo_options.get('skip_labels')))]
    else:
        return res_list


def fetch_assets(hosts, task, all_hosts=True):
    """Set the hosts for a task requiring hosts.

    This method is helpful for action/execute resources. These resources
    need the actual host objects instead of the referenced string name for
    the host in the given scenario descriptor file.

    It will fetch the correct hosts if the hosts for the given task are
    either string or host class type.

    :param hosts: scenario hosts
    :type hosts: list
    :param task: task requiring hosts
    :type task: dict
    :param all_hosts: determine to set all hosts
    :type all_hosts: bool
    :return: updated task object including host objects
    :rtype: dict
    """

    # placeholders
    _hosts = list()
    _all_hosts = list()
    _filtered_hosts = list()
    _type = None

    # determine the task attribute where hosts are stored
    if 'resource' in task:
        _type = 'resource'
    elif 'package' in task:
        _type = 'package'

    # determine the task host data types
    if all(isinstance(item, string_types) for item in task[_type].hosts):
        for host in hosts:
            if all_hosts:
                _all_hosts.append(host)
            if 'all' in task[_type].hosts:
                _hosts.append(host)
                continue
            if host.name in task[_type].hosts or [h for h in task[_type].hosts if h == host.name]:
                _hosts.append(host)
                continue
            elif hasattr(host, 'groups'):
                for g in host.groups:
                    if g in task[_type].hosts:
                        _hosts.append(host)
    else:
        for host in hosts:
            if all_hosts:
                _all_hosts.append(host)
            for task_host in task[_type].hosts:
                # additional check task_host.name in host.name was put in case when linchpin count was
                # used and there are host resources with names matching original resource name
                if host.name == task_host.name or task_host.name in host.name:
                    _hosts.append(host)
                    break
    if _hosts:
        task[_type].hosts = _hosts
    task[_type].all_hosts = _all_hosts
    return task


def fetch_executes(executes, hosts, task):
    """Set the executes for a task requiring executes.

    This method is helpful for report resources. These resources
    need the actual execute objects instead of the referenced string name for
    the execute in the given scenario descriptor file.

    It will fetch the correct execute if the execute for the given task are
    either string or execute class type.

    :param executes: scenario executes
    :type executes: list
    :param hosts: scenario hosts
    :type hosts: list
    :param task: task requiring executes
    :type task: dict
    :return: updated task object including execute objects
    :rtype: dict
    """

    # placeholders
    _executes = list()
    _type = None

    # determine the task attribute where hosts are stored
    if 'resource' in task:
        _type = 'resource'
    elif 'package' in task:
        _type = 'package'

    # determine the task host data types
    if all(isinstance(item, string_types) for item in task[_type].executes):
        for e in executes:
            if e.name in task[_type].executes:
                # fetch hosts to be used later for data injection
                dummy_task = dict()
                dummy_task[_type] = e
                dummy_task = fetch_assets(hosts, dummy_task)
                _executes.append(dummy_task[_type])
    else:
        for e in executes:
            for task_execute in task[_type].executes:
                if e.name == task_execute.name:
                    # fetch hosts to be used later for data injection
                    dummy_task = dict()
                    dummy_task[_type] = e
                    dummy_task = fetch_assets(hosts, dummy_task)
                    _executes.append(dummy_task[_type])
                    break

    if not _executes:
        # Kept having issues tyring to import the Execute
        # resource to make a dummy Execute with all the hosts
        # so this is a hack way of assigning the hosts.
        task[_type].all_hosts = hosts
    else:
        task[_type].executes = _executes
    return task


def filter_host_name(name):
    """
    A host name is limited to max 20 characters and ruled
    by the RULE_HOST_NAMING regex pattern defined in
    constants.

    :param name: the name to be filtered
    :return: 20 characters filtered name
    """
    result = RULE_HOST_NAMING.sub('', name)
    return str(result[:20]).lower()


def ssh_retry(obj):
    """
    Decorator to check SSH Connection before method execution.
    Will perform 30 retries with sleep of 10 seconds
    between attempts
    """
    MAX_ATTEMPTS = 30
    MAX_WAIT_TIME = 10

    def check_access(*args, **kwargs):
        """
        SSH Connection check and retries
        """
        # Set flag and Inventory
        ssh_errs = False
        args[0].set_inventory()

        # put everything into a list for rather than doing repetative if else statements
        # especially now that the inventory 'groups' property can be a string list of hosts
        # in the master inventory vs what is in the unique inventory
        host_groups = [kwargs['extra_vars']['hosts']] if kwargs['extra_vars']['hosts'].find(', ') == -1 \
            else kwargs['extra_vars']['hosts'].split(', ')
        inv_groups = args[0].inventory.groups
        for host_group in host_groups:
            if is_host_localhost(host_group):
                # Run Playbook/Module if localhost; no need to check.
                result = obj(*args, **kwargs)
                return result
            if host_group not in inv_groups:
                raise HelpersError(
                    'ERROR: Unexpected error - Group %s not found in inventory file!' % kwargs['extra_vars']['hosts']
                )

        def can_connect(group):

            sys_vars = group.vars
            server_ip = group.hosts[0].address
            LOG.info(server_ip)

            # skip ssh connectivity check if server is localhost
            if is_host_localhost(server_ip):
                return False

            server_user = sys_vars['ansible_user']
            server_key_file = sys_vars['ansible_ssh_private_key_file']
            server_ssh_port = 22 if 'ansible_port' not in sys_vars else sys_vars.get('ansible_port')

            # Perform SSH checks
            attempt = 1
            while attempt <= MAX_ATTEMPTS:
                try:
                    # Test ssh connection
                    pkey = import_privkey_file(server_key_file)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((server_ip, server_ssh_port))

                    session = Session()
                    session.options_set(options.USER, server_user)
                    session.options_set(options.HOST, server_ip)
                    session.options_set_port(server_ssh_port)
                    session.options_set(options.TIMEOUT, '5')

                    # Test ssh connection
                    session.connect()
                    rc = session.userauth_publickey(pkey)
                    LOG.debug("Server %s - IP: %s is reachable." %
                              (group, server_ip))
                    break

                except (SSHError, HostKeyNotVerifiable, AuthenticationError, socket.error, ConnectFailed,
                        ConnectionLost) as ex:
                    attempt = attempt + 1
                    LOG.error(ex)
                    LOG.error("Server %s - IP: %s is unreachable." % (group,
                                                                      server_ip))
                    if attempt <= MAX_ATTEMPTS:
                        LOG.info('Attempt %s of %s: retrying in %s seconds' %
                                 (attempt, MAX_ATTEMPTS, MAX_WAIT_TIME))
                        time.sleep(MAX_WAIT_TIME)
                except Exception:
                    LOG.error("Error occured while attempting to ssh to the host. Please verify ssh keys")
                    return True

            # Check Max SSH Retries performed
            if attempt > MAX_ATTEMPTS:
                LOG.error(
                    'Max Retries exceeded. SSH ERROR - Resource unreachable - Server %s - IP: %s!' %
                    (group, server_ip)
                )
                return True
            return False

        for host_group in host_groups:
            inv_group = inv_groups[host_group]
            # This is just here for backwards compat. In case I've missed any
            # corner case
            if hasattr(inv_group, 'child_groups') and inv_group.child_groups:
                LOG.debug('In the child group block')
                for group in inv_group.child_groups:
                    ssh_errs = can_connect(group)
            else:
                # Most cases should be falling into this block,
                # based on teflo returning the actual host asset name once its
                # done with its fetch_assets logic
                ssh_errs = can_connect(inv_group)

        # Check for SSH Errors
        if ssh_errs:
            raise HelpersError(
                'ERROR: Unable to establish ssh connection with resources!'
            )

        # Run Playbook/Module
        result = obj(*args, **kwargs)
        return result

    return check_access


def get_ans_verbosity(config):
    """Gets the Ansible verbosity level to be used by ansible or ansible-playbook commands.

    Below are the options for how Ansible verbosity can be set (in order):
        1. Ansible verbosity set within teflo.cfg
        2. Ansible verbosity set as environment variable
        3. Ansible verbosity is taken from teflo's log level option (debug == -vvvv)
        4. Ansible verbosity is disabled
    """
    if "ANSIBLE_VERBOSITY" in config and \
            config["ANSIBLE_VERBOSITY"]:
        ver = config["ANSIBLE_VERBOSITY"]
        if False in [letter == 'v' for letter in ver]:
            LOG.warning("Incorrect verbosity %s is set in teflo config file." % ver)
            ans_verbosity = 'vvvv' if config['LOG_LEVEL'] == 'debug' else None
            LOG.warning("Ansible logging set to %s" % ans_verbosity)
        else:
            ans_verbosity = ver
    elif os.getenv("ANSIBLE_VERBOSITY"):
        try:
            verbosity = os.getenv("ANSIBLE_VERBOSITY")
            verbosity = int(verbosity)
            if verbosity not in [0, 1, 2, 3, 4]:
                LOG.warning(f"Ansible verbosity level: {verbosity} is invalid. Defaulting to verbosity 0.")
                raise ValueError
            verbosity = "v" * verbosity
        except ValueError:
            verbosity = None
        ans_verbosity = verbosity
    elif config['LOG_LEVEL'] == 'debug':
        ans_verbosity = 'vvvv'
    else:
        ans_verbosity = None

    return ans_verbosity


class DataInjector(object):
    """Data injector class.

    This class is primarily used for injecting data into strings which the
    data to be replaced needs to come from a host resource. It is helpful
    in the cases where orchestrate or execute tasks require additional data.
    i.e. ip address, metadata, authentication details, etc.

    ---

    How does this work?

    You have a command in your definition file that needs the ip address of a
    host resource.

    command: /usr/bin/foo --ip { host01.ip_address[0] } --args ..

    The host01 is a resource defined in the provision section of teflo and
    the ip_address is an attribute of the host01. This class will evaluate
    the string and lookup the ip_address[0] from the host01 resource object
    and update the string with the correct information. This makes it helpful
    when orchestrate/execute tasks require data from the hosts itself.
    """

    def __init__(self, hosts):
        """Constructor.

        :param hosts: teflo host resources
        :type hosts: list
        """
        self.hosts = hosts

        # regular expression to search for in the string
        # data to be injected needs to be in the format of
        # { host01.metadata.k1 }
        self.regexp = r"\{(.*?)\}"

        # regex to check jsonpath strings
        self.exclusion_chk_str = r"^range|^[|.|$|@]|[\w|']+:"

    def host_exist(self, node):
        """Determine if the host defined in the string formatted var is valid.

        In the case no host is found, an exception is raised.

        :param node: node name
        :type node: str
        :return: teflo host resource matching based on node input
        :rtype: object
        """
        for host in self.hosts:
            if node == getattr(host, 'name'):
                return host
        raise TefloError('Node %s not found!' % node)

    def inject(self, command):
        """Main worker.

        This method will perform the data injection.

        :param command: command to inject data into
        :type command: str
        :return: updated command
        :rtype: str
        """

        variables = list(map(str.strip, re.findall(self.regexp, command)))

        if not variables.__len__():
            return command

        for variable in variables:
            if re.match(self.exclusion_chk_str, variable):
                LOG.debug("JSONPath format was identified in the command %s." % variable)
                continue
            else:
                value = None
                _vars = variable.split('.')
                node = _vars.pop(0)

                # verify variable has a valid host set
                host = self.host_exist(node)

                for index, item in enumerate(_vars):
                    try:
                        # is the item intended to be a position in a list, if so
                        # get the key and position
                        key = item.split('[')[0]
                        pos = int(item.split('[')[1].split(']')[0])

                        if value:
                            # get the latest value from the dictionary
                            value = value[key][pos]
                        else:
                            # get latest value from host
                            if hasattr(host, key) and index <= 0:
                                value = getattr(host, key)[pos]
                                if isinstance(value, str):
                                    break

                        # is the value a dict, if so keep going!
                        if isinstance(value, dict):
                            continue
                    except IndexError:
                        # item is not intended to be a position in a list

                        # check if the item is an attribute of the host
                        if hasattr(host, item) and index <= 0:
                            value = getattr(host, item)

                            if isinstance(value, str):
                                # we know the value has no further traversing to do
                                break
                            # value is either a list or dict, more traversing to do
                            continue
                        else:
                            if value is None:
                                raise AttributeError('%s not found in host %s!' %
                                                     (item, getattr(host, 'name')))

                        # check if the item's value is a dict and update the value
                        # for further traversing to do
                        try:
                            if isinstance(value[item], dict):
                                value = value[item]
                                continue
                        except KeyError:
                            raise TefloError('%s not found in %s' % (item, value))

                        # final check to get value no more traversing required
                        if value:
                            value = value[item]
                    except KeyError:
                        raise TefloError('Unable to locate item %s!' % item)

                command = command.replace('{ %s }' % variable, value)
        return command

    def inject_dictionary(self, dictionary):
        """
        inject data into a dictionary where
        data-passthrough template is encountered

        :param dictionary:
        :return:
        """
        injected_dict = dict()

        for key, value in dictionary.items():
            inj_key = self.inject(key)
            if isinstance(value, list):
                inj_val = self.inject_list(value)
            elif isinstance(value, dict):
                inj_val = self.inject_dictionary(value)
            elif isinstance(value, string_types):
                inj_val = self.inject(value)
            else:
                inj_val = value
            injected_dict.update({inj_key: inj_val})

        return injected_dict

    def inject_list(self, item_list):
        """
        inject data into a list where
        data-passthrough template is encountered

        :param item_list: a list to inject data into
        :return:
        """
        injected_list = list()

        for item in item_list:
            if isinstance(item, list):
                inj_item = self.inject_list(item)
            elif isinstance(item, dict):
                inj_item = self.inject_dictionary(item)
            elif isinstance(item, string_types):
                inj_item = self.inject(item)
            else:
                inj_item = item
            injected_list.append(inj_item)

        return injected_list


def is_host_localhost(host_ip):
    """Determine if the host ip address given is localhost.

    Since it can be hard to determine if the host is localhost, we will
    initially verify its localhost if the ip_address has a value of either:
        - 127.0.0.1
        - localhost
    If the host ip_address is either of those, then we know that the machine
    is the localhost.

    :param host_ip: host resource ip address
    :type host_ip: str
    :return: whether the ip address is localhost or not
    :rtype: bool
    """
    if host_ip not in ['127.0.0.1', 'localhost']:
        return False
    return True


def find_artifacts_on_disk(data_folder, report_name, art_location=[]):
    """
    Used by the Artifact Importer to to search a list of paths in the results folder
    to see if they exist. If the Execute collected artifacts, it will check the
    the .results/artifacts/ specifically for the artifacts.

    If the Execute did not collect artifacts, it will walk the .results
    looking for the artifacts

    :param data_folder: the results directory
    :type data_folder: path as a string
    :param path_list: The list of artifacts to look for
    :type path_list: a list containing a string of paths
    :param art_location_found: Whether the Executes object collected artifacts
    :type art_location_found: Boolean
    :return: a list of artifacts that were found to be imported.
    """
    fnd_paths = list()
    # build the regex query from the report_name pattern specified
    regquery = build_artifact_regex_query(report_name)

    # search the artifact location dictionary if provided
    fnd_paths.extend(search_artifact_location_dict(art_location, report_name, data_folder, regquery))

    # attempt to walk the directory as well in case there was anything else the user wanted collected
    walked_list = walk_results_directory(data_folder, fnd_paths)

    # check for any matches from the walked list
    matches = [regquery.search(p) for p in walked_list]

    # Add any matches from walked list to the found artifacts list
    fnd_paths.extend([m.string for m in matches if m])

    if fnd_paths:
        for f in fnd_paths:
            LOG.info('Artifact %s has been found!' % os.path.basename(f))
            LOG.debug('Full path to artifact on disk: %s' % f)

    if not fnd_paths:
        LOG.error('Did not find any of the artifacts on local disk. '
                  'Import cannot occur!')

    return fnd_paths


def check_path_exists(element, dir):
    # check if the path exists
    return os.path.exists(os.path.abspath(os.path.join(dir, element)))


def search_artifact_location_dict(art_locations, report_name, data_folder, reg_query):
    """
    Use by the Artifact Importer to search a list of collected
    artifacts by the Execute phase using regex to search for the report name

    :param art_locations: the list of files collected during Execute
    :type art_locations: list of string paths
    :param report_name: The artifact to look for
    :type report_name: a string of an artifact name, can contain regex
    :param data_folder: the directory to look in if path are found
    :type: data_folder: string
    :param reg_query: The regex query to use to search the artifact_location
    :type reg_query: regexquery object
    :return: a list containing the artifacts found
    """
    artifacts_path = []

    if art_locations:
        full_path = art_locations
        for f in full_path:
            LOG.debug('These are the artifact_locations in the execute: %s' % f)
        matches = [reg_query.search(p) for p in full_path]
        artifacts_path = [m.string for m in matches if m]

        for fn in artifacts_path:
            LOG.debug('Found the following artifact, %s, that matched %s in artifact_location' % (fn, report_name))

        # Check the path in data_folder
        artifacts_path = [os.path.abspath(os.path.join(data_folder, p))
                          for p in artifacts_path if check_path_exists(p, data_folder)]

    return artifacts_path


def walk_results_directory(dir, path_list):
    """
    Used to walk the .results directory
    when the artifact in question is not in the list of
    artifacts collected by Execute

    :param dir: The directory to walk
    :type dir: string dir path
    :param path_list: The list of pathes that was found in artifact_locations
    :type path_list: List
    :return: a list containing all the paths from data_folder and .results
    """

    data_dir_list = []

    # Teflo specific folders in datafolder and .results folder
    exclude = ['logs', 'rp_logs', 'rp_payload', 'inventory']

    # iterate over the data folder first
    for root, dirs, files in os.walk(dir):
        # Excluding teflo specific folders
        dirs[:] = [d for d in dirs if d not in exclude]
        for f in files:
            p = os.path.abspath(os.path.join(root, f))
            if p not in path_list:
                LOG.debug(p)
                data_dir_list.append(p)

    return data_dir_list


def build_artifact_regex_query(name):
    """
    Used to build a regex query from the artifact
    name which could contain shell file matching pattern.

    :param name: The artifact name
    :type name: string
    :return: a compiled regex query
    """

    regex = fnmatch.translate(name)
    regquery = re.compile(regex)
    return regquery


def check_for_var_file(config):
    """ This method  is for checking if variable file/directory is provided by the user in teflo.cfg under var_file key,
     var_file.yml under the workspace , vars folder in the workspace and
     It looks for yaml/yml files and then returns a list of file paths

     Var files set every where (teflo.cfg, var_file.yml. vars folder) are collected, but the following
     precedence is followed:
     1. values passed over cli will override the ones set by the below options
     2. values set in teflo.cfg will override the ones set by the below options
     3. values set in var_file.yml will override the ones set by below options
     4. values set in vars folder in current workspace

    :param config: config object for teflo
    :type config: config obj
    :return: var_file_list
    :rtype: list of variable file paths
    """

    var_file_list = list()
    var_dir = os.path.join(config.get('WORKSPACE'), 'vars')
    workspace_var_file = os.path.join(config.get('WORKSPACE'), 'var_file.yml')
    if config.get('VAR_FILE'):
        default_var_file = os.path.abspath(os.path.expandvars(os.path.expanduser(config.get('VAR_FILE'))))
    else:
        default_var_file = ''

    if os.path.exists(var_dir) and os.path.isdir(var_dir):
        LOG.debug("Looking for .yml files as variable file under vars folder in the current workspace")

        for subdir, dirs, files in os.walk(var_dir):
            for filename in files:
                filepath = subdir + os.sep + filename
                if filepath.endswith(".yml"):
                    var_file_list.append(filepath)

    if os.path.exists(workspace_var_file):
        LOG.debug("var_file.yml in current workspace added as a varaible file")
        var_file_list.append(workspace_var_file)

    if default_var_file and os.path.exists(default_var_file):
        if os.path.isdir(default_var_file):
            LOG.debug("Default variable file path in teflo.cfg is a directory. "
                      "Looking for .yml files to be used as variable files")

            for subdir, dirs, files in os.walk(default_var_file):
                for filename in files:
                    filepath = subdir + os.sep + filename
                    if filepath.endswith(".yml"):
                        var_file_list.append(filepath)
        else:
            LOG.debug("Default variable file found in teflo.cfg")
            var_file_list.append(default_var_file)

    return var_file_list


def validate_brackets(input):
    """
    Helper funcion that validates if the input
    is a validate string that has paired brackets
    param input: raw variable string, something like this -> "hello {{ var }}"
    :param type: str
    e.x. :
    "hello {{ var }}" is valid
    "hello {{ var }" is invalid
    :type config: config obj
    :rtype: bool

    """
    left = []
    for char in input:
        if char == "{":
            left.append(char)
        if char == "}":
            if len(left) == 0:
                return False
            left.pop()
    return len(left) == 0


def replace_brackets(input, temp_data):
    """
    This function replace the the refered variable by it's true value recursively
    e.x.:
    input_yaml:
        a = "Hello, world!!"
        b = "{{ hello }}" -> this is the input for this function
    b will be conveted to "hello world" after running replace_brackerts(b, input_yaml)
    :param input: the raw string in yaml input
    :param type: str
    :return new string with variables' values
    """
    if validate_brackets(input) and input.__contains__("{{") and input.__contains__("}}"):
        left = []
        key_start, key_end = 0, 0
        replace_start, replace_end = 0, 0
        for i in range(len(input)):
            if input[i] == "{":
                left.append(i)
            elif input[i] == "}":
                key_start, key_end = left.pop() + 1, i
                replace_start, replace_end = left.pop(), i + 2
                break

        key = input[key_start:key_end].strip()
        if temp_data.get(key, None) is None:
            return input
        if not isinstance(temp_data[key], str):
            temp_data.update({key: preprocyaml(temp_data[key], temp_data)})

        if isinstance(temp_data[key], str):
            ret = input.replace(input[replace_start:replace_end], temp_data[key], 1)
        elif isinstance(temp_data[key], list) or isinstance(temp_data[key], dict):
            ret = temp_data[key]

        return replace_brackets(ret, temp_data)
    else:
        return input


def preprocyaml_str(input, temp_data):
    """
    This function is a wrapper function for replace_brackets
    Just make it look more intuitive from its name
    """
    return replace_brackets(input, temp_data)


def preprocyaml(input, temp_data):
    """
    This function will add the variable value to the raw string,
    it handles all kinds of input including: string, list, dict
    this function will add varible value to the input recursively
    :param input: input from the yaml file
    :param type: str, list, or dict
    :return new value with the nested variable value added to the field in the yaml file
    """
    if isinstance(input, str):
        return preprocyaml_str(input, temp_data)
    elif isinstance(input, list):
        new_list = []
        for val in input:
            new_list.append(preprocyaml(val, temp_data))
        return new_list
    elif isinstance(input, comments.CommentedMap):
        new_dict = {}
        for item in input._items():
            if not isinstance(item[0], str):
                result = ""
                for key in item[0].keys():
                    if not isinstance(temp_data[key], str):
                        temp_data.update({key: preprocyaml(temp_data[key], temp_data)})
                    result = result + temp_data[key]
                return result
            new_dict.update({item[0]: item[1]})
        for item in new_dict.items():
            new_dict.update({item[0]: preprocyaml(item[1], temp_data)})
        return new_dict
    else:
        return input


def preprocyaml_jinja(temp_data: dict, file_path: str = None) -> dict:
    """
    This function recursively render the temp_data(var_data), with itself until
    the rendered result doesn't change any more.
    It returns a dict version of the temp_data
    """
    prev_res = ""
    res_dict = temp_data
    result = yaml.dump(res_dict, sort_keys=False)

    class NullUndefined(jinja2.Undefined):
        def __getattr__(self, key):
            return ''

    while result != prev_res:
        prev_res = result
        t = jinja2.Template(result, undefined=NullUndefined)
        result = t.render(yaml.safe_load(result))

    return yaml.safe_load(result)


def preproc_path(data_folder: str) -> str:
    """
    This method takes a path and remove
    the "." and the uuid at the end of it
    For example:
    ./data_folder/sjf8f2vc
    will become /data_folder
    """

    ret = ""
    if data_folder[0] == ".":
        ret = data_folder[1:]
    else:
        ret = data_folder
    ret = ret[:ret.rindex("/")]
    return ret


def validate_render_scenario(scenario_path, config, temp_data_raw=()):
    """
    This method takes the absolute path of the scenario descriptor file and returns back a list of
    data streams of scenario(s) after doing the following checks:
    (1) Checks there is no yaml.safe_load error for the provided scenario file
    (2) Checks for include section present in the scenario file
    (3) Checks the include section has valid scenario file path and it is not empty
    (4) Checks there is no yaml.safe_load error for scenario file in the include section
    :param scenario: scenario file path
    :type scenario: str
    :param config: config object for teflo
    :type config: config obj
    :param temp_data_raw: a list of the file path to jinja template vars data or a json dictionary of vars data
    :type temp_data_raw: dict or str
    :return scenario_graph
    :rtype: ScenarioGraph
    """

    # Click gives us a tuple, by default
    var_file_list = check_for_var_file(config)
    if isinstance(temp_data_raw, tuple):
        var_file_list.extend(list(temp_data_raw))
    # Convert each item to an object, then reduce them all back to one
    temp_data_objs = [file_mgmt("r", t) if os.path.isfile(t)
                                  else json.loads(t) for t in var_file_list]
    # Reduce it down to a single object we can work with
    temp_data = {}
    [temp_data.update(t) for t in temp_data_objs]

    for item in temp_data.items():
        temp_data.update({item[0]: preprocyaml(item[1], temp_data)})

    temp_data = preprocyaml_jinja(temp_data)
    temp_data.update(os.environ)

    try:
        # Build a scenario graph
        scenario_graph = build_scenario_graph(root_scenario_path=scenario_path,
                                              root_scenario_temp_data=temp_data, config=config)

    except yaml.YAMLError as e:
        # here raising yaml error to differentiate yaml issue is with main scenario
        raise e
    return scenario_graph


def build_scenario_graph(root_scenario_path: str, config, root_scenario_temp_data):
    '''
    This method builds a scenario graph with the root_sceanrio_path and root_scenario_temp_data
    We utilized the iterative way to implement this, so it will not cause stackoverflow even
    with over 1000 linked included sdfs

    :param root_scenario_path: the root sdf path
    :type root_scenario_path: str
    :param root_scenario_temp_data: the temp data that all sdf need to render with
    :type root_scenario_temp_data: dict
    '''
    # Must import these two libs here to avoid circular import for Python intepreter
    from .resources import Scenario
    from .utils.scenario_graph import ScenarioGraph
    yaml.safe_load(template_render(root_scenario_path, root_scenario_temp_data,
                                   config.get("TOGGLE_JINJA_INCLUDE", False)))
    root_scenario_yaml_data = template_render(root_scenario_path, root_scenario_temp_data,
                                              config.get("TOGGLE_JINJA_INCLUDE", False))
    root_scenario = Scenario(config=config, path=os.path.basename(root_scenario_path))
    root_scenario.fullpath = root_scenario_path
    root_scenario.yaml_data = root_scenario_yaml_data
    # deepcopy will work only under pythonversion > 3.9
    # leave this line here for future improvement
    # root_config = deepcopy(config)

    def addAllIncludes(parent_scenario: Scenario, checked_list: dict):
        '''
        This method add all included child sdfs to the parent_scenario
        as its child_scenarios

        :param parent_scenario: the parent scenario object
        :type root_scenario_path: Scenario
        :param checked_list: the checked list for all visited Scenarios
        :type checked_list: dict
        '''
        if parent_scenario is None:
            return

        data = yaml.safe_load(parent_scenario.yaml_data)

        # process the parent sc here, (process its remote_workspace section,include section)

        def process_remote_workspace(remote_workspaces: list):

            if config["REMOTE_WORKSPACE_DOWNLOAD_LOCATION"][-1] != "/":
                config["REMOTE_WORKSPACE_DOWNLOAD_LOCATION"] = config["REMOTE_WORKSPACE_DOWNLOAD_LOCATION"] + "/"
            ret = {}
            for workspace in remote_workspaces:
                url = workspace.get("workspace_url", None)
                short_name_of_workspace = workspace.get("alias_name", None)
                if url is None:
                    raise TefloError(
                            "Your format of the imported remote_workspace is incorrect ")
                cmd = 'git clone ' + url + ' ' + config["REMOTE_WORKSPACE_DOWNLOAD_LOCATION"] + short_name_of_workspace
                if not os.path.isdir(config["REMOTE_WORKSPACE_DOWNLOAD_LOCATION"] + short_name_of_workspace):
                    result = exec_local_cmd(cmd)
                    if result[0] != 0:
                        raise TefloError("Remote remote_workspaces download failed!!")

                # all remote remote_workspaces should be stored in the same place
                # (root_workspace/.teflo_remote_workspace_cache/)
                # so we should use root_config instead of parent_scenario.config,
                # which always contains the root sdf workspace path
                remote_workspace_path = os.path.join(
                        config["WORKSPACE"], config["REMOTE_WORKSPACE_DOWNLOAD_LOCATION"] + short_name_of_workspace)
                ret[short_name_of_workspace] = remote_workspace_path
            return ret

        workspace_info = None
        if 'remote_workspace' in data.keys() and data['remote_workspace'] is not None \
                and len(data['remote_workspace']) is not 0:
            remote_workspaces = data['remote_workspace']
            workspace_info = process_remote_workspace(remote_workspaces)

        def process_path(path: str, workspace_info: dict):
            # ex remote_workspace/sdf.yml
            if path is None or path == "":
                return None, None
            if workspace_info is None:
                return None, None
            real_path = path.split("/")
            if workspace_info.get(real_path[0], None) is not None:
                real_path[0] = workspace_info.get(real_path[0], None)
            else:
                return path, None
            ret = "/".join(real_path)
            # return processed full path and the remote workspace dir name
            return ret, real_path[0]

        if 'include' in data.keys() and data['include'] is not None:
            include_item = data['include']
            for item in include_item:
                if checked_list.get(item) is not None:
                    raise TefloError(
                        "Your scenario has an import cycle. \
                            %s is already a node in the scenario graph, It cannot be added again. "
                        % item)
                # this config is from the root teflo project which means the current workspace's teflo.cfg
                sc_fullpath = os.path.join(parent_scenario.config['WORKSPACE'], item)
                sc_abspath = item
                # return processed path and the remote short name
                remote_path = process_path(item, workspace_info)
                sc_fullpath_is_valid = os.path.isfile(sc_fullpath)
                sc_abspath_is_valid = os.path.isfile(sc_abspath)
                remote_path_is_valid = os.path.isfile(remote_path[0]) if \
                    remote_path[0] else False

                if sc_fullpath_is_valid or sc_abspath_is_valid or remote_path_is_valid:
                    path = os.path.basename(item)
                    if os.path.isfile(sc_fullpath):
                        item = sc_fullpath
                    elif os.path.isfile(sc_abspath):
                        item = sc_abspath
                    elif remote_path[0] and os.path.isfile(remote_path[0]):
                        item = remote_path[0]
                    # check to verify the data in included scenario is valid
                    try:
                        yaml.safe_load(template_render(item, root_scenario_temp_data,
                                                       config.get("TOGGLE_JINJA_INCLUDE", False)))
                        from .utils.config import Config
                        root_config = Config()
                        root_config.load()
                        for xxx in parent_scenario.config.items():
                            root_config[xxx[0]] = xxx[1]
                        child_sc = Scenario(config=root_config, path=path)
                        # change workspace if this is a remote sc
                        if workspace_info is not None and remote_path[1]:
                            child_sc.config["WORKSPACE"] = remote_path[1]
                        else:
                            child_sc.config["WORKSPACE"] = parent_scenario.config.get("WORKSPACE")
                        child_sc.fullpath = sc_fullpath if os.path.isfile(sc_fullpath) else sc_abspath
                        child_sc.yaml_data = template_render(item, root_scenario_temp_data,
                                                             config.get("TOGGLE_JINJA_INCLUDE", False))
                        parent_scenario.add_child_scenario(child_sc)
                        # use filename because the scenario name could
                        # contain some special characters, which is not good for
                        # file generation
                        if preproc_path(config['RESULTS_FOLDER']) in child_sc.fullpath or \
                                preproc_path(config["DATA_FOLDER"]) in child_sc.fullpath:
                            parent_scenario.included_scenario_path = os.path.join(
                                config['RESULTS_FOLDER'], child_sc.path)
                        else:
                            parent_scenario.included_scenario_path = os.path.join(
                                config['RESULTS_FOLDER'], child_sc.path.split(".")[0] + "_results.yml")
                    except yaml.YAMLError as err:
                        # raising Teflo error to differentiate the yaml issue is with included scenario
                        raise TefloError('Error loading included '
                                         'scenario data! ' + item + str(err.problem_mark))
                else:
                    raise TefloError('Included File is invalid or Include section is empty.'
                                     ' You have to provide valid scenario files to be included.')

    def include(unchecked_list: list, checked_list: dict):
        '''
        This method will build a scenario linked graph
        It reads from the unckecked_list for unread sceanrios
        and add all its child to it, then add all it's children
        to the unchecked list for next iteration

        :param unchecked_list: the unchecked list of sceanrios
        :type unchecked_list: list
        :param checked_list: the checked list for all visited Scenarios
        :type checked_list: dict
        '''
        # unchecked_list is a queue-liked list, we keep this as channel
        # to maintain all unchecked scenarios
        while len(unchecked_list) != 0:
            sc: Scenario = unchecked_list.pop(0)
            checked_list[sc.path] = sc.path
            addAllIncludes(sc, checked_list)
            # We need to remove the checked scenario from the unchecked_list
            # after we addAllIncludes for it
            if sc.child_scenarios != []:
                for sc in sc.child_scenarios:
                    unchecked_list.append(sc)

    include([root_scenario], {})
    scenario_graph = ScenarioGraph(root_scenario, iterate_method=config.get("INCLUDED_SDF_ITERATE_METHOD", "by_level"),
                                   scenario_vars=root_scenario_temp_data)
    return scenario_graph


def ssh_key_file_generator(workspace, ssh_key_param):
    """
    A method to find if the ssh key value in a provider
    param is a path to a public or private key. If it
    is a public key, just return the key back. If it
    is a private key, generate the public key from it
    and return that back.

    Right now this is only really used by Linchpin
    in the LinchpinResourceBuilder class for Beaker
    resources because they expect a public key and the
    various ssh key options in their resource defintions

    :param workspace: the Teflo workspace keys directory
    :type workspace: path as a string
    :param ssh_key_param: the ssh_key from the provider param
    :type ssh_key_param: value of the ssh_key param either a path or an actual key
    :return: a path to a public key
    """

    # setup absolute path for key
    key = os.path.join(workspace, ssh_key_param)

    # set permission of the key
    try:
        os.chmod(key, stat.S_IRUSR | stat.S_IWUSR)
    except OSError as ex:
        raise HelpersError(
            'Error setting private key file permissions: %s' % ex
        )

    # Lets assume it's a private key file and try to load it
    # and create a public key for it
    try:
        rsa_key = RSAKey.from_private_key_file(key)
        # generate public key from private
        public_key = os.path.join(
            workspace, ssh_key_param + ".pub"
        )
        with open(public_key, 'w') as f:
            f.write('%s %s\n' % (rsa_key.get_name(), rsa_key.get_base64()))
        return public_key
    except SSHException:
        # Exception means the key file was invalid.
        # Assume it's a public key and return it
        return key


def lookup_ip_of_hostname(host_name):
    """
    A method to find the ip of the hostname.
    This is used by Linchpin specifically for Beaker
    since 99% of the systems in beaker are by FQDN host name.
    To make sure the IP address field in the teflo Asset resource
    is an actual IP address we need to look it up


    :param host_name: the FQDN of the host
    :type host_name: string
    :return: return a string containing the ip
    """
    return socket.gethostbyname(host_name)


def set_task_class_concurrency(task, resource):
    """
    set the task __concurrency__ field in the class
    to whatever was passed in the config
    :param task:
    :type task: TefloTask class
    :param resource:
    :type TefloResource object
    :return: TefloTask class
    """
    val = getattr(resource, 'config')['TASK_CONCURRENCY'].get(task['task'].__task_name__.upper())
    if val.lower() == 'true':
        val = True
    else:
        val = False
    task['task'].__concurrent__ = val
    return task


def mask_credentials_password(credentials):
    """
    Mask the credentials that could get printed out
    to stdout or teflo_output.log

    :param credentials:
    :return: credentials dict
    """
    asteriks = ''
    masked_creds = dict()
    if credentials:
        for k, v in credentials.items():
            for p in ['password', 'token', 'key', 'id']:
                if p not in k:
                    continue
                else:
                    for i in range(0, len(v)):
                        asteriks += '*' * random.randint(1, 3)
            if asteriks != '':
                masked_creds.update({k: asteriks})
                asteriks = ''
                continue
            masked_creds.update({k: v})

    return masked_creds


def sort_tasklist(user_tasks):
    """
    :param user_tasks:
    :return: Array of tasks
    """

    try:
        return sorted(user_tasks, key=TASKLIST.index)
    except IndexError:
        return sorted(user_tasks, key=NOTIFYSTATES.index)


def validate_cli_scenario_option(ctx, scenario, config, vars_data=None):
    # Make sure the file exists and gets its absolute path
    if scenario is not None and os.path.isfile(scenario):
        scenario = os.path.abspath(scenario)
    else:
        click.echo('You have to provide a valid scenario file.')
        ctx.exit(1)

    # Checking if include section is present and getting validated scenario stream/s
    try:
        scenario_graph = validate_render_scenario(scenario, config, vars_data)
        return scenario_graph
    except yaml.YAMLError as err:
        click.echo('Error loading scenario data! %s' % err)
        ctx.exit(1)
    except HelpersError:
        click.echo('Included File is invalid or Include section is empty.'
                   'You have to provide valid scenario files to be included.')
        ctx.exit(1)
    except TefloError as err:
        click.echo('%s' % err.message)
        ctx.exit(1)
    except jinja2.exceptions.UndefinedError as err:
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        if calframe[1][3] == 'show':
            click.echo("\n\nYou need to use --vars-data to fill your variables for show command")
            ctx.exit(1)
        else:
            raise TefloError("You need to fill your variable with --vars-data label")


def create_individual_testrun_results(artifact_locations, config):
    """this method creates a summary of total tests passed, failed, skipped for all the xml files found
    as artifacts
     :param artifact_locations: list of relative paths of artifacts where root dir is the key and artifact names are
                                values
     :type artifact_locations: list
     :param config: config parameter used by execute resource
     :type config: dict
     :return testruns: a dictionary of test results summary for individual xml files as well as aggregate of all xml
                       files found
     :rtype testruns: dict
    """
    fnd_paths = list()
    individual_res = list()
    # build the regex query to get only xml files
    regquery = build_artifact_regex_query('*.xml')
    # search the artifact location dictionary provided to search in the .results folder
    fnd_paths.extend(search_artifact_location_dict(artifact_locations, '*.xml', config.get('RESULTS_FOLDER'), regquery))
    try:
        for path in fnd_paths:
            trun = dict()
            trun['total_tests'] = 0
            trun['failed_tests'] = 0
            trun['error_tests'] = 0
            trun['skipped_tests'] = 0
            trun['passed_tests'] = 0
            tree = ET.parse(path)
            root = tree.getroot()
            temp = list()
            # if root.tag is testsuites then collect all the element which are 'testsuite'
            # if root.tag is testsuite then just collect that element
            if root.tag == "testsuites":
                temp.extend(root.findall('testsuite'))
            elif root.tag == "testsuite":
                temp.append(root)
            if temp:
                for test in temp:
                    trun['total_tests'] = trun['total_tests'] + len(test.findall('testcase'))
                    trun['failed_tests'] = trun['failed_tests'] + len([testcase.find('failure')
                                                                        for testcase in test.findall('testcase')
                                                                        if testcase.findall('failure')])
                    trun['error_tests'] = trun['error_tests'] + len([testcase.find('error')
                                                                        for testcase in test.findall('testcase')
                                                                        if testcase.findall('error')])
                    trun['skipped_tests'] = trun['skipped_tests'] + len([testcase.find('skipped')
                                                                         for testcase in test.findall('testcase')
                                                                         if testcase.findall('skipped')])
                    trun['passed_tests'] = trun['total_tests'] - trun['failed_tests'] - trun['error_tests'] -\
                                           trun['skipped_tests']
                individual_res.append({os.path.basename(path): trun})
            else:
                LOG.warning("The xml file %s does not have the correct format (no 'testsuite' or 'testsuites'"
                            " tags) to collect testrun results" % path)
                continue
    except ET.ParseError:
        raise TefloError("The xml file %s is malformed " % path)
    return individual_res


def create_aggregate_testrun_results(individual_results):
    """this method creates a aggregate summary of total tests passed, failed, skipped for all the xml files found
    as artifacts
    :param individual_results: list of individual test summaries of xml files found as artifacts
    :type: individual_results: list
    :return agg_results: summary of aggregate of all individual summaries of xml files found as artifacts
    :rtype agg_results: dict
    """
    total_tests = 0
    failed_tests = 0
    error_tests = 0
    skipped_tests = 0
    passed_tests = 0
    agg_results = dict()

    for run in individual_results:
        for val in run.values():
            total_tests += val['total_tests']
            failed_tests += val['failed_tests']
            error_tests += val['error_tests']
            skipped_tests += val['skipped_tests']
            passed_tests += val['passed_tests']

    agg_results.update(aggregate_testrun_results=dict(total_tests=total_tests,
                                                      failed_tests=failed_tests,
                                                      error_tests=error_tests,
                                                      skipped_tests=skipped_tests,
                                                      passed_tests=passed_tests
                                                      ))
    return agg_results


def create_testrun_results(artifact_locations, config):
    """This method goes through the artifact_locations or paths provided and finds only the xmls. Using these
    xmls, generates a testrun_results dictionary which is a summary of total tests passed, failed, skipped. It
    generates the aggregate as well as individual xml summary
     :param artifact_locations: list of relative paths of artifacts where root dir is the key and artifact names are
                                values
     :type artifact_locations: list
     :param config: config parameter used by execute resource
     :type config: dict
     :return testruns: a dictionary of test results summary for individual xml files as well as aggregate of all xml
                       files found
     :rtype testruns: dict
     """
    testruns = dict()
    individual_results = create_individual_testrun_results(artifact_locations, config)
    testruns.update(create_aggregate_testrun_results(individual_results))
    testruns.update(individual_results=individual_results)
    return testruns


def generate_default_template_vars(scenario, notification):
    """
    Default template dictionary created to be used
    when rendering the default notification template.
    :return: temp_dict dict dictionary of selected variables for rendering notification templates
    """

    passed_tasks = getattr(scenario, 'passed_tasks', [])
    failed_tasks = getattr(scenario, 'failed_tasks', [])

    temp_dict = dict(scenario=scenario)

    temp_dict['scenario_graph'] = scenario.__getattribute__('scenario_graph')

    temp_dict['scenario_vars'] = temp_dict.get('scenario_graph').__getattribute__('scenario_vars')

    if getattr(notification, 'on_start', False):
        temp_dict['passed_tasks'] = passed_tasks[-1]
        return temp_dict

    if passed_tasks:
        temp_dict['passed_tasks'] = ','.join(passed_tasks)

    if failed_tasks:
        temp_dict['failed_tasks'] = ','.join(failed_tasks)

    return temp_dict


class StatusPageHelper(object):

    def __init__(self, proxyserver_url):
        self.proxyserver_url = proxyserver_url

    def get_info(self):
        ret = {}
        try:
            info = requests.get(self.proxyserver_url + "/components").json()['components']
            for item in info:
                if item.get("name") is not None:
                    ret[item["name"]] = item
        except Exception:
            raise TefloError("The url is incorrect for resource check")
        return ret
