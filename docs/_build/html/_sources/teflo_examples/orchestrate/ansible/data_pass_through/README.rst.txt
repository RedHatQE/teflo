Data Pass-through
=================

This example demonstrates how you can perform configuration against test
machines by ansible using teflo with passing data between orchestrate actions.

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
of machines. The orchestrate section contains two actions to be processed.
Each action is an ansible playbook to be run. Each action has a *hosts* key
which defines which host resource to be run against (defined in the provision
section).

Run
---

Option 1
++++++++

To configure the machines under test, just run the following teflo command.

.. code-block:: none

    (teflo) $ teflo run -t provision -t orchestrate -s scenario.yml

You will see teflo skip over provisioning the machine due to its a static
machine. Orchestrate task will start and execute both the actions defined
against the hosts it was declared against. This example will first installing
product a and then go on to install product b. Product b installation requires
data from product a. The product a playbook will set facts that are persistent
and can be accessed by the product b install playbook.

To cleanup the machine, just execute the following teflo command below.

.. code-block:: none

    (teflo) $ teflo run -t cleanup -s .teflo/.results/results.yml -w .

We pointed teflo to the updated descriptor file. This provides teflo with
the updated information from the provision/orchestrate task. Please note
nothing will be deleted due to the host resource was static.

Option 2
++++++++

Within this directory is a script that wraps all the teflo commands to provide
an easy way showing how to run teflo (for a demo purpose).

You can run the script to orchestrate/cleanup as follows:

.. code-block:: none

    # you will need to provide the data to the prompts
    (teflo) $ ./run.sh
