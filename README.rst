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
