Welcome to Teflo!
==================

.. important::
             The Teflo confluence section is only present to provide
             information about plugins and features that are internal to
             redhat. For all other information please visit https://teflo.readthedocs.io/en/latest/

What is Teflo?
---------------

**TEFLO** stands for (**T** est **E** xecution **F** ramework **L** ibraries and **O** bjects)

Teflo is an orchestration software that controls the flow of a set of testing scenarios.
It is a standalone tool that includes all aspects of the workflow.
It allows users to provision machines, deploy software, execute tests against them and
manage generated artifacts and report results.


Teflo is developed in Python.
**It was originally known as Carbon.**

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

Teflo Tickets/Issues
--------------------

At present users can file Teflo issues on github `issues <https://github.com/RedHatQE/teflo/issues>`_
OR  filing a ticket on the project CCIT CARBON on JIRA
See the list of current open `Issues on JIRA <https://projects.engineering.redhat.com/issues/?filter=40207>`_

We are working on changing this so that users can file tickets using only the github issues.
We will updtae this space once that is implemented

.. include:: contents.rst.inc
