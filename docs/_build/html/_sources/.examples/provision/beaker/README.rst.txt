Beaker
======

This example demonstrates how you can define and use beaker machines within
teflo.

Prior to running this example, please make sure you have followed the steps
for `installing teflo <http://teflo-dev-01.usersys.redhat.com/cbn/
users/install.html>`_.

Prior to running this example, please make sure you have followed the steps
for `configuring teflo <http://teflo-dev-01.usersys.redhat.com/cbn/
users/configuration.html>`_.

**ATTENTION**

This example below has teflo installed in a virtual environment named teflo.
Please replace this virtual environment with the virtual environment you
created for teflo if it differs.

Pre-Run
-------

First lets review the content of the `scenario descriptor file <scenario.yml>`_.
This file contains a provision section with one host resource defined. You will
see the machine requires a couple keys (*name*, *role*, *provider*). It is
highly recommended to define *ansible_params* key. This tells teflo about how
ansible should connect to the machine.

Run
---

Option 1
++++++++

To provision the machine, please make sure you have set your beaker
credentials properly within the `teflo.cfg <teflo.cfg>`_.

You also need to set the following environment variables. This data will be
templated into the scenario descriptor file.

.. code-block:: bash

    (teflo) $ export jobgroup=<BEAKER_JOB_GROUP>
    (teflo) $ export username=<BEAKER_USERNAME_LOGIN_TO_MACHINES>
    (teflo) $ export password=<BEAKER_PASSWORD_LOGIN_TO_MACHINES>
    (teflo> $ export host_fqdn=<FQDN_OF_SPECIFIC_BEAKER_HOST>

Once you have set those environment variables you can execute the following
command to run teflo.

.. code-block:: none

    (teflo) $ teflo run -t provision -s scenario.yml -w .

You will see teflo provision the machine by submitting a beaker reservation job.
On completion, teflo will create an updated scenario descriptor file
(results.yml). This file will be an exact copy but contains additional
information from provisioning such as ip address, beaker job, etc.

To cleanup the machine, just execute the following teflo command below.

.. code-block:: none

    (teflo) $ teflo run -t cleanup -s .teflo/.results/results.yml

We pointed teflo to the updated descriptor file. This provides teflo with
the updated information from the provision task.

Option 2
++++++++

Within this directory is a script that wraps all the teflo commands to provide
an easy way showing how to run teflo (for a demo purpose).

You can run the script to provision/cleanup as follows:

.. code-block:: none

    # you will need to provide the data to the prompts
    (teflo) $ ./run.sh
