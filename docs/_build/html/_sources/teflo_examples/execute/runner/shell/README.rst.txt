Shell
=====

This example demonstrates how you can execute tests against test machines
using teflo.

**ATTENTION**

This example below has teflo installed in a virtual environment named teflo.
Please replace this virtual environment with the virtual environment you
created for teflo if it differs.

Pre-Run
-------

First lets review the content of the `scenario descriptor file <scenario.yml>`_.
This file contains a provision section which contains one host resource
defined. For the case of keeping this example simple, the host resource is
the localhost where teflo will be run. This way we can avoid any provisioning
of machines. The execute section contains one execute task to be run. It
defines a shell key which has a list of test commands to be run. For this
simple example it will just print the environment variables to a file. Once
the test is finished running, teflo will archive the artifacts that were
defined.

Run
---

Option 1
++++++++

To execute tests against the machines under test, just run the following
teflo command.

.. code-block:: none

    (teflo) $ teflo run -t provision -t execute -s scenario.yml

You will see teflo skip over provisioning the machine due to its a static
machine. Then execute task will start to run the defined test.

Option 2
++++++++

Within this directory is a script that wraps all the teflo commands to provide
an easy way showing how to run teflo (for a demo purpose).

You can run the script to execute as follows:

.. code-block:: none

    (teflo) $ ./run.sh