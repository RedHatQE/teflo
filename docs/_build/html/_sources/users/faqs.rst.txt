FAQS
====

The following are some answers to frequently asked questions about Teflo.

How Do I...
-----------

Provision
+++++++++

... call teflo using static machines?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You need to define the machine as a static machine in the teflo definition
file.  See `Defining Static Machines
<definitions/provision.html#defining-static-machines>`_ for details.

... run scripts on my local system?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You need to define your local system as a static resource.
See `The localhost example <localhost.html>`_ for details.

... run teflo and not delete my machines at the end of the run?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default when running teflo, you will run all of teflo's tasks; however,
you also have the option to pick and choose which tasks you would like to run,
and you can specify it with -t or --task.  By using this option, you can
specify, all tasks, and just not specify cleanup.  See `Running Teflo
<quickstart.html#run>`_ for more details.

... know whether to use the Linchpin provisioner?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Its recommended new users onbaording with teflo or new scenarios
being developed to use the Linchpin provisioner. Its being adopted as
the standard provisioning tool and supports a lot more resource providers
that can be enabled in teflo. If you have a pre-existing scenario that is
not using a teflo native provisioner specific parameter is also a good
candidate to migrate over to using the Linchpin provisioner.

If the pre-existing scenarios use teflo native provisioner specific parameters
that Linchpin does not support you will need to continue to use those until Lincphin
supports the parameter. Linchpin is also python 3 compatible except for Beaker. This
support is still not available. We are working with Beaker development to fully
support Beaker client on python 3. Any Beaker scenarios using Python 3 should
continue to use the teflo bkr-client provisioner. All other providers are
supported in Python 3.

... install Linchpin to use the Linchpin provisioner?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Refer to the `Linchpin Requirements section <install.html#linchpin-requirements>`_
to install Linchpin and it's dependencies.

... know if my current scenarios will work with the new Linchpin provisioner?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can add the provisioner key to use the linchpin-wrapper and run the validate
command

.. code-block:: bash

    teflo validate -s <scenario.yml>

This will diplay warnings on which resource parameters may be supported
and error out on parameters that are not supported by the provisioner. Resolve
any of the warnings and failures. Once validate passes then the scenario should
be Linchpin compatible.

... parallel provisioning fails with linchpin provisioner ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Linchpin version 1.9.1.1 introduced issue where when provison concurrency is set to True in
teflo.cfg file the provisioning hangs. This can be addressed by setting task concurrency to provision= False
in the teflo.cfg. This issue is now fixed with Linchpin version 1.9.2.


... which Linchpin version to use ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Recommended version of linchpin to use is 1.9.2. Lower version will give errors like
ModuleNotFoundError: No module named 'ansible.module_utils.common.json' or ansible requirements mismatch or
concurrency issues

... what versions of python are supported by Linchpin ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Teflo uses Linchpin to provision openstack, aws, libvirt  with python 2 and 3. For beaker Linchpin
supports python 3 only with beaker 27 client on Fedora 30 and RH8 systems.

Orchestrate
+++++++++++

... pass data from playbook to playbook using teflo?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See the `Data Pass-through Section
<data_pass_through.html#data-pass-through>`_


Execute
+++++++

... have my test shell command parsed correctly?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When crafting your complex commands you need to consider a couple items:

 - proper YAML syntax
 - proper Shell escaping

You can refer to any online YAML validator to make sure the test command
is valid YAML syntax. Then you need to remember to make sure you have proper
shell escaping syntax to make sure the test command is interpreted properly.
Refer to the :ref:`Using Shell Parameter for Test Execution <using_shell>` section
in the Execute page.


Report
++++++

... import an artifact that wasn't collected as part of Execute?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can place the file(s) or folder(s) in the teflo's *<data_folder>/.results*
and let teflo search for it or once in the results directory
define in it in the *artifact_locations* key telling teflo where to look.
Refer to the :ref:`Finding the right artifacts <finding_artifacts>` section
on the Report page.

... stop finding duplicate artifacts during the import?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The driving factor is the name field of the report block. You can narrow and
restrict the search based on the shell pattern specified.

For example, if you specify an artifact like *SampleTest.xml* but the artifact
has been collected numerous times before its possible a list of the same file in
different locations within the teflo *<data_folder>* are going to be found.
You can restrict the search to a particular instance by doing something like
*test_driver/SampleTest.xml* with test_driver being a directory. Telling teflo
to look in that particular directory for the artifact.

For more information on the different patterns that can be used in the name field
refer to some of the :ref:`examples <report_examples>` under Polarion and Report Portal
in the Report page.report_examples


Miscellaneous
+++++++++++++

... see the current issues logged against teflo?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See the list of current `Issues
<https://projects.engineering.redhat.com/issues/?filter=40207>`_
logged against teflo.

... see the supported teflo_plugins?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See the matrix which calls out all the supported versions for the teflo_plugins for importers and provisioners
and related libraries :ref:`here <cbn_plugin_matrix>`
