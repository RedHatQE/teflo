Configure Teflo
================

This is a mandatory configuration file, where you set your credentials, and
there are many optional settings to help you adjust your usage of Teflo.
The credentials of the configuration file is the only thing that
is mandatory.  Most of the other default configuration settings should be
sufficient; however, please read through the options you have.

Where it is loaded from (using precedence low to high):

#. /etc/teflo/teflo.cfg
#. ./teflo.cfg (current working directory)
#. TEFLO_SETTINGS environment variable to the location of the file

.. important::

   It is important to realize if you have a configuration file set using
   both options, the configuration files will be combined, and common
   key values will be overridden by the higher precedent option, which will
   be the TEFLO_SETTINGS environment variable.

Configuration example (with all options):

.. literalinclude:: ../../examples/docs-usage/configuration.txt


.. note::

    Many of the configuration options can be overridden by passing cli options when running
    teflo. See the options in the running teflo `example. <quickstart.html#run>`__

Using Jinja Variable Data
~~~~~~~~~~~~~~~~~~~~~~~~~

Teflo uses Jinja2 template engine to be able to template variables
within the teflo.cfg file. Teflo allows template variable data to be
set as environmental variables

Here is an example teflo.cfg file using Jinja to template some variable data:

.. code-block:: bash

    [credentials:openstack]
    auth_url=<auth_url>
    username={{ OS_USER }}
    password={{ OS_PASSWORD }}
    tenant_name={{ OS_TENANT }}
    domain_name=redhat.com

    [task_concurrency]
    provision=True
    report=False
    orchestrate={{ ORC_TASK_CONCURRENCY }}

Prior to running teflo, the templated variables will have to be exported

.. code-block:: bash

    export OS_USER=user1
    export OS_PASSWORD=password
    export OS_TENANT=project1
    export ORC_TASK_CONCURRENCY=True



inventory_folder
~~~~~~~~~~~~~~~~

The **inventory_folder** option is not a required option but it is important enough to note its usage.
By default teflo will create an inventory directory containing ansible inventory files in its data
directory. These are used during orchestration and execution. Refer to the `Teflo Output <output.html>`__
page.

Some times this is not desired behavior. This option allows a user to specify a static known directory
that Teflo can use to place the ansible inventory files. If the specified directory does not exist,
teflo will create it and place the ansible inventory files. If it does, teflo will only place the
ansible files in the directory. Teflo will then use this static directory during orchestrate and execution.

task_concurrency
~~~~~~~~~~~~~~~~

The **task_concurrency** option is used to control how tasks are executed by Teflo. Whether it should be sequential
or in parallel/concurrent. Below is the default execution type of each of the Teflo tasks:

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Concurrent
        - Type

    *   - validate
        - True
        - String

    *   - provision
        - True
        - String

    *   - orchestrate
        - False
        - String

    *   - execute
        - False
        - String

    *   - report
        - False
        - String

There are cases where it makes sense to adjust the execution type. Below are some examples:

There are cases when provisioning assets of different types that there might be an inter-dependency so executing
the tasks in parallel will not suffice, i.e. provision a virtual network and a VM attached to that network.
In that case, set the **provision=False** and arrange the assets in the scenario descriptor file in
the proper sequential order.

There are cases when you need to import the same test artifact into separate reporting systems but one reporting
systems needs the data in the test artifact to be modified with metadata before it can be imported.
i.e modify and import into Polarion with Polarion metadata and then import that same artifact into Report Portal.
In that case, set the **report=False** and arrange the resources defined in the scenario descriptor file in the
proper sequential order.

There could be a case where you would like to execute two different test suites concurrently because they have
no dependency on each other or there is no affect to each other. In that case, set the **execute=True** to have
them running concurrently.
