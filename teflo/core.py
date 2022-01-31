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
    teflo.core

    Module containing the core classes which teflo resources, tasks,
    providers, provisioners, etc inherit.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import errno
import os
import yaml
import inspect
from glob import glob
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
from logging import getLogger, Filter
from logging import config as log_config
from time import time, sleep
from collections import OrderedDict
from .exceptions import TefloError, TefloResourceError, LoggerMixinError, TefloImporterError
from .helpers import get_core_tasks_classes
from traceback import format_exc
from ._compat import RawConfigParser, string_types
from .constants import LOGGING_CONFIG
import threading
from .helpers import gen_random_str


class LoggerMixin(object):
    """Teflos logger mixin class.

    This class provides an easy interface for other classes throughout teflo
    to utilize the teflo logger.

    When a teflo object is created, the teflo logger will be created also.
    Allowing easy access to the logger as follows:

        cbn = Teflo()
        cbn.logger.info('Teflo!')

    Teflo packages (classes) can either include the logger mixin or create
    their own object.

        class Asset(TefloResource):
            self.logger.info('Teflo Resource!')

    Modules that want to use teflo logger per function base and not per class,
    can access the teflo logger as follows:

        from logging import getLogger
        LOG = getLogger(__name__)
        LOG.info('Teflo!')

    New loggers for other libraries can easily be added. A create_lib_logger
    method will need to be create to setup the logger. Then lastly you can set
    a property to return that specific logger for easy access.
    """

    _DEBUG_LOG_FORMAT = ("%(asctime)s %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s")
    _INFO_LOG_FORMAT = ("%(asctime)s %(levelname)s %(message)s")

    _LOG_LEVELS = {
        'debug': DEBUG,
        'info': INFO,
        'warning': WARNING,
        'error': ERROR,
        'critical': CRITICAL
    }

    @classmethod
    def setup_logger(cls, name, file_path, config=None):

        # Setting up handlers
        LOGGING_CONFIG['handlers']['file'].update({'filename': file_path})

        # setup logging formatters
        LOGGING_CONFIG['formatters']['default'].update({'format': cls._INFO_LOG_FORMAT})
        LOGGING_CONFIG['formatters']['debug'].update({'format': cls._DEBUG_LOG_FORMAT})

        if config:
            # setup any other loggers that might have been specified in the teflo.cfg
            # For now this might suffice but if the teflo community changes we can look
            # at a better way through the plugins
            for logger in config['SETUP_LOGGER']:
                LOGGING_CONFIG['loggers'].update({logger: {'handlers': ['console', 'file'],
                                                           'level': cls._LOG_LEVELS[config['LOG_LEVEL']],
                                                           'propagate': False}})
            log_level = config['LOG_LEVEL']
        else:
            log_level = 'info' if getLogger('teflo').getEffectiveLevel() == 20 else 'debug'

        if log_level == 'debug':

            for handler in LOGGING_CONFIG['handlers']:
                LOGGING_CONFIG['handlers'][handler].update({'formatter': 'debug'})
                LOGGING_CONFIG['handlers'][handler].update({'level': cls._LOG_LEVELS[log_level]})

            for logger in LOGGING_CONFIG['loggers']:
                LOGGING_CONFIG['loggers'][logger].update({'level': cls._LOG_LEVELS[log_level]})

        # Configure the individual logger, name is the logger name provided during creation
        LOGGING_CONFIG['loggers'].update({name: {'handlers': ['console', 'file'],
                                                 'level': cls._LOG_LEVELS[log_level],
                                                 'propagate': False}})

        # Init the logging config
        log_config.dictConfig(LOGGING_CONFIG)

    @classmethod
    def create_logger(cls, name, config=None, data_folder=None):
        """Create logger.

        This method will create logger's to be used throughout teflo.

        :param data_folder: name of teflo's data folder
        :type data_folder: str
        :param name: Name for the logger to create.
        :type name: str
        :param config: Teflo config object.
        :type config: dict

        """

        # create log directory
        if config:
            log_dir = os.path.join(config['DATA_FOLDER'], 'logs')
        else:
            log_dir = os.path.join(data_folder, 'logs')

        try:

            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
        except OSError as ex:
            msg = 'Unable to create %s directory' % log_dir
            if ex.errno == errno.EACCES:
                msg += ', permission defined.'
            else:
                msg += ', %s.' % ex
            raise LoggerMixinError(msg)

        full_path = os.path.join(log_dir, 'teflo_scenario.log')

        # setup and initialize LOGGING_CONFIG
        cls.setup_logger(name, full_path, config)

    @property
    def logger(self):
        """Returns the default logger (teflo logger) object."""
        return getLogger(inspect.getmodule(inspect.stack()[1][0]).__name__)

    class ExceptionFilter(Filter):

        def filter(self, record):
            if record.getMessage().find('Traceback') != -1:
                return False
            else:
                return True


class TimeMixin(object):
    """Teflo's time mixin class.

    This class provides an easy interface for other teflo classes to save
    a start and end time. Once times are saved they can calculate the time
    delta between the two points in time.
    """
    _start_time = None
    _end_time = None
    _hours = 0
    _minutes = 0
    _secounds = 0

    def start(self):
        """Set the start time."""
        self._start_time = time()

    def end(self):
        """Set the end time."""
        self._end_time = time()

        # calculate time delta
        delta = self._end_time - self._start_time
        self.hours = delta // 3600
        delta = delta - 3600 * self.hours
        self.minutes = delta // 60
        self.seconds = delta - 60 * self.minutes

    @property
    def start_time(self):
        """Return the start time."""
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        """Set the start time.

        :param value: Start time.
        :type value: int
        """
        raise TefloError('You cannot set the start time.')

    @property
    def end_time(self):
        """Return the end time."""
        return self._end_time

    @end_time.setter
    def end_time(self, value):
        """Set the end time.

        :param value: End time.
        :type value: int
        """
        raise TefloError('You cannot set the end time.')

    @property
    def hours(self):
        """Return hours."""
        return self._hours

    @hours.setter
    def hours(self, value):
        """Set hours.

        :param value: Hours to set.
        :type value: int
        """
        self._hours = value

    @property
    def minutes(self):
        """Return minutes."""
        return self._minutes

    @minutes.setter
    def minutes(self, value):
        """Set minutes.

        :param value: Minutes to set.
        :type value: int
        """
        self._minutes = value

    @property
    def seconds(self):
        """Return seconds."""
        return self._secounds

    @seconds.setter
    def seconds(self, value):
        """Set seconds.

        :param value: Seconds to set.
        :type value: int
        """
        self._secounds = value


# TODO Remove this class if we do not find use for it
class FileLockMixin(object):
    """
    The FileLockMixin is designed to
    use file locks to be able to read/write
    to a file when multipleprocesses need to
    access the same file.
    """
    _lock_file = '/tmp/cbn.lock'
    _lock_sleep = 5
    _lock_timeout = 120

    @property
    def lock_file(self):
        return self._lock_file

    @lock_file.setter
    def lock_file(self, value):
        self._lock_file = value

    @property
    def lock_sleep(self):
        return self._lock_sleep

    @lock_sleep.setter
    def lock_sleep(self, value):
        self._lock_sleep = value

    @property
    def lock_timeout(self):
        return self._lock_timeout

    @lock_timeout.setter
    def lock_timeout(self, value):
        self._lock_timeout = value

    def acquire(self):
        self.cleanup_locks()
        if self._check_and_sleep():
            open(self._lock_file, 'w').close()

    def release(self):
        try:
            os.remove(self._lock_file)
        except OSError:
            raise

    def _check_and_sleep(self):

        attempts = 0
        total_attempts = self.lock_timeout / self.lock_sleep

        while os.path.exists(self.lock_file):
            if attempts < total_attempts:
                sleep(self.lock_sleep)
                attempts += 1
            else:
                raise TefloError('Timed out waiting for the lock to release')
        return True

    def cleanup_locks(self):
        if glob(os.path.join(os.path.dirname(self.lock_file), 'cbn_*')):
            for f in glob(os.path.join(os.path.dirname(self.lock_file), 'cbn_*')):
                if f != self.lock_file:
                    os.remove(f)


class TefloTask(LoggerMixin, TimeMixin):
    """
    This is the base class for every task created for Teflo framework.
    All instances of this class can be found within the ~teflo.tasks
    package.
    """

    __task_name__ = None
    __concurrent__ = True
    __task_id__ = ''

    def __init__(self, name=None, **kwargs):
        if name is not None:
            self.name = name

    def run(self):
        pass

    def __str__(self):
        return self.name

    @staticmethod
    def get_formatted_traceback():
        """Get traceback when exception is raised. Will log traceback as well.
        :return: Exception information.
        :rtype: tuple
        """

        return format_exc()


class TefloResource(LoggerMixin, TimeMixin):
    """
    This is the base class for every resource created for Teflo Framework.
    All instances of this class can be found within ~teflo.resources
    package.
    """
    _valid_tasks_types = []
    _req_tasks_methods = ['run']
    _fields = []

    def __init__(self, config=None, name=None, **kwargs):

        # every resource has a name
        self._name = name

        # A list of tasks that will be executed upon the reource.
        self._tasks = []

        # Teflo configuration
        self._config = config

        # every resource can have a optional description
        self._description = None

        # every resource can have optional labels
        self._labels = list()
        self._resource_id = gen_random_str(10)

    def __eq__(self, o) -> bool:
        return self.resource_id == o.resource_id

    def __hash__(self) -> int:
        return super().__hash__()

    @property
    def resource_id(self):
        return self._resource_id

    @resource_id.setter
    def resource_id(self, id):
        raise AttributeError('You cannot set resource_id after class is instantiated.')

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        raise AttributeError('You can set name after class is instantiated.')

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        raise AttributeError('You can set config after resource is created.')

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        raise AttributeError('You cannot set the resource description after '
                             'its class is instantiated.')

    @property
    def workspace(self):
        """Scenario workspace property.

        :return: scenario workspace folder
        :rtype: str
        """
        return str(self.config['WORKSPACE'])

    @workspace.setter
    def workspace(self, value):
        """Set workspace."""
        raise AttributeError('You cannot set the workspace directly. Only '
                             'the teflo object can.')

    @property
    def data_folder(self):
        """Data folder property.

        :return: resource data folder
        :rtype: str
        """
        return str(self.config['DATA_FOLDER'])

    @data_folder.setter
    def data_folder(self, value):
        """Set data folder."""
        raise AttributeError('You cannot set the data folder directly. Only '
                             'the teflo object can.')

    @property
    def labels(self):
        """labels property for the resource"""
        return self._labels

    @labels.setter
    def labels(self, value):
        """set labels property"""
        self._labels = self._set_labels(value)

    @labels.deleter
    def labels(self):
        """
        delete the labels property
        """
        del self._labels

    def _set_labels(self, labels):
        """
        Checks if the input is a comma separated string/string and converts it to a list
        :param labels: string of labels provided in the SDF
        :type labels: string or comma separated strings
        :rtype: list
        """
        if isinstance(labels, string_types):
            labels = labels.replace(' ', '').split(',')
        return labels

    def _add_task(self, t):
        """
        Add a task to the list of tasks for the resource
        """
        if t['task'] not in set(get_core_tasks_classes()):
            raise TefloResourceError(
                'The task class "%s" used is not valid.' % t['task']
            )
        self._tasks.append(t)

    def _extract_tasks_from_resource(self):
        """
        It checks every member of this class and compare if this is
        an instance of TefloTask.

        # TODO: better if we return a generator
        :return: list of tasks for this class
        """
        lst = []
        for name, obj in inspect.getmembers(self, inspect.isclass):
            if issubclass(obj, TefloTask):
                lst.append(name)
        return lst

    def load(self, data):
        """
        Given a dictionary of attributes, this function loads these
        attributes for this class.

        :param data: a dictionary with attributes for the resource
        """
        if data:
            for key, value in data.items():
                # name has precedence when coming from a YAML file
                # if name is set through name=, it will be overwritten
                # by the YAML file properties.
                if key == 'name':
                    self._name = value
                elif key == 'description':
                    self._description = value
                elif key in self._fields:
                    setattr(self, key, value)
            self.reload_tasks()

    def _get_task_constructors(self):
        return [getattr(self, "_construct_%s_task" % task_type)
                for task_type in self._valid_tasks_types]

    def reload_tasks(self):
        self._tasks = []
        for task_constructor in self._get_task_constructors():
            self._add_task(task_constructor())

    def dump(self):
        pass

    def get_tasks(self):
        return self._tasks

    def profile(self):
        raise NotImplementedError

    def validate(self):
        pass


class TefloProvider(LoggerMixin, TimeMixin):
    """Teflo Provider."""
    __provider_name__ = None

    def __init__(self):
        """Constructor."""
        self._req_params = []
        self._opt_params = []
        self._req_credential_params = []
        self._opt_credential_params = []
        self._credentials = {}

    @property
    def name(self):
        """Return the provider name."""
        return self.__provider_name__

    @name.setter
    def name(self, value):
        """Raises an exception when trying to set the name for the provider
        :param value: name
        """
        raise AttributeError('You cannot set provider name.')

    @property
    def req_params(self):
        """Return the required parameters."""
        return self._req_params

    @req_params.setter
    def req_params(self, value):
        """Set the required parameters."""
        self._req_params.extend(value)

    @property
    def opt_params(self):
        """Return the optional parameters."""
        return self._opt_params

    @opt_params.setter
    def opt_params(self, value):
        """Set the optional parameters."""
        self._opt_params.extend(value)

    @property
    def req_credential_params(self):
        """Return the required credential parameters."""
        return self._req_credential_params

    @req_credential_params.setter
    def req_credential_params(self, value):
        """Set the required credential parameters."""
        self._req_credential_params.extend(value)

    @property
    def opt_credential_params(self):
        """Return the optional credential parameters."""
        return self._opt_credential_params

    @opt_credential_params.setter
    def opt_credential_params(self, value):
        """Set the optional credential parameters."""
        self._opt_credential_params.extend(value)

    @property
    def credentials(self):
        """Return the credentials for the provider."""
        return self._credentials

    @credentials.setter
    def credentials(self, value):
        """Raise an exception when trying to set the credentials for the
        provider after the class has been instanciated. You should use the
        set_credentials method to set credentials.
        :param value: The provider credentials
        """
        raise ValueError('You cannot set provider credentials directly. Use '
                         'function ~TefloProvider.set_credentials')

    def set_credentials(self, cdata):
        """Set the provider credentials.
        :param cdata: The provider credentials dict
        """
        for p in self.req_credential_params:
            param = p[0]
            self._credentials[param] = cdata[param]

        for p in self.opt_credential_params:
            param = p[0]
            if param in cdata:
                self._credentials[param] = cdata[param]

    def validate_req_params(self, resource):
        """Validate the required parameters exists in the host resource.

        :param host: host resource
        :type host: object
        """
        for item in self.req_params:
            name = getattr(resource, 'name')
            param, param_type = item[0], item[1]
            msg = "Resource %s : required param '%s' " % (name, param)
            try:
                param_value = getattr(resource, 'provider_params')[param]
                self.logger.info(msg + 'exists.')

                if not type(param_value) in param_type:
                    self.logger.error(
                        '    - Type=%s, Required Type=%s. (ERROR)' %
                        (type(param_value), param_type))
                    raise TefloError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % getattr(resource, 'name')
                    )
            except KeyError:
                msg = msg + 'does not exist.'
                self.logger.error(msg)
                raise TefloError(msg)

    def validate_opt_params(self, resource):
        """Validate the optional parameters exists in the host resource.

        :param resource: host resource
        :type resource: object
        """
        for item in self.opt_params:
            name = getattr(resource, 'name')
            param, param_type = item[0], item[1]
            msg = "Asset %s : optional param '%s' " % (name, param)
            try:
                param_value = getattr(resource, 'provider_params')[param]
                self.logger.info(msg + 'exists.')

                if not type(param_value) in param_type:
                    self.logger.error(
                        '    - Type=%s, Optional Type=%s. (ERROR)' %
                        (type(param_value), param_type))
                    raise TefloError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % getattr(resource, 'name')
                    )
            except KeyError:
                self.logger.warning(msg + 'is undefined for resource.')

    def validate_req_credential_params(self, resource):
        """Validate the required credential parameters exists in the host.

        :param resource: host resource
        :type resource: object
        """
        for item in self.req_credential_params:
            name = getattr(resource, 'name')
            param, param_type = item[0], item[1]
            msg = "Resource %s : required credential param '%s' " % (name, param)
            try:
                provider = getattr(resource, 'provider')
                param_value = getattr(provider, 'credentials')[param]
                if param_value:
                    self.logger.info(msg + 'exists.')
                else:
                    raise TefloError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % getattr(resource, 'name')
                    )

                if not type(param_value) in param_type:
                    self.logger.error(
                        '    - Type=%s, Required Type=%s. (ERROR)' %
                        (type(param_value), param_type)
                    )
                    raise TefloError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % getattr(resource, 'name')
                    )
            except (AttributeError, KeyError):
                msg = msg + 'does not exist.'
                self.logger.error(msg)
                raise TefloError(msg)

    def validate_opt_credential_params(self, resources):
        """Validate the optional credential parameters exists in the host.

        :param resources: host resource
        :type resources: object
        """
        for item in self.opt_credential_params:
            name = getattr(resources, 'name')
            param, param_type = item[0], item[1]
            msg = "Resource %s : optional credential param '%s' " % (name, param)
            try:
                provider = getattr(resources, 'provider')
                param_value = getattr(provider, 'credentials')[param]
                if param_value:
                    self.logger.info(msg + 'exists.')
                else:
                    raise TefloError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % getattr(resources, 'name')
                    )
                if not type(param_value) in param_type:
                    self.logger.error(
                        '    - Type=%s, Optional Type=%s. (ERROR)' %
                        (type(param_value), param_type)
                    )
                    raise TefloError(
                        'Error occurred while validating required provider '
                        'parameters for resources %s' % getattr(resources, 'name')
                    )
            except (AttributeError, KeyError):
                self.logger.warning(msg + 'does not exist.')


class CloudProvider(TefloProvider):
    """Cloud provider class."""

    def __init__(self):
        super(CloudProvider, self).__init__()
        """Constructor."""
        self._req_params = [
            ('name', [str]),
            ('image', [str]),
            ('flavor', [str]),
            ('networks', [list])
        ]
        self._opt_params = [
            ('hostname', [str])
        ]


class PhysicalProvider(TefloProvider):
    """Physical provider class."""

    def __init__(self):
        super(PhysicalProvider, self).__init__()
        """Constructor."""
        pass


class ReportProvider(TefloProvider):
    """Report provider class."""

    def __init__(self):
        super(ReportProvider, self).__init__()
        """Constructor."""
        pass


class TefloOrchestrator(LoggerMixin, TimeMixin):
    # TODO Remove the teflo orchestrator class as it is no longer being used

    __orchestrator_name__ = None

    # all parameters that MUST be set for the orchestrator
    _mandatory_parameters = ()

    # additional parameters that can be set for the orchestrator
    _optional_parameters = ()

    def __init__(self):
        """Constructor."""
        self._action = None
        self._hosts = None
        self._status = 0

    def validate(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError

    @property
    def name(self):
        """Return the name of the orchestrator."""
        return self.__orchestrator_name__

    @name.setter
    def name(self, value):
        raise AttributeError('You cannot set name for the orchestrator.')

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, value):
        raise AttributeError('You cannot set the action the orchestrator will'
                             ' perform.')

    @property
    def hosts(self):
        return self._hosts

    @hosts.setter
    def hosts(self, value):
        raise AttributeError('Hosts cannot be set once the object is created.')

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @classmethod
    def _mandatory_parameters_set(cls):
        """
        Build a set of mandatory parameters
        :return: a set
        """
        return {'{}_{}'.format(cls.__orchestrator_name__, k) for k in cls._mandatory_parameters}

    @classmethod
    def get_mandatory_parameters(cls):
        """
        Get the list of the mandatory parameters
        :return: a tuple of the mandatory parameters.
        """
        return (param for param in cls._mandatory_parameters_set())

    @classmethod
    def _optional_parameters_set(cls):
        """
        Build a set of optional parameters
        :return: a set
        """
        return {'{}_{}'.format(cls.__orchestrator_name__, k) for k in cls._optional_parameters}

    @classmethod
    def get_optional_parameters(cls):
        """
        Get the list of the optional parameters
        :return: a tuple of the optional parameters.
        """
        return (param for param in cls._optional_parameters_set())

    @classmethod
    def _all_parameters_set(cls):
        """
        Build a set of all parameters
        :return: a set
        """
        return cls._mandatory_parameters_set()\
            .union(cls._optional_parameters_set())

    @classmethod
    def get_all_parameters(cls):
        """
        Return the list of all possible parameters for the provider.
        :return: a tuple with all parameters
        """
        return (param for param in cls._all_parameters_set())

    @classmethod
    def build_profile(cls, action):
        """Builds a dictionary with all the parameters for the orchestrator.

        :param action: action object
        :type action: object
        :return: dictionary with all orchestrator parameters
        :rtype: OrderedDict
        """
        profile = OrderedDict()
        for param in cls.get_all_parameters():
            profile.update({param: getattr(action, param, None)})
        return profile


class TefloExecutor(LoggerMixin, TimeMixin):

    __executor_name__ = None

    # all parameters that MUST be set for the executor
    _mandatory_parameters = ()

    # additional parameters that can be set for the executor
    _optional_parameters = ()

    # execute types the executor offers
    _execute_types = []

    def __init__(self, execute=None, host=None):
        """Constructor."""
        self._execute = execute
        self._hosts = host

    def validate(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError

    @property
    def name(self):
        """Return the name of the executor."""
        return self.__executor_name__

    @name.setter
    def name(self, value):
        raise AttributeError('You cannot set name for the executor.')

    @property
    def execute(self):
        return self._execute

    @execute.setter
    def execute(self, value):
        raise AttributeError('You cannot set the execute to run.')

    @property
    def hosts(self):
        return self._hosts

    @hosts.setter
    def hosts(self, value):
        raise AttributeError('Hosts cannot be set once the object is created.')

    @classmethod
    def _mandatory_parameters_set(cls):
        """
        Build a set of mandatory parameters
        :return: a set
        """
        return {'{}_{}'.format(cls.__executor_name__, k) for k in cls._mandatory_parameters}

    @classmethod
    def get_mandatory_parameters(cls):
        """
        Get the list of the mandatory parameters
        :return: a tuple of the mandatory parameters.
        """
        return (param for param in cls._mandatory_parameters_set())

    @classmethod
    def _optional_parameters_set(cls):
        """
        Build a set of optional parameters
        :return: a set
        """
        return {'{}_{}'.format(cls.__executor_name__, k) for k in cls._optional_parameters}

    @classmethod
    def get_optional_parameters(cls):
        """
        Get the list of the optional parameters
        :return: a tuple of the optional parameters.
        """
        return (param for param in cls._optional_parameters_set())

    @classmethod
    def _all_parameters_set(cls):
        """
        Build a set of all parameters
        :return: a set
        """
        return cls._mandatory_parameters_set()\
            .union(cls._optional_parameters_set())

    @classmethod
    def get_all_parameters(cls):
        """
        Return the list of all possible parameters for the provider.
        :return: a tuple with all parameters
        """
        return (param for param in cls._all_parameters_set())

    @classmethod
    def get_execute_types(cls):
        """
        Return the list of all execute_types for the executor.
        :return: a list with all execute_types
        """
        return cls._execute_types

    @classmethod
    def build_profile(cls, execute):
        """Builds a dictionary with all the parameters for the executor.

        :param execute: execute object
        :type execute: object
        :return: dictionary with all executor parameters
        :rtype: OrderedDict
        """
        profile = OrderedDict()
        for param in cls.get_all_parameters():
            if getattr(execute, param, None):
                profile.update({param: getattr(execute, param)})
        for param in cls.get_execute_types():
            if getattr(execute, param, None):
                profile.update({param: getattr(execute, param)})
        return profile


class TefloImporter(LoggerMixin, TimeMixin):

    # TODO Remove the teflo importer class as it is no longer being used
    # set the importer name
    __importer_name__ = None

    def __init__(self, report):
        """Constructor.

        The reporter requires a teflo report resource. This resource
        contains all the necessary elements that are needed to fulfill
        the reporting request by the reporter of choice.

        :param report: teflos report resource
        :type report: object
        """
        self._report = report

        # set commonly accessed data used by importers
        self.report_name = getattr(report, 'name')
        self.data_folder = getattr(report, 'data_folder')
        self.provider = getattr(getattr(report, 'provider'), 'name', 'dummy')
        self.provider_params = getattr(report, 'provider_params', {})
        self.provider_credentials = getattr(getattr(
            report, 'provider'), 'credentials', {})
        self.workspace = getattr(report, 'workspace')
        self.config = getattr(report, 'config')

        if not self.name and self.__class__.__name__ != 'TefloImporter':
            raise TefloImporterError(
                'Attribute __importer_name__ is None. Please set the '
                'attribute and retry creating an object from the class.'
            )

    @property
    def name(self):
        """Return the name of the importer."""
        return self.__importer_name__

    @name.setter
    def name(self, value):
        raise AttributeError('You cannot set name for the importer.')

    @property
    def report(self):
        return self._report

    @report.setter
    def report(self, value):
        raise AttributeError('You cannot set the report to run.')

    def import_artifacts(self):
        raise NotImplementedError

    def cleanup_artifacts(self):
        raise NotImplementedError

    def aggregate_artifacts(self):
        raise NotImplementedError

    def validate_artifacts(self):
        raise NotImplementedError


class TefloPlugin(LoggerMixin, TimeMixin):
    """Teflo gateway class.

        Base class that all teflo resource implmentations will use. This
        is to facilitate decoupling the interface from the implementation.
        """
    # set the plugin name
    __plugin_name__ = None

    __schema_file_path__ = ''

    @classmethod
    def get_schema_keys(cls):

        with open(cls.__schema_file_path__) as f:
            schema_data = f.read()
        return yaml.safe_load(schema_data).get('mapping').keys()

    @classmethod
    def build_profile(cls, resource):
        """Builds a dictionary with all the parameters for the resource.

        :param resource: resource object
        :type resource: object
        :return: dictionary with all plugin resource parameters
        :rtype: OrderedDict
        """
        profile = OrderedDict()
        for param in cls.get_schema_keys():
            if hasattr(resource, param):
                profile.update({param: getattr(resource, param, None)})
        return profile


class ProvisionerPlugin(TefloPlugin):
    """Teflo provisioner plugin class.

    Each provisioner implementation added into teflo requires that they
    inherit the porvisioner plugin class. This enforces that the
    required methods are implemented in the new provisioner class.
    Additional support/helper methods can be added to this class
    """

    def __init__(self, asset):
        """Constructor.

        Each asset resource is linked to a provisioner that knows how to
        work with the different providers. Along with the provider you will also
        have access to all the provider parameters needed to fulfill the
        provision request. (i.e. images, flavor, network, etc. depending on
        the provider).

        Common Attributes:
          - name: data_folder
            description: the runtime folder where all files/results are stored
            and archived for historical purposes.
            type: string

          - name: provider_params
            description: available data about the host to be created or
            deleted in the provider defined.
            type: dictionary

          - name: provider_credentials
            description: credentials for the provider associated to the host
            resource.
            type: dictionary

          - name: workspace
            description: workspace where teflo can access all files needed
            by the scenario in order to successfully run it.
            type: string

        There can be more information within the asset resource but the ones
        defined above are the most commonly ones used by provisioners.

        :param asset: teflo asset resource
        :type asset: object
        """
        self.asset = asset

        # set commonly accessed data used by provisioners
        self.data_folder = getattr(self.asset, 'data_folder')
        if hasattr(self.asset, 'provider'):
            self.provider_params = {k: v for k, v in self.asset.profile().items()
                                    if k not in getattr(self.asset, '_fields')}.get('provider')
        else:
            self.provider_params = {k: v for k, v in self.asset.profile().items()
                                    if k not in getattr(self.asset, '_fields')}
        self.provider_credentials = getattr(self.asset, 'credential', {})
        self.workspace = getattr(self.asset, 'workspace')
        self.config = getattr(self.asset, 'config')

    def create(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    def authenticate(self):
        raise NotImplementedError

    def validate(self):
        raise NotImplementedError


class ImporterPlugin(TefloPlugin):
    """Teflo reporter plugin class.

    Each reporter implementation added into teflo requires that they
    inherit the teflo reporter plugin class. This enforces that the
    required methods are implemented in the new plugin class.
    Additional support/helper methods can be added to this class.
    """

    def __init__(self, report):

        # set commonly accessed data used by importer_plugin
        self.report = report
        self.report_name = getattr(report, 'name')
        self.data_folder = getattr(report, 'data_folder')
        self.import_results = []

        # provider_params are plugin specific parameters
        # for backward compatibility, if provider key was used in the SDF get the provider attribute from report profile
        # if no provider key was used create teh provider_params  using the _fields attribute from report profile
        if hasattr(report, 'provider'):
            self.provider_params = self.report.profile().get('provider')
        else:
            self.provider_params = {k: v for k, v in self.report.profile().items()
                                    if k not in getattr(self.report, '_fields')}
        # credentials specific to plugin
        self.provider_credentials = getattr(self.report, 'credential', {})
        self.workspace = getattr(self.report, 'workspace')
        self.artifacts = []
        self.config = getattr(self.report, 'config')
        # build the config params that might be useful to plugin and instantiate
        if report.do_import:
            plugin_name = getattr(self.report, 'importer_plugin').__plugin_name__
            config_params = dict()
            for k, v in self.config.items():
                if plugin_name.upper() in k:
                    config_params[k.lower()] = v
            self.config_params = config_params
        else:
            self.config_params = {}

    def aggregate_artifacts(self):
        raise NotImplementedError

    def import_artifacts(self):
        raise NotImplementedError

    def cleanup_artifacts(self):
        raise NotImplementedError


class OrchestratorPlugin(TefloPlugin):
    """Teflo orchestrator gateway class.

    Each orchestrator implementation added into teflo requires that they
    inherit the teflo orchestrator plugin class. This enforces that the
    required methods are implemented in the new plugin class.
    Additional support/helper methods can be added to this class.
    """

    def __init__(self, action):
        """Constructor."""
        self._action = action
        self._hosts = self.action.hosts
        self._status = 0
        self.action_name = self.action.name
        self.config = self.action.config
        self.workspace = self.action.workspace

    def validate(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError

    @property
    def name(self):
        """Return the name of the orchestrator."""
        return self.__plugin_name__

    @name.setter
    def name(self, value):
        raise AttributeError('You cannot set name for the orchestrator.')

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, value):
        raise AttributeError('You cannot set the action the orchestrator will'
                             ' perform.')

    @property
    def hosts(self):
        return self._hosts

    @hosts.setter
    def hosts(self, value):
        raise AttributeError('Hosts cannot be set once the object is created.')

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value


class ExecutorPlugin(TefloPlugin):
    """Teflo executor plugin class.

    Each executor implementation added into teflo requires that they
    inherit the teflo executor plugin class. This enforces that the
    required methods are implemented in the new plugin class.
    Additional support/helper methods can be added to this class.
    """

    def __init__(self, execute):
        """Constructor."""
        self._execute = execute
        self._hosts = self.execute.hosts
        self.execute_name = self.execute.name
        self._status = 0
        self.config = self.execute.config
        self.workspace = self.execute.workspace

    def validate(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError

    @property
    def name(self):
        """Return the name of the executor."""
        return self.__plugin_name__

    @name.setter
    def name(self, value):
        raise AttributeError('You cannot set name for the executor.')

    @property
    def execute(self):
        return self._execute

    @execute.setter
    def execute(self, value):
        raise AttributeError('You cannot set the execute to run.')

    @property
    def hosts(self):
        return self._hosts

    @hosts.setter
    def hosts(self, value):
        raise AttributeError('Hosts cannot be set once the object is created.')

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value


class NotificationPlugin(TefloPlugin):
    """Teflo notification plugin class.

    Each notification implementation added into teflo requires that they
    inherit the teflo notification plugin class. This enforces that the
    required methods are implemented in the new plugin class.
    Additional support/helper methods can be added to this class.
    """

    def __init__(self, notification):
        self.notification = notification
        self.config = getattr(notification, 'config')

    def notify(self):
        raise NotImplementedError

    def validate(self):
        raise NotImplementedError

    def get_credential_params(self):

        crd = dict()

        if getattr(self.notification, 'credential'):
            for item in self.config['CREDENTIALS']:
                if item['name'] == getattr(self.notification, 'credential'):
                    crd = item
                    break

        return crd

    def get_config_params(self):

        cfg = dict()
        for item in self.config['NOTIFICATIONS']:
            if item['name'] == getattr(self.notification, 'notifier').__plugin_name__:
                cfg = item
                break
        return cfg


class SingletonMixin(object):
    """ This class helps in creating a singleton object for a class,
    so that object is created only once"""

    __singleton_lock = threading.Lock()
    __singleton_instance = None

    @classmethod
    def get_instance(cls, *args, **kwargs):
        # check for the singleton instance
        if not cls.__singleton_instance:
            with cls.__singleton_lock:
                if not cls.__singleton_instance:
                    cls.__singleton_instance = cls(*args, **kwargs)

        # return the singleton instance
        return cls.__singleton_instance


class Inventory(LoggerMixin, FileLockMixin, SingletonMixin):
    """This class primary responsibility is handling creating/deleting the
    ansible inventory for the teflo ansible action.
    """

    def __init__(self, config, uid, inv_dump=None):
        """Constructor.
        :param config: teflo's config
        :type static_inv_dir: dict
        :param uid: unique id created for teflo data folder
        :type uid: str
        :param inv_dump: multipart string from provisioners that generate their own inventory layout
        :type inv_dump: str
        """

        self.config = config
        self.results_folder = self.config['RESULTS_FOLDER']
        self.uid = uid
        self.lock_file = '/tmp/cbn_%s.lock' % self.uid
        self.static_inv_dir = self.config['INVENTORY_FOLDER']
        self.inv_dump = inv_dump
        self._create_inv_dir()

    def _create_inv_dir(self):
        # set & create the inventory directory if not already present
        if 'inventory' in (os.path.basename(self.static_inv_dir),
                           os.path.basename(os.path.dirname(self.static_inv_dir))):
            self.inv_dir = os.path.expandvars(
                os.path.expanduser(self.static_inv_dir)
            )
        else:
            self.inv_dir = os.path.expandvars(os.path.expanduser(os.path.join(self.static_inv_dir, 'inventory')))
        if not os.path.isdir(os.path.abspath(self.inv_dir)):
            os.makedirs(self.inv_dir)

        # Setting config with updated static_inv folder
        self.config['INVENTORY_FOLDER'] = self.inv_dir

        # set the master inventory
        self.master_inv = os.path.join(self.inv_dir, 'inventory-%s' % self.uid)

    def create_inventory(self, all_hosts):
        """Create the master ansible inventory.
        This method will create a master inventory which contains all the
        hosts in the given scenario. Each host will have a group/group:vars.
        """
        try:

            # get the lock
            self.acquire()
            # check for any old master inventories and delete them.
            # Check both the static inv folder as well as the .results/inventory folder for old master inventories

            inv_results_dir = os.path.join(self.results_folder, 'inventory/inventory*')
            stat_inv_dir = os.path.join(self.inv_dir, 'inventory*')
            for path in [stat_inv_dir, inv_results_dir]:
                if glob(path):
                    for f in glob(path):
                        if f != self.master_inv:
                            os.remove(f)

            if self.inv_dump:
                self.write_inventory()
                return

            # create parser object, raw config parser allows keys with no values
            config = RawConfigParser(allow_no_value=True)
            # disable default behavior to set values to lower case
            config.optionxform = str

            # do not create master inventory if already exists
            # load it and keep building upon it
            if os.path.exists(self.master_inv):
                with open(self.master_inv) as f:
                    config.read_file(f)

            # Sort the list of hosts so that if N number of hosts are getting
            # added to same host group the order is predictable.
            for host in sorted(all_hosts, key=lambda h: h.name):
                section = host.name
                section_vars = '%s:vars' % section
                if hasattr(host, 'groups') or hasattr(host, 'ip_address'):
                    for sect in getattr(host, 'groups', []):
                        host_section = sect + ":children"
                        if host_section in config.sections():
                            config.set(host_section, host.name)
                        else:
                            config.add_section(host_section)
                            config.set(host_section, host.name)

                    # create section(s)
                    for item in [section, section_vars]:
                        config.add_section(item)

                    # add ip address to group
                    if getattr(host, 'ip_address', None):
                        if isinstance(host.ip_address, dict):
                            config.set(section, host.ip_address.get('public'))
                        elif isinstance(host.ip_address, list):
                            [config.set(section, ip) for ip in host.ip_address]
                        elif isinstance(host.ip_address, string_types):
                            config.set(section, host.ip_address)

                    # add host vars
                    for k, v in host.ansible_params.items():
                        if k in ['ansible_ssh_private_key_file']:
                            v = os.path.join(getattr(host, 'workspace'), v)
                        if k == 'ansible_port':
                            v = str(v)
                        config.set(section_vars, k, v)

            # write the inventory
            self.write_inventory(config)

        except Exception as ex:
            raise ex
        finally:
            self.release()

        self.logger.debug("Master inventory content")
        self.log_inventory_content(config)

    def log_inventory_content(self, parser):
        # log the inventory file content
        cfg_str = ''
        new_section = False
        for section in parser.sections():
            if new_section:
                cfg_str += '\n'
            cfg_str += '[' + section.strip() + ']' + '\n'
            new_section = False
            for k, v in parser.items(section):
                if v:
                    cfg_str += k + '=' + v
                else:
                    cfg_str += k
                cfg_str += '\n'
            new_section = True
        self.logger.debug('\n' + cfg_str)

    def write_inventory(self, config=None):
        # generic method to write out the inventory file
        if config:
            with open(self.master_inv, 'w') as f:
                config.write(f)
        else:
            with open(self.master_inv, 'w+') as inv_file:
                inv_file.write(self.inv_dump)
