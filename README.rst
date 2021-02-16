Welcome to Teflo!
==================

What is Teflo?
---------------

**TEFLO** stands for (**T** est **E** xecution **F** ramework **L** ibraries and **O** bjects)

Teflo is an orchestration software that controls the flow of a set of testing scenarios.
It is a standalone tool that includes all aspects of the workflow.
It allows users to provision machines, deploy software, execute tests against them and
manage generated artifacts and report results.

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

Teflo is a test execution framework. It is a standalone tool written in Python.
Teflo has following stages

Provision - Create resources they want to test on (physical resources, VMs etc)

Orchestrate - Configure these resources , like install packages on them, run scripts, ansible playbooks etc

Execute- Execute actual tests on the configured resources

Report- Send or collect logs from the run tests

Notification- Send email/gchat/slack notification during each stage of teflo run or at the end based on the triggers set

Cleanup- Cleanup all the deployed resources.

These stages can be run individually or together.

To learn more about how to set up and use Teflo please check out https://teflo.readthedocs.io/en/latest/