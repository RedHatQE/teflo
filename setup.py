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
Test Execution Framework Libraries and Objects (TEFLO) an orchestration software.
"""
import os
import re
import io

from setuptools import setup, find_packages

ROOT = os.path.dirname(__file__)
VERSION_RE = re.compile(r'''__version__ = ['"]([a-zA-Z0-9.]+)['"]''')


def get_version():
    init = open(os.path.join(ROOT, 'teflo', '__init__.py')).read()
    return VERSION_RE.search(init).group(1)


# reading description from README.rst
with io.open(os.path.join(ROOT, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='teflo',
    version=get_version(),
    license='GPLv3',
    author='Red Hat Inc.',
    description='Test Execution Framework Libraries and Objects. It is an orchestration software that controls the flow of a set of testing scenarios.',
    long_description=long_description,
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.6",
    install_requires=[
        'ansible>=2.5.0',
        'apache-libcloud==2.2.0',
        "blaster>=0.3.0",
        'Click>=6.7',
        'ipaddress',
        'Jinja2>=2.10',
        'pykwalify>=1.6.0',
        'python-cachetclient',
        'ruamel.yaml>=0.15.64',
        'paramiko>=2.4.2',
        'ssh-python==0.9.0',
        'requests>=2.20.1',
        'urllib3<1.26',
        'termcolor>=1.1.0'
    ],
    extras_require={
                    'linchpin-wrapper': ['teflo_linchpin_plugin'],
                    'openstack-client-plugin': ['teflo_openstack_client_plugin'],
                    'terraform-plugin': ['teflo-terraform-plugin'],
                    'webhook-notification-plugin': ['teflo-webhooks-notification-plugin'],
                    'notify-service-plugin': ['teflo-notify-service-plugin']

                    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
    ],
    entry_points={
        'console_scripts': ['teflo=teflo.cli:teflo'],
        'provider_plugins': [
            'aws_provider = teflo.providers:AwsProvider',
            'beaker_provider = teflo.providers:BeakerProvider',
            'libvirt_provider = teflo.providers:LibvirtProvider',
            'openstack_provider = teflo.providers:OpenstackProvider'
             ],
        'provisioner_plugins': [
            'beaker_client = teflo.provisioners.ext:BeakerClientProvisionerPlugin',
            'openstack_libcloud = teflo.provisioners.ext:OpenstackLibCloudProvisionerPlugin'
        ],
        'orchestrator_plugins': [
            'ansible = teflo.orchestrators.ext:AnsibleOrchestratorPlugin'
        ],
        'executor_plugins': [
            'runner = teflo.executors.ext:AnsibleExecutorPlugin'
        ],
        'notification_plugins': [
            'email-notifier = teflo.notifiers.ext:EmailNotificationPlugin'
        ]

    }
)
