Including Scenarios
===================

Overview
--------
The *Include* section is introduced to provide a way to include common steps of
provisioning, orchestration, execute or reports under one common scenario file.
This reduces the redundancy of putting the same set of steps in every scenario file.

When running a scenario that is using the include option, two results files will be generated.
One for the main scenario which will still be results.yml and one for the included scenario which
will use the scenario's name as a prefix. e.g. common_scenario_results.yml where common_scenario
is the name of the included scenario file. This file will be stored in the same location as the result.yml file.
This allows users to run the common.yml once and its result can be included in other 
scenario files saving time on test executions. Also see `Teflo Output <../output.html>`_

.. note::

        For any given task the included scenario is checked and executed first followed by the main
        scenario. For example, for Orchestrate task, if you have an orchestrate section in both the included
        and main scenario, then the orchestrate tasks in included scenario will be performed first followed
        by the orchestrate tasks in the main scenario.

Example 1
+++++++++
You want to separate out provision of a set of resources because this is a common resource
used in all of your scenarios.

.. literalinclude:: ../../../examples/docs-usage/include.yml
       :lines: 1-21

The provision.yml could look like below

.. literalinclude:: ../../../examples/docs-usage/provision.yml
    :lines: 23-32

Example 2
+++++++++
You want to separate out provision and orchestrate because this is common configuration across all your
scenarios.

.. literalinclude:: ../../../examples/docs-usage/include.yml
    :lines: 22-38

The orchstrate.yml could look like below

.. literalinclude:: ../../../examples/docs-usage/orchestrate.yml
    :lines: 193-205

Example 3
+++++++++
You've already provisioned a resource from a scenario that contained just the provision
and you want to include it's results.yml in another scenario.

.. literalinclude:: ../../../examples/docs-usage/include.yml
    :lines: 40-60

The common-provision_results.yml could look like below

.. literalinclude:: ../../../examples/docs-usage/provision.yml
    :lines: 34-65

Example 4
+++++++++
You want to separate out provision and orchestrate because this is common configuration across all your
scenarios but with this particular scenario you want to also a run a non-common orchestration task.

.. literalinclude:: ../../../examples/docs-usage/include.yml
    :lines: 62-92

