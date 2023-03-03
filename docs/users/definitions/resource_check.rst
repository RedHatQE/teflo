Resource Check
==============

Teflo's Resource Dependency Check Section is optional. It is run during the Validate task
Resource_check is a dictionary which takes in three keys **monitored_services (formerly was service), playbook, script**

Monitored_Services
~~~~~~~~~~~~~~~~~~

User can define a list of external components to check if their status is up or not.
if all components are up the scenario will be executed .If one or more components are
down the scenario will exit with an error. It will also indicate if a component name
given is invalid.

The key "resource_check_endpoint" must be set in the teflo.cfg file to actually
perform check. If not set this section is ignored. The "resource_check_endpoint"
must be the URL of a "Cachet" status page endpoint. Component names must be valid
for that status page

.. code-block:: yaml

   [defaults]
   log_level=info
   workspace=.
   data_folder=.teflo
   resource_check_endpoint=<URL>


Playbook/ Script
~~~~~~~~~~~~~~~~

User can put in a list of customized playbooks or scripts to validate certain things
before starting their scenario. if any of the user defined validation playbook/scripts
fail the scenario will not be run.

All playbooks and scripts are run only on the localhost from where teflo is being executed.
Teflo will not be able to take any output from these scripts/playbooks and make any
decisions based on that
Teflo will consider the resource _check successfull or not based on the return code received
after running the playbook or script

Teflo uses the ansible to run these playbooks and scripts. User should define playbooks and
scripts similar to how it is defined in the `Execute <./execute.html>`_ section of Teflo


Example 1
~~~~~~~~~

Using service, playbook, script

.. literalinclude:: ../../../examples/docs-usage/resource_check.txt
    :lines: 2-43

Example 2
~~~~~~~~~

Using service

.. literalinclude:: ../../../examples/docs-usage/resource_check.txt
    :lines: 46-61
