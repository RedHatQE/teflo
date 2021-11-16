Execute
=======

Overview
--------

Teflo's execute section declares the test execution of the scenario.  In
most cases there would be three major steps performed during execution:

- cloning the tests
- executing the tests
- gathering the test results, logs, and other important information for the
  test execution.

The execution is further broken down into 3 different types:

- execution using a command
- execution using a user defined script
- execution using a user defined playbook

The following is the basic structure that defines an execution task, using a
command for execution:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 1-18

The following is the basic structure that defines an execution task, using a
user defined script for execution:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 20-37

The following is the basic structure that defines an exectuion task, using a
user defined playbook for execution:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 40-57


The above code snippet is the minimal structure that is required to create a
execute task within teflo. This task is translated into a teflo execute
object which is part of the teflo compound. You can learn more about this at
the `architecture <../../developers/architecture.html>`_ page.

Please see the table below to understand the key/values defined.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required
        - Default

    *   - name
        - Name assigned to the execution task
        - String
        - Yes
        - n/a

    *   - description
        - Description of the execution task
        - String
        - No
        - n/a

    *   - executor
        - Name of the executor to be used
        - String
        - No
        - runner

    *   - hosts
        - the machine(s) that execute will run on
        - String
        - Yes
        - n/a

    *   - ignore_rc
        - ignore the return code of the execution
        - Boolean
        - No
        - False

    *   - valid_rc
        - valid return codes of the execution (success)
        - list of integers
        - No
        - n/a

    *   - git
        - git information for the tests in execution
        - list of dictionaries
        - No
        - n/a

    *   - shell
        - list of shell commands to execute the tests.
        - list of dictionaries
        - (Not required; however, one of the following must be defined:
          shell, script or playbook)
        - False

    *   - script
        - list of scripts to execute to run the tests.
        - list of dictionaries
        - (Not required; however, one of the following must be defined:
          shell, script or playbook)
        - False

    *   - playbook
        - list of playbooks that execute the tests.
        - list of dictionaries
        - (Not required; however, one of the following must be defined:
          shell, script or playbook)
        - False

    *   - artifacts
        - list of all the data to collect after execution.
          If a directory is listed, all data in that folder
          will be gathered.  A single file can also be listed.
        - list
        - No
        - n/a

    *   - artifact_locations
        - A list of data collected during artifacts or a list of additional log files to be
          considered by Teflo after execution.
          It is a list of relative path for the directories or files to be considered
          under the teflo's **.results** folder.
        - dict
        - No
        - n/a

    *   - ansible_options
        - get ansible options for the tests in execution
        - dictionary
        - No
        - n/a

    *   - environment_vars
        - Additional environment variables to be passed during the test execution
        - dict
        - No
        - environment variables set prior to starting the teflo run are available



Hosts
-----

Teflo provides many ways to define your host.  This has already been
described in the orchestration section, please view information about
defining the hosts `here <orchestrate.html#hosts>`_. For more localhost
usage refer to the `localhost <../localhost.html>`_ page.

Ansible
-------

The default executor '*runner*' uses ansible to perform the requested actions.
This means users can set ansible options to be used by the runner executor.
In this case, the options should mostly be used for defining the user that is
performing the execution. Please see the following example for more details:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 59-64

.. note::
   Teflo uses the ansible copy module to process the results of the requested action. The copy module requires selinux
   access. Refer to the `install guide <../install.html#install>`_.


Ansible Logs
~~~~~~~~~~~~

To get ansible logs, you must set the **log_path** in the ansible.cfg, and it
is recommended to set the **log_filter** in the ansible.cfg as described to
filter out non ansible logs.  If you do not set the log path or don't provide
an ansible.cfg, you will not get any ansible logs.  The ansible log will be
added to the **ansible_executor** folder under the logs folder of teflo's output,
please see `Teflo Output <../output.html>`_ for more details.


Return Code for Test Execution
------------------------------

Teflo will fail out if there is a non-zero return code.  However, for many
unit testing frameworks there is a non-zero return code if there are test failures.
For this case, teflo has two options to handle these situations:

 #.  ignore the return code for the test execution
 #.  give list of valid return codes that will not flag failure

Option 1 to handle non-zero return codes is called **ignore_rc**, this option 
can be used at the top level key of execute or can also be used for each
specific call.  The following shows an example, where it is defined in both
areas.  The top level is set to False, which is the default, then it is used
only for the 2nd pytest execution call, where there are failures:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 66-85

Options 2 to handle non-zero return codes is called **valid_rc**, this option
can also be used at the top level key of execute or can be used for each
specific call. If **ignore_rc** is set it takes precedence. The following shows
an example, where it is defined in both areas. The top level is set to one value
and the call overides it:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 187-207

.. _using_shell:

Using Shell Parameter for Test Execution
----------------------------------------

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

   shell:
     - command: glusto --pytest='-v tests/test_sample.py --junitxml=/tmp/SampleTest.xml'
                --log /tmp/glusto_sample.log

On the surface the above command will pass YAML syntax parsing but will fail when actually
executing the command on the shell. That is because the command is not preserved properly on
the shell when it comes to the *--pytest* optioned being passed in. In order to get
this to work you could escape this in one of two ways so that the *--pytest* optioned is
preserved.

.. code-block:: yaml

   shell:
     - command: glusto --pytest=\\\"-v tests/test_sample.py --junitxml=/tmp/SampleTest.xml\\\"
                --log /tmp/glusto_sample.log


   shell:
     - command: glusto \\\"--pytest=-v tests/test_sample.py --junitxml=/tmp/SampleTest.xml\\\"
                --log /tmp/glusto_sample.log


Here is a more complex example

.. code-block:: yaml

    shell:
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

    shell:
        - command: 'if [ \`echo \$PRE_GA | tr [:upper:] [:lower:]\` == ''true'' ];
                   then sed -i \"s/pre_ga:.*/pre_ga: true/\" ansible/test_playbook.yml; fi'


    shell:
        - command: "if [ \\`echo \\$PRE_GA | tr [:upper:] [:lower:]\\` == \\'true\\' ];
                   then sed \\'s/pre_ga:.*/pre_ga: true/\\' ansible/test_playbook.yml; fi"

.. note::
     It is NOT recommended to output verbose logging to standard output for long running tests as there could be
     issues with teflo parsing the output


Extra_args for script and shell
-------------------------------

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

Using Playbook Parameter for Test Execution
-------------------------------------------

Using the playbook parameter to execute tests works like how playbooks
are executed in the Orchestration phase. The only thing not supported is the
ability to download roles using the *ansible_galaxy_option*. The following
is an example of how run test playbooks.

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 209-223


.. note::
    Unlike the shell or script parameter the test playbook executes locally
    from where teflo is running. Which means the test playbook must be in
    the workspace.

.. note::
    extra_vars are set same as the orchestrate stage. Please refer :ref:`Extra Vars <extra_vars>`


Data Substitution Required for Test Execution
---------------------------------------------

In some cases, you may need to substitute data for the execution.  Teflo
allows you to substitute the information from the dynamically created hosts.

Let's first take a look at some example data of key/values a user may use
for provisioning a host:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 106-119

After the machines are provsioned, we have more information in the host object,
and this can be seen by the results.yml file after a provision is successful.
Some basic information that is added is the machine's actual name and ip
address.  The following is what the data looks like after provisioning:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 122-144

Looking at the data presented above, there is a lot of information about the
host, that may be useful for test execution.  You can also see the key
**metadata**, this key can be used to set any data the user wishes to when
running teflo.

The following is an example, where the user plans to use the ip address in an
execution command.  From the data above, you can see the user is accessing the
data from **test_client_a** -> **ip_address**.

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 87-103


Artifacts of the Test Execution
-------------------------------

After an execution is complete, it is common to get results of the test
execution, logs related to the execution, and other logs or files generated
by a specific product during the execution.  These will all be gathered by
teflo and placed in an artifacts directory of your data directory.

For the data gathering, if you specify a folder, teflo will gather all the
data under that folder, if you specify a file, it will gather that single
file.

The following is a simple example of the data gathering (defining artifacts):

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 146-153

Going through the basics of artifacts, the user can archive individual files,
as shown by the following example:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 156-160

The user can also collect artifact files using wildcards as shown in the following
example:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 162-165

The user can also archive a directory using either of the following two
examples:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 167-170

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 172-175

Finally, the user can archive a directory using a wildcard using either
of the following two examples:

.. literalinclude:: ../../../examples/docs-usage/execute.yml
   :lines: 177-180

.. literalinclude:: ../../../examples/docs-usage/execute.yml
   :lines: 182-185

Teflo by default will **NOT** exit if the collection of artifact task fails. In order to exit the run on an error during
collection of artifacts user can set the **exit_on_error** field for executor in the teflo.cfg as below:

.. code-block:: bash

   [executor:runner]
   exit_on_error=True

.. _finding_locations:

Artifact Locations
~~~~~~~~~~~~~~~~~~
The **artifact_locations** key is used to keep track of the artifacts that were collected using artifacts key during
execute stage. It's a list which consists of the relative path of the artifacts to be considered which are placed under
the teflo's **.results** folder.
The artifact_locations key is available to users to define locations for artifacts that
may not have been collected as part of artifacts but they want to be tracked for later use in Report.
The only caveat is the artifacts defined under artifact_locations must be placed in the
teflo_data_folder/.results directory. Refer to the :ref:`Finding the right artifacts <finding_artifacts>`

Teflo also auto creates the artifacts folder under the .results folder. Users can place their artifacts in this folder
as well

In the below example, the payload_dir is the name of the directory  which is present under the .results folder

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 226-245

In the below example, the payload_dir  and dir1 are placed in the artifacts folder created by teflo.

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 248-267

Testrun Results for Artifacts collected during the Execute block:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Teflo generates a testrun results summary for all the **xml files** it collects as a part of artifacts OR
artifact_locations in an execute block. This summary can be seen in the results.xml as weel as is printed out
on the console. The summary shows aggregate summary of all xmls collected and individual summary
of each xml file. The summary contains **number of tests passed, failed, errored, skipped and the total tests.**

.. code-block:: yaml

    - name: junit
      description: execute junit test on client
      executor: runner
      hosts:
      - laptop
      shell:
      - chdir: /home/client1/junit/tests
        command: javac Sample.java; javac UnitTestRunner.java; javac CustomExecutionListener.java; javac SampleTest.java; java UnitTestRunner SampleTest
      git:
      - repo: https://gitlab.cee.redhat.com/ccit/teflo/junit-example.git
        version: master
        dest: /home/client1/junit
      artifacts:
      - /home/client1/junit/tests/*.log
      - /home/client1/junit/tests/*.xml
      artifact_locations:
        - dir1/junit_example.xml
        - artifacts/client1/junit_example.xml
        - artifacts/client1/ocp_edge_deploment_integration_results.xml
        - artifacts/client1/SampleTest.xml
      testrun_results:
        aggregate_testrun_results:
          total_tests: 22
          failed_tests: 9
          error_tests: 0
          skipped_tests: 0
          passed_tests: 13
        individual_results:
        - junit_example.xml:
            total_tests: 6
            failed_tests: 2
            error_tests: 0
            skipped_tests: 0
            passed_tests: 4
        - junit_example.xml:
            total_tests: 6
            failed_tests: 2
            error_tests: 0
            skipped_tests: 0
            passed_tests: 4
        - ocp_edge_deploment_integration_results.xml:
            total_tests: 8
            failed_tests: 5
            error_tests: 0
            skipped_tests: 0
            passed_tests: 3
        - SampleTest.xml:
            total_tests: 2
            failed_tests: 0
            error_tests: 0
            skipped_tests: 0
            passed_tests: 2

This is the default behavior of Teflo. If a user does not want this summary generated, user can change the
following setting to False in the teflo.cfg

.. code-block:: bash

   [executor:runner]
   testrun_results=False

.. note::

   Teflo expects the xmls collected to have the **<testsuites>** tag  OR **<testsuite>** as its root tag,
   else it skips those xml files for testrun summary generation

Using environment variables:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the below example the environment variables data_dir and uname are made available during
the playbook execution

.. literalinclude:: ../../../examples/docs-usage/execute.yml
    :lines: 271-288

Common Examples
---------------

Please review the following for detailed end to end examples for common
execution use cases:

* `Pytest Example <../examples.html#pytest>`_
* `JUnit Example <../examples.html#junit>`_
* `Restraint Example <../examples.html#restraint>`_
