Scenario Descriptor
===================

This page is intended to explain the input to teflo. The goal and focus behind
teflos input is to be simple and transparent. It uses common language to
describe the entire scenario (E2E). The input is written in YAML. The term
used to reference teflo's input is a scenario descriptor file. You will hear
this throughout teflo's documentation.

Every scenario descriptor file is broken down into different sections. Below is
a table of the keys that correlate to the different sections.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - name
        - The name of the scenario descriptor file.
        - String
        - True

    *   - description
        - A description of the intent of the scenario.
        - String
        - False

    *   - resource_check
        - A list of external resources the scenario depends on
          that Teflo can check in Semaphore before running
          the scenario.
        - List
        - False

    *   - include
        - A list of scenario descriptor files that should be included
          when running the scenario.
        - List
        - False

    *   - provision
        - A list that contains blocks of Asset definitions that should be dynamically
          provisioned or statically defined to be used by the rest of the scenario.
        - List
        - False

    *   - orchestrate
        - A list that contains blocks of Action definitions that define scripts or
          playbooks that should be run to configure the assets defined in the provision.
        - List
        - False

    *   - execute
        - A list that contains blocks of Execute definitions that define scripts,
          commands, or playbooks that execute tests on the appropriately configured assets.
        - List
        - False

    *   - report
        - A list that contains blocks of Report definitions that should be run
          to import test artifacts collected during test execution to a desired
          reporting system.
        - List
        - False


Each section relates to a particular component within teflo. You can learn about this at
the `architecture <../developers/architecture.html>`_ page. Below are sub pages which go
into further detail explaining the different sections.

.. toctree::
    :maxdepth: 1

    definitions/resource_check
    definitions/credentials
    definitions/include
    definitions/provision
    definitions/orchestrate
    definitions/execute
    definitions/report
    definitions/notifications
    definitions/timeout

When we put all of these sections together, we have a complete scenario to
provide to teflo. You can see an example of a complete scenario descriptor
below:

.. literalinclude:: ../../examples/docs-usage/template.yml
