Using Localhost
===============

There may be a scenario where you want to run cmds or scripts on the
local system instead of the provisioned resources.  There are couple options
to be able to do this.

Explicit Localhost
------------------

The following is an example of a statically defined local machine:

.. _localhost_example:

Example
+++++++

.. literalinclude:: ../../examples/docs-usage/orchestrate.txt
    :lines: 331-363

When explicitly defined, this host entry is written to the master inventory
file and the localhost will be accessible to ALL the Orchestrate and Execute tasks
in the scenario.

Implicit Localhost
------------------

As of 1.6.0, The use of any other arbitrary hostname will not be supported to infer localhost.
It must be *localhost* that is used as a value to *hosts* in the Orchestrate or Execute sections,
Teflo will infer that the intended task is to be run on the localhost.

Example
+++++++

Here an Orchestrate and an Execute task refer to *localhost*,
respectively, that are not defined in the provision section.

.. code-block:: yaml

    ---
    provision:
      - name: ci_test_client_b
        groups:
        - client
        - vnc
        ip_address: 192.168.100.51
        ansible_params:
           ansible_private_ssh_key: keys/test_key

    orchestrate:
      - name: test_setup_playbook.yml
        description: "running a test setup playbook on localhost"
        orchestrator: ansible
        hosts: localhost

    execute:
      - name: test execution
        description: "execute some test script locally"
        hosts: localhost
        executor: runner
        ignore_rc: False
        shell:
          - chdir: /home/user/tests
            command: python test_sample.py --output-results suite_results.xml
            ignore_rc: True
        artifacts:
          - /home/user/tests/suite_results.xml
