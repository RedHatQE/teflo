Install Teflo
==============

Requirements
++++++++++++

Your system requires the following packages to install teflo:

.. code-block:: bash

    # To install git using dnf package manager
    $ sudo dnf install -y git

    # To install git using yum package manager
    $ sudo yum install -y git

    # Install python pip: https://pip.pypa.io/en/stable/installing
    $ sudo curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    $ sudo python get-pip.py

    # Recommend installation of virtualenv using pip
    $ sudo pip install virtualenv

.. note::

   To install Teflo pip version 18.1 or higher is required

Install
+++++++

Install teflo from source:

.. code-block:: bash

    # for ansible modules requiring selinux, you will need to enable system site packages
    $ virtualenv --system-site-packages teflo
    $ source teflo/bin/activate
    (teflo) $ pip install git+https://github.com/RedHatQE/teflo.git

Post Install
++++++++++++

If you require teflo to interface with beaker using the bkr-client provisioner,
you will need to enable the beaker client repository/install the beaker-client package.
Teflo uses the beaker client package to provision physical machines in beaker.

.. code-block:: bash

    # https://beaker-project.org/download.html
    $ sudo curl -o /etc/yum.repos.d/bkr-client.repo \
    https://beaker-project.org/yum/beaker-client-<DISTRO>.repo

    # To install beaker-client using dnf package manager
    $ sudo dnf install -y beaker-client

    # To install beaker-client using yum package manager
    $ sudo yum install -y beaker-client

.. note::

    Beaker-client could be installed from PyPI rather than RPM. Installing from
    pip fails in Python 3. Beaker client is not compatible with Python 3
    currently. Once compatibile it can be installed with teflo. Teflo is Python 3 compatible.


Teflo External Plugin Requirements
++++++++++++++++++++++++++++++++++

Teflo is able to use external tools using its plugins. These plugins need to be installed
separately.

Users can develop Teflo has plugins for provisioners, orchestrators, executors, importers and notifiers.
Following are the plugins currently developed and supported by Teflo

Provisioner Plugins
-------------------

Teflo_Linchpin_Plugin
~~~~~~~~~~~~~~~~~~~~~

This plugin can be use to provision using the Linchpin tool.
The Linchpin plugin will be available as an extra. To install Linchpin certain requirements need to be
met so that it can be installed correctly. Please refer to the
`before install section <https://redhatqe.github.io/teflo_linchpin_plugin/docs/user.html#before-install>`__
of the plugin documentation on how to install them.

Once installed, you can install Linchpin from Teflo

.. code-block:: bash

    $ pip install teflo[linchpin-wrapper]

Once Linchpin_Plugin is installed, you will get support for all providers that linchpin supports. Although there are
some providers that require a few more dependencies to be installed. Refer to the
`post-install section <https://redhatqe.github.io/teflo_linchpin_plugin/docs/user.html#post-install>`__
of the plugin document for methods on how to install those dependencies.

Openstack_Client_Plugin
~~~~~~~~~~~~~~~~~~~~~~~
This plugin is used to Provision openstack assets using openstack-client tool
This plugin is also available as extra. To install this  plugin do the following
Refer `here <https://redhatqe.github.io/teflo_openstack_client_plugin/docs/user.html>`__ to get more
information on how to use the plugin

.. code-block:: bash

    $ pip install teflo[openstack-client-plugin]

.. _cbn_importer_plugin:

Importer Plugins
----------------

Teflo_Polarion_Plugin
~~~~~~~~~~~~~~~~~~~~~

This plugin allows teflo to send test results to Polarion tool. This plugin allows teflo
to import xunit files to Polarion by using the Polar library. Polar library helps converts the generic
xUnit file by applying Polarion specific tags and import them to Polarion and monitor their progress
teflo_polarion_plugin uses the parameters declared in the Teflo's Scenario Descriptor File Report section
to send the xunit files to Polarion

.. note::

    This plugin is meant for Internal RED HAT use and is not available publicly yet


Teflo_Rppreproc_Plugin
~~~~~~~~~~~~~~~~~~~~~~

This plugin allows teflo to send test results to Report Portal tool.
Based on the input provided by Teflo's Scenario Descriptor File (SDF),the teflo_rppreproc_plugin
validates the config file for report portal client if provided else creates one
using the other parameters in the SDF, creates appropriate payload (logs and attachements)for
the report portal client and uses Teflo's helper methods to send the payload to the report portal client
by running the rp_preproc commands

.. note::

    This plugin is meant for Internal RED HAT use and is not available publicly yet


Notification Plugins
--------------------

Teflo_Webhooks_Notification_Plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This plugin is used to notify based users using chat applications gchat and slack.
Please review the `repo documentation <https://redhatqe.github.io/teflo_webhooks_notification_plugin/user.html>`__
and how to use the plugin.Please review `Teflo's notification triggers <./definitions/notifications.html#triggers>`__
to get more info on using Teflo`s notification feature

.. _cbn_plugin_matrix:

Teflo Matrix for Plugins
+++++++++++++++++++++++++

The table below lists out the released Teflo version and supported teflo plugin versions. This matrix will track
n and n-2 teflo releases

.. list-table:: Teflo plugin matrix for n and n-2 releases
    :widths: auto
    :header-rows: 1

    *   - Teflo Release
        - 1.0.0
        - 1.0.1

    *   - Rppreproc Plugin
        - 1.0.0
        - 1.0.0

    *   - Polarion Plugin
        - 1.0.0
        - 1.0.0

    *   - Linchpin Plugin
        - 1.0.0
        - 1.0.1

    *   - Openstack Client Plugin
        - 1.0.0
        - 1.0.0

    *   - Webhooks_Notification_Plugin
        - 1.0.0
        - 1.0.0

    *   - Polar
        - 1.2.1
        - 1.2.1

    *   - Rp_preproc
        - 0.1.3
        - 0.1.3
