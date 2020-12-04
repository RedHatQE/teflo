Static
======

This example demonstrates how you can define and use static machines within
teflo.

Prior to running this example, please make sure you have followed the steps
for `installing teflo <http://teflo-dev-01.usersys.redhat.com/cbn/
users/install.html>`_.

**ATTENTION**

This example below has teflo installed in a virtual environment named teflo.
Please replace this virtual environment with the virtual environment you
created for teflo if it differs.

Pre-Run
-------

First lets review the content of the `scenario descriptor file <scenario.yml>`_.
This file contains a provision section with one host resource defined. Static
machines only require a couple keys (*name*, *role*, *ip_address*). It is highly
recommended to define *ansible_params* key. This tells teflo about how
ansible should connect to the machine.

Run
---

Option 1
++++++++

To provision the machine, just execute the following teflo command below.

.. code-block:: none

    (teflo) $ teflo run -t provision -s scenario.yml

You will see that teflo skips provisioning due to the machine is static.

Since the machine is static, cleanup task is not necessary. If you wish to run
cleanup, teflo will not delete the machine. You can call cleanup as follows:

.. code-block:: none

    (teflo) $ teflo run -t cleanup -s .teflo/.results/results.yml -w .

As you can see we gave a different scenario file. At the end of each teflo
run a new results file gets generated. This file is an exact copy of the
initial scenario file just with additional information appeneded.

Option 2
++++++++

Within this directory is a script that wraps all the teflo commands to provide
an easy way showing how to run teflo (for a demo purpose).

You can run the script to provision/cleanup as follows:

.. code-block:: none

    # you will need to provide the data to the prompts
    (teflo) $ ./run.sh
