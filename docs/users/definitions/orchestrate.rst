Orchestrate
===========

Teflo's orchestrate section declares the configuration to be be performed in
order to test the systems properly.

First lets go over the basic structure that defines a configuration task.

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 1-6

The above code snippet is the minimal structure that is required to create a
orchestrate task within teflo. This task is translated into a teflo action
object which is part of the teflo compound. You can learn more about this at
the `architecture <../../developers/architecture.html>`_ page. Please see the table below to
understand the key/values defined.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required
        - Default

    *   - name
        - The name of the action you want teflo to execute
        - String
        - Yes
        - n/a

    *   - description
        - A description of what the resource is trying to accomplish
        - String
        - No
        - n/a

    *   - orchestrator
        - The orchestrator to use to execute the action (name) you defined
          above
        - String
        - No (best practice to define this!)
        - ansible

    *   - hosts
        - The list of hosts where teflo will execute the action against
        - List
        - Yes
        - n/a

Hosts
-----

You can associate hosts to a given orchestrate task a couple of different ways.
First is to define your hosts in a comma separated string.

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 9-14

You can also define your hosts as a list.

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 16-23

It can become tedious if an orchestrate task needs to be performed on multiple
or all hosts within the scenario and you have many hosts declared. Teflo
provides you with the ability to run against a group of hosts or all hosts.
To run against multiple hosts use the name defined in the **groups** key for
your hosts or use **all** to run against all hosts.  This eliminates the need
to define every host per multiple tasks. It can be either in string or list
format.

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 25-30

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 32-37


Re-running Tasks and Status Code
--------------------------------

You may notice in your results.yml that each orchestrate block has a new parameter

.. code-block:: yaml

    status: 0

When teflo runs any of the defined orchestration tasks successfully a status code of 0
will be set. If an orchestration task fails, teflo will set the status to 1. The next time
you re-run the Orchestration task teflo will check for any orchestration tasks with a failed
status and start the orchestration process from there.

This is useful when you have a long configuration process and you don't want to start over
all the way from the beginning. If at some point you would rather have the orchestration process
start from the beginning, you can modify the status code back 0.

----

Since teflos development model is plug and play. This means different
orchestrator's could be used to execute configuration tasks declared.
Ansible is Teflo's default orchestrator. Its information can be found below.

.. _ans:

Ansible
-------

Ansible is teflos default orchestrator. As we mentioned above each task has
a given **name** (action). This name is the orchestrate task name.

Teflo uses these keywords to detect to ansible playbook, script or shell command **ansible_playbook, ansible_script, ansible_shell**
respectively.
Please refer :ref:`here<ans_keys>` to get an idea on how to use the keys


In addition to the required orchestrate base keys, there are more you can define based
on your selected orchestrator.Lets dive into them..

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required
        - Default

    *   - ansible_options
        - Additional options to provide to the ansible orchestrator regarding
          the task (playbook) to be executed
        - Dictionary
        - No
        - n/a

    *   - ansible_galaxy_options
        - Additional options to provide to the ansible orchestrator regarding
          ansible roles and collections
        - Dictionary
        - No
        - n/a

    *   - ansible_script
        - scribt to be executed
        - Dictionary
        - (Not required; however, one of the following must be defined:
          ansible_shell/ansible_script/ansible_playbook)
        - False

    *   - ansible_playbook
        - playbook to be run.
        - dictionary
        - (Not required; however, one of the following must be defined:
          ansible_shell/ansible_script/ansible_playbook)
        - False

    *   - ansible_shell
        - shell commands to be run.
        - list of dictionary
        - (Not required; however, one of the following must be defined:
          ansible_shell/ansible_script/ansible_playbook)
        - False

The table above describes additional key:values you can set within your
orchestrate task. Each of those keys can accept additional key:values.


Teflo Ansible Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the teflo configuration file, you can set some options related to ansible.
These values should be set in the **[orchestrator:ansible]** section of the
teflo.cfg file.  The following are the settings.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Default

    *   - log_remove
        - configuration option to delete the ansible log file after
          configuration is complete.  Either way the ansible log
          will be moved to the user's output directory.
        - By default this is set to true to delete it.

    *   - verbosity
        - configuration option to set the verbosity of ansible.
        - Teflo sets the ansible verbosity to the value provided
          by this option. If this is not set then, teflo will
          set the verbosity based on teflo's logging level.
          If logging level is 'info' (default) ansible verbosity is
          set to **None** else if logging level is 'debug' then ansible
          verbosity is 'vvvv'.

.. note::
        If incorrect value for verbosity is set in teflo.cfg, Teflo changes the verbosity based on
        teflo's logging level

Ansible Configuration
~~~~~~~~~~~~~~~~~~~~~

It is highly recommended that every scenario that uses Ansible provide their
own ansible.cfg file. This can be used for specific connection requirements,
logging, and other settings for the scenario.  The following is an example
of a configuration file that can be used as a base.

.. code-block:: yaml

   [defaults]
   # disable strict SSH key host checking
   host_key_checking = False

   # filter out logs that are not ansible related
   log_filter = paramiko,pykwalify,teflo,blaster,urllib3

   # set the path to set ansible logs
   log_path = ./ansible.log

   # set specific privelege escalation if necessary for the scenario
   [privilege_escalation]
   become=True
   become_method=sudo
   become_user=test

To see all of the settings that can be set see `Ansible Configuation Settings
<https://docs.ansible.com/ansible/latest/reference_appendices/config.html#ansible-configuration-settings>`_.

Ansible Logs
~~~~~~~~~~~~

To get ansible logs, you must set the **log_path** in the ansible.cfg, and it
is recommended to set the **log_filter** in the ansible.cfg as described to
filter out non ansible logs.  If you do not set the log path or don't provide
an ansible.cfg, you will not get any ansible logs.  The ansible log will be
added to the **ansible_orchestrate** folder under the logs folder of teflo's output,
please see `Teflo Output <../output.html>`_ for more details.


.. _ans_keys:

Using ansible_script
~~~~~~~~~~~~~~~~~~~~

Orchestrate task uses ansible playbook module to run the user provided scripts.
The script name can be given within the **name** key of the ansible_script list of dictionary.

The script parameters can be provided along with name of the script by separating
it using space.

.. note::
        The script parameters can also be passed using ansible_options key. But this will be deprecated in
        the future releases
        :ref:`Example 15<Example_15>`

Extra_args for the script can be provided as a part of the ansible_script list
of dictionary or under ansible_options. Please see
:ref:`Extra_args<extra_args>`
:ref:`Example 13<Example_13>`
:ref:`Example 14<Example_14>`

Using ansible_shell
~~~~~~~~~~~~~~~~~~~

Orchestrate task uses ansible shell module to run the user provided shell commands.
ansible_shell takes in a list of dictionaries for the different commands to be run.
The shell command can be provided under the *command* key the ansible_shell list of
dictionary. Extra_args for the shell command can be provided as a part of the ansible_shell
list of dictionary or under ansible_options. Please see :ref:`Extra_args<extra_args>`
:ref:`Example 12<eg_12>`


When building your shell commands it is important to take into consideration
that there are multiple layers the command is being passed through before
being executed. The two main things to pay attention to are
YAML syntax/escaping and Shell escaping.

When writing the command in the scenario descriptor file it needs to be written in
a way that both Teflo and Ansible can parse the YAML properly. From a Teflo perspective
it is when the the scenario descriptor is first loaded. From an Ansible perspective
its when we pass it the playbook we create, cbn_execute_shell.yml, through to the
ansible-playbook CLI.

Then there could be further escapes required to preserve the test command so it can be
interpreted by the shell properly. From a Teflo perspective that is when we
pass the test command to the ansible-playbook CLI on the local shell using the
-e "xcmd='<test_command>'" parameter. From the Ansible perspective its when
the shell module executes the actual test command using the shell on the designated system.

Let's go into a couple examples

.. code-block:: yaml

   ansible_shell:
     - command: glusto --pytest='-v tests/test_sample.py --junitxml=/tmp/SampleTest.xml'
                --log /tmp/glusto_sample.log

On the surface the above command will pass YAML syntax parsing but will fail when actually
executing the command on the shell. That is because the command is not preserved properly on
the shell when it comes to the *--pytest* optioned being passed in. In order to get
this to work you could escape this in one of two ways so that the *--pytest* optioned is
preserved.

.. code-block:: yaml

   ansible_shell:
     - command: glusto --pytest=\\\"-v tests/test_sample.py --junitxml=/tmp/SampleTest.xml\\\"
                --log /tmp/glusto_sample.log


   ansible_shell:
     - command: glusto \\\"--pytest=-v tests/test_sample.py --junitxml=/tmp/SampleTest.xml\\\"
                --log /tmp/glusto_sample.log


Here is a more complex example

.. code-block:: yaml

    ansible_shell:
        - command: if [ `echo \$PRE_GA | tr [:upper:] [:lower:]` == 'true' ];
                   then sed -i 's/pre_ga:.*/pre_ga: true/' ansible/test_playbook.yml; fi

By default this will fail to be parsed by YAML as improper syntax. The rule of thumb is
if your unquoted YAML string has any of the following special characters :-{}[]!#|>&%@
the best practice is to quote the string. You have the option to either use single quote
or double quotes. There are pros and cons to which quoting method to use. There are online
resources that go further into this topic.

Once the string is quoted, you now need to make sure the command is preserved properly
on the shell. Below are a couple of examples of how you could achieve this using either
a single quoted or double quoted YAML string

.. code-block:: yaml

    ansible_shell:
        - command: 'if [ \`echo \$PRE_GA | tr [:upper:] [:lower:]\` == ''true'' ];
                    then sed -i \"s/pre_ga:.*/pre_ga: true/\" ansible/test_playbook.yml; fi'


    ansible_shell:
        - command: "if [ \\`echo \\$PRE_GA | tr [:upper:] [:lower:]\\` == \\'true\\' ];
                    then sed \\'s/pre_ga:.*/pre_ga: true/\\' ansible/test_playbook.yml; fi"

.. note::
        It is NOT recommended to output verbose logging to standard output for long running tests as there could be
        issues with teflo parsing the output

Using ansible_playbook
~~~~~~~~~~~~~~~~~~~~~~

Using the ansible_playbook parameter you can provide the playbook to be run
The name of the playbook can be provided as the **name** under the ansible_playbook list of dictionary

:ref:`Example2<eg_2>`
:ref:`Example12<eg_12>`

.. note::
        Unlike the shell or script parameter the test playbook executes locally
        from where teflo is running. Which means the test playbook must be in
        the workspace.

.. _extra_args:


.. note::
         Only one action type, either ansible_playbook or ansible_script or ansible_shell is supported
         per orchestrate task

Extra_args for script and shell
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Teflo supports the following parameters used by ansible script and shell modules

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Parameters
    *   - chdir
    *   - creates
    *   - decrypt
    *   - executable
    *   - removes
    *   - warn
    *   - stdin
    *   - stdin_add_newline

Please look here for more info

`Ansible Script Module <https://docs.ansible.com/ansible/latest/modules/script_module.html>`_

`Ansible Shell Module <https://docs.ansible.com/ansible/latest/modules/shell_module.html>`_

vault-password-file
~~~~~~~~~~~~~~~~~~~~~
The vault-password-file can be passed using **vault-password-file** under **ansible_options**

.. code-block:: yaml

    ---
    orchestrate:
      - name: rhsm_register.yml
        description: "register systems under test against rhsm"
        orchestrator: ansible
        hosts: all
        ansible_options:
          vault-password-file:
            - "./vaultpass"

Extra_vars
~~~~~~~~~~

Extra variables needed by ansible playbooks can be passed using **extra_vars** key under
the **ansible_options** section

.. code-block:: yaml

    ---
    orchestrate:
      - name: rhsm_register.yml
        description: "register systems under test against rhsm"
        orchestrator: ansible
        hosts: all
        ansible_options:
          extra_vars:
            username: kingbob
            password: minions
            server_hostname: server01.example.com
            auto_attach: true

Use the **file** key to pass a variable file to the playbook. This file needs to present in teflo's workspace
**file** key can be a single file give as string or a list of variable files present in teflo's workspace


.. code-block:: yaml

    ---
    orchestrate:
      - name: rhsm_register.yml
        description: "register systems under test against rhsm"
        orchestrator: ansible
        hosts: all
        ansible_options:
          extra_vars:
            file: variable_file.yml


.. code-block:: yaml

    ---
    orchestrate:
      - name: rhsm_register.yml
        description: "register systems under test against rhsm"
        orchestrator: ansible
        hosts: all
        ansible_options:
          extra_vars:
            file:
            - variable_file.yml
            - variable_1_file.yml


Ansible Galaxy Options
~~~~~~~~~~~~~~~~~~~~~~

These are additional options provided to the ansible orchestrator regarding the ansible roles and collections

Retry
+++++

To make sure ansible roles and collections are downloaded correctly, 'retry' ansible galaxy option is used

.. code-block:: yaml

    ---
    - name: ansible/setup-vnc.yml
      description: "setup a vnc server on test clients"
      orchestrator: ansible
      hosts: vnc
      ansible_galaxy_options:
        role_file: roles.yml
        retry: True

Examples
--------

Lets dive into a couple different examples.

Example 1
~~~~~~~~~

You have a playbook which needs to run against x number of hosts and does not
require any additional extra variables.

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 40-49

.. _eg_2:

Example 2
~~~~~~~~~

You have a playbook which needs to run against x number of hosts and requires
additional extra variables.

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 52-67

Example 3
~~~~~~~~~

You have a playbook which needs to run against x number of hosts and requires
only tasks with a tag set to prod.

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 70-81

Example 4
~~~~~~~~~

You have a playbook which needs to run against x number of hosts and requires
only tasks with a tag set to prod and requires connection settings that conflicts with your ansible.cfg.

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 84-101


Example 5
~~~~~~~~~

You have a playbook which needs to run against x number of hosts and requires
an ansible role to be downloaded.

.. note::
         Although the option is called *role_file:* but it relates both, roles and collections.

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 104-115

Content of requirements.yml as a dictionary, suitable for both roles and collections:

.. code-block:: yaml

    ---
    roles:
    - src: oasis-roles.rhsm

    collections:
    - name: geerlingguy.php_roles
    - geerlingguy.k8s

As you can see we defined the role_file key. This defines the ansible
requirements filename. Teflo will consume that file and download all the
roles and collections defined within.

.. note::

         We can define roles in the req file as a list or as dictionary, Teflo support both ways.
         but if we chose to set roles as list then we can't set collections in the same file.

Content of requirements.yml file as a list, only suitable for roles:

.. code-block:: yaml

    ---
    - src: oasis-roles.rhsm
    - src: https://gitlab.cee.redhat.com/PIT/roles/junit-install.git
      scm: git

An alternative to using the requirements file is you can directly define them using
the roles or collections key.

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 118-134

It is possible to define both role_file and direct definitions. Teflo will install the
roles and collections first from the role_file and then the roles and collections defined using the keys. It is up to the
scenario to ensure no problems may occur if both are defined.

.. note::

    If your scenario directory has roles and collections already defined, you do not need to
    define them. This is only if you want teflo to download roles or collections from sites
    such as ansible galaxy, external web servers, etc.

Example 6
~~~~~~~~~

You have a playbook which needs to run against x number of hosts, requires
ansible roles to be downloaded and requires additional extra variables.

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 137-154

.. attention::

    Every scenario processed by teflo should define an ansible configuration
    file. This provides the scenario with the flexibility to easily control
    portions of ansible.

    If you are using the ability to download roles or collections by teflo, you need to set
    the *roles_path* or the *collections_paths* within your ansible.cfg. If this is not set, problems will
    occur and teflo will fail. Due to being unable to locate the roles and collections within
    the playbook its executing.

    Here is an example ansible.cfg setting the roles_path and collections_paths to a relative path
    within the scenario directory.

    .. code-block:: bash

        [defaults]
        host_key_checking = False
        retry_files_enabled = False
        roles_path = ./roles
        collections_paths = ./collections

Example 7
~~~~~~~~~

You have a playbook which needs to run against x number of hosts. Prior to
deleting the configured hosts. You want to run a playbook to do some post
tasks.

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 157-181


Example 8
~~~~~~~~~

The following is an example of running a script.  The following is an
example of a script running on the localhost. For localhost usage refer
to the`localhost <../localhost.html>`_ page.

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 184-191

Example 9
~~~~~~~~~

The following builds on the previous example, by showing how a user
can add options to the script they are executing (In the example below,
the script is run with options as **create_dir.sh -c -e 12**).

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 194-203

Example 10
~~~~~~~~~~

Again building on the previous example, you can set more options to the
script execution.  The script is executed using the script ansible
module, so you can set options the script module has.  The example below
uses the **chdir** option.  You can also set other ansible options, and the
example below sets the **remote_user** option.

To see all script options see ansible's documentation `here
<https://docs.ansible.com/ansible/latest/modules/script_module.html>`_.

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 206-216

Example 11
~~~~~~~~~~

You have a playbook which needs to run against x number of hosts and requires
skipping tasks with a tag set to ssh_auth and requires extra variables.

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 219-234

.. _eg_12:

Example 12
~~~~~~~~~~

Example to run playbooks, scripts and shell command as a part of orchestrate task

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 237-261

.. _Example_13:

Example 13
~~~~~~~~~~

Example to use ansible_script with extra arags with in the ansible_script
list of dictionary and its paramter in the name field

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 265-272


.. _Example_14:

Example 14
~~~~~~~~~~

Example to use ansible_script with extra arags as a part of ansible_options

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 275-283

.. _Example_15:

Example 15
~~~~~~~~~~

Example to use ansible_script and using ansible_options: extra_args to
provide the script parameters

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 286-294

Resources
~~~~~~~~~

For system configuration & product installs use roles from: `Oasis Roles`_

.. _Oasis Roles: https://github.com/oasis-roles
