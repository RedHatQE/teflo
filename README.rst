Welcome to Teflo!
==================

What is Teflo?
---------------

**TEFLO** stands for (**T** est **E** xecution **F** ramework **L** ibraries and **O** bjects)

Teflo is an orchestration software that controls the flow of a set of testing scenarios.
It is a standalone tool written in Python that includes all aspects of the workflow.
It allows users to provision machines, deploy software, execute tests against them and
manage generated artifacts and report results.

Teflo Provides *structure*, *readability*, *extensibility* and *flexibility* by :

- providing a YAML file to express a test workflow as a series of steps.
- enabling integration of external tooling to execute the test workflow as defined by the steps.

Teflo can be used for an E2E (end to end) multi-product scenario. Teflo handles coordinating the
E2E task workflow to drive the scenario execution.

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

Teflo has following stages

**Provision** - Create resources to test against (physical resources, VMs etc)

**Orchestrate** - Configure the provisioned resources (e.g. install packages on them, run scripts, ansible playbooks etc)

**Execute** - Execute tests on the configured resources

**Report** - Send or collect logs from the tests run

**Notification** - Send email/gchat/slack notification during each stage of teflo run or at the end based on the set triggers

**Cleanup** - Cleanup all the deployed resources.

These stages can be run individually or together.


Teflo follows a plugable architechture, where users can add different pluggins to support external tools
Below is a diagram that gives you a quick overview of the Teflo workflow

.. image:: /docs/_static/teflo_workflow.png

* To learn more about how to set up and use Teflo please check out https://teflo.readthedocs.io/en/latest/
* To know how to create a custom plugin check out https://teflo.readthedocs.io/en/latest/developers/development.html#how-to-write-an-plugin-for-teflo
* To know about our release cadence and contribution policy check out https://teflo.readthedocs.io/en/latest/developers/development.html#release-cadence