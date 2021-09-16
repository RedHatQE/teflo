Including Scenarios
===================

Overview
--------
The __*Include*__ section is introduced to provide a way to include common steps of
provisioning, orchestration, execute or reports under one or more common scenario files.
This reduces the redundancy of putting the same set of steps in every scenario file. Each
scenario file is a single node of the whole __*Scenario Graph*__

When running a scenario that is using the include option, several results files will be generated.
One for each of the scenarios. the included scenario will use the scenario's name as a prefix. 
e.g. common_scenario_results.yml where common_scenario is the name of the included scenario file. 
All these files will be stored in the same location. This allows users to run common.yml(s) once 
and their result(s) can be included in other scenario files saving time on test executions.
Also see `Teflo Output <../output.html>`_

.. note::

        For any given task the included scenario is checked and executed first followed by the parent
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


Scenario Graph Explanation
==========================


There are two ways of executing teflo scenarios, which are __by_level and by__depth.
User can modify how the scenarios are executed by changing the setting __included_sdf_iterate_method__
in the teflo.cfg , as shown below, by_level is set by default if you don't specify this
parameter

.. code-block:: bash

    [defaults]
    log_level=info
    workspace=.
    included_sdf_iterate_method = by_depth

All blocks(provision, orchestrate, execute, report) in a senario descriptor file will be executed together for each scenario,
in case there are included scenarios

.. note::

        Scenarios should be designed such that the dependent(which you want it to run first) scenario should be
        at the child level. In the below example if sdf13 has the provisioning information and the orchestrate block
        which uses these provisioned assets can be in scenario which is at a higher level, but not the other way
        round


Example
-------
::

                                        sdf

                  /                      |                     \

                sdf1                    sdf7                     sdf

          /       |       \             /   \                 /    |    \

        sdf3    sdf8      sdf5       sdf10 sdf11          sdf4   sdf9  sdf6

                /    \

            sdf12 sdf13              

The above is an complex include usage. Consider sdf1-sdf13 are different included scenarios
and sdf is the main scenario


by_level
+++++++++
The execution order will be
12,13,3,8,5,10,11,4,9,6,1,7,2,0

by_depth
+++++++++
The execution order will be
12,13,3,8,5,1,10,11,7,4,9,6,2,0
