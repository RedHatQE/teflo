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
    teflo.resources.notification

    Module used for building teflo host compounds. Hosts are the base to a
    scenario object. The remaining compounds that make up a scenario are
    processed against the hosts defined.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from collections import OrderedDict
from ..core import TefloResource, TefloResourceError
from ..tasks import NotificationTask, ValidateTask
from ..helpers import get_notification_plugin_list, get_notifier_plugin_class
from ..notifiers import Notifier
from ..constants import TASKLIST
from .._compat import string_types


class Notification(TefloResource):

    _valid_tasks_types = ['validate', 'notification']

    _fields = [
        'name',
        'description',
        'notifier',
        'credential',
        'on_success',
        'on_failure',
        'on_tasks',
        'on_start',
        'on_demand',
        "validate_timeout",
        "notification_timeout"
    ]

    def __init__(self,
                 config=None,
                 name=None,
                 parameters={},
                 validate_task_cls=ValidateTask,
                 notification_task_cls=NotificationTask,
                 **kwargs):
        """Constructor.

        :param config: teflo configuration
        :type config: dict
        :param name: host resource name
        :type name: str
        :param parameters: content which makes up the host resource
        :type parameters: dict
        :param notification_task_cls: teflos notification task class
        :type notification_task_cls: object
        :param kwargs: additional key:value(s)
        :type kwargs: dict
        """
        super(Notification, self).__init__(config=config, name=name, **kwargs)
        # set the timeout for VALIDATE
        try:
            if parameters.get('validate_timeout') is not None:
                self._validate_timeout = parameters.pop("validate_timeout")
            else:
                self._validate_timeout = config["TIMEOUT"]["VALIDATE"]
        except TypeError:
            self.logger.error("No teflo.cfg found,  so no timeout will be set")
            self._validate_timeout = 0

        # set the timeout for NOTIFICATION
        try:
            if parameters.get('notification_timeout') is not None:
                self._notification_timeout = parameters.pop("notification_timeout")
            else:
                self._notification_timeout = config["TIMEOUT"]["NOTIFICATION"]
        except TypeError:
            self.logger.error("No teflo.cfg found,  so no timeout will be set")
            self._notification_timeout = 0

        # set the resource name
        if name is None:
            self._name = parameters.pop('name', None)
            if self._name is None:
                raise TefloResourceError('Unable to build notification object. Name'
                                          ' field missing!')
        else:
            self._name = name

        self._description = parameters.pop('description', None)

        notifier = parameters.pop('notifier', 'email-notifier')
        if notifier in get_notification_plugin_list():
            self._notifier = get_notifier_plugin_class(notifier)
        else:
            raise TefloResourceError('The specified notification, %s, does not exist.' % notifier)

        self._scenario = None

        if 'on_success' not in parameters and 'on_failure' not in parameters:
            self._on_success = True
            self._on_failure = True
        elif 'on_success' not in parameters or 'on_failure' not in parameters:
            self._on_success = parameters.pop('on_success', False)
            self._on_failure = parameters.pop('on_failure', False)
        else:
            self._on_success = parameters.pop('on_success')
            self._on_failure = parameters.pop('on_failure')

        self._on_tasks = parameters.pop('on_tasks', TASKLIST)

        if isinstance(self._on_tasks, string_types):
            self._on_tasks = self._on_tasks.replace(' ', '').split(',')

        self._on_start = parameters.pop('on_start', False)

        self._on_demand = parameters.pop('on_demand', False)

        if self.on_start:
            self._on_failure = None
            self._on_success = None

        if self.on_demand:
            self._on_tasks = None
            self._on_success = None
            self._on_failure = None
            self._on_start = None

        self._credential = parameters.pop('credential', None)

        # load in rest of parameters
        for p, v in parameters.items():
            setattr(self, p, v)

        # set the teflo task classes for the resource
        self._validate_task_cls = validate_task_cls
        self._notification_task_cls = notification_task_cls

        # reload construct task methods
        self.reload_tasks()

        # load the parameters set into the object itself
        if parameters:
            self.load(parameters)

    def __set_feature_toggles_(self):

        self._feature_toggles = None
        for item in self.config['TOGGLES']:
            if item['name'] == 'notification':
                self._feature_toggles = item

    @property
    def notifier(self):
        """notifier property.

        :return: notification type
        :rtype: str
        """
        return self._notifier

    @notifier.setter
    def notifier(self, value):
        """Set notifier property."""
        raise AttributeError('Notifier property cannot be set.')

    @property
    def on_success(self):
        """
        on_success property

        :return: bool
        """
        return self._on_success

    @on_success.setter
    def on_success(self, value):
        """Set on_success property."""
        raise AttributeError('On_success property cannot be set.')

    @on_success.deleter
    def on_success(self):
        """delete on_success property."""
        del self._on_success

    @property
    def on_failure(self):
        """
        on_failure property

        :return: bool
        """
        return self._on_failure

    @on_failure.setter
    def on_failure(self, value):
        """Set on_failure property."""
        raise AttributeError('On_failure property cannot be set.')

    @on_failure.deleter
    def on_failure(self):
        """delete on_failure property."""
        del self._on_failure

    @property
    def on_tasks(self):
        """
        on_tasks property

        :return: list
        """
        return self._on_tasks

    @on_tasks.setter
    def on_tasks(self, value):
        """Set on_task property."""
        raise AttributeError('On_tasks property cannot be set.')

    @on_tasks.deleter
    def on_tasks(self):
        """delete on_task property."""
        del self._on_tasks

    @property
    def on_start(self):
        """
        on_start property

        :return: bool
        """
        return self._on_start

    @on_start.setter
    def on_start(self, value):
        """Set on_start property."""
        raise AttributeError('On_start property cannot be set.')

    @on_start.deleter
    def on_start(self):
        """delete on_start property."""
        del self._on_start

    @property
    def on_demand(self):
        """
        on_demand property

        :return: bool
        """
        return self._on_demand

    @on_demand.setter
    def on_demand(self, value):
        """Set on_demand property."""
        raise AttributeError('On_demand property cannot be set.')

    @on_demand.deleter
    def on_demand(self):
        """delete on_demand property."""
        del self._on_demand

    @property
    def credential(self):
        """credential property.

        :return: credential
        :rtype: str
        """
        return self._credential

    @credential.setter
    def credential(self, value):
        """Set credential property."""
        raise AttributeError('You cannot set the asset credential after notification '
                             'class is instantiated.')

    @credential.deleter
    def credential(self):
        """
        delete the credential property
        :return:
        """
        del self._credential

    @property
    def scenario(self):
        """
        scenario property

        :return: object
        """
        return self._scenario

    @scenario.setter
    def scenario(self, value):
        """Set the scenario property."""
        self._scenario = value

    def profile(self):
        """Builds a profile for the notification resource.

            :return: the notification profile
            :rtype: OrderedDict
            """

        profile = OrderedDict()
        filtered_attr = {k: v for k, v in vars(self).items() if not k.startswith('_') and not k.startswith('scenario')}

        # update asset fields
        for f in self._fields:
            if hasattr(self, f) and f == 'notifier':
                profile.update({'notifier': getattr(
                    self.notifier, '__plugin_name__')})
                continue
            if hasattr(self, f) and getattr(self, f) is not None:
                profile.update({f: getattr(self, f)})

        profile.update(filtered_attr)

        return profile

    def validate(self):
        """Validate the notification."""

        # TODO This will change once we get everything over to use the plugin model
        getattr(Notifier(self), 'validate')()

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

    def _construct_notification_task(self):
        """Constructs the notification task associated to the resource.

        :returns: notification task definition
        :rtype: dict
        """
        task = {
            'task': self._notification_task_cls,
            'name': str(self.name),
            'resource': self,
            'msg': 'triggering %s' % self.name,
            'methods': self._req_tasks_methods,
            "timeout": self._notification_timeout
        }
        return task
