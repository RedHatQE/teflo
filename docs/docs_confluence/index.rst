Welcome to Teflo!
==================

What is Teflo?
---------------

**TEFLO** stands for (**T** est **E** xecution **F** ramework **L** ibraries and **O** bjects)

Teflo is an orchestration software that controls the flow of a set of testing scenarios.
It is a standalone tool that includes all aspects of the workflow.
It allows users to provision machines, deploy software, execute tests against them and
manage generated artifacts and report results.


Teflo is developed in Python.
It was originally known as Carbon.

Teflo can be used for an E2E (end to end) multi-product scenario. Teflo handles coordinating the
E2E task workflow to drive the scenario execution.

What does an E2E workflow consist of?
-------------------------------------

At a high level teflo executes the following tasks when processing a scenario.

   - Provision system resources
   - Perform system configuration
   - Install products
   - Configure products
   - Install test frameworks
   - Configure test frameworks
   - Execute tests
   - Report results
   - Destroy system resources
   - Send Notifications

.. important::
             The Teflo confluence section is only present to provide
             information about plugins and features that are supported only
             within redhat. For all other information please visit https://teflo.readthedocs.io/en/latest/

Teflo Report Task
~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 1

   ./users/definitions/report.rst

Teflo Compatibility Matrix for Plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The table below lists out the released Teflo version and supported teflo plugin versions. This matrix will track
n and n-2 teflo releases

.. list-table:: Teflo plugin matrix for n and n-2 releases
    :widths: auto
    :header-rows: 1

    *   - Teflo Release
        - 1.0.0

    *   - Rppreproc Plugin
        - 1.0.0

    *   - Polarion Plugin
        - 1.0.0

    *   - Linchpin Plugin
        - 1.0.0

    *   - Openstack Client Plugin
        - 1.0.0

    *   - Webhooks_Notification_Plugin
        - 1.0.0

    *   - Polar
        - 1.2.1

    *   - Rp_preproc
        - 0.1.3

    *   - Ansible
        - >=2.5.0


.. toctree::
   :maxdepth: 1


