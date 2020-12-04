Using Jinja Variable Data
=========================

Teflo uses Jinja2 template engine to be able to template variables
within a scenario file. Teflo allows template variable data to be
set as environmental variables as well as pass variable data via command line.

Here is an example scenario file using Jinja to template some variable data:

.. code-block:: yaml

    ---

    name: linchpin_vars_example
    description: template example

    provision:
      - name: db2_dummy
        provisioner: linchpin-wrapper
        groups: example
        credential: openstack
        resource_group_type: openstack
        resource_definitions:
          - name: {{ name | default('database') }}
            role: os_server
            flavor: {{ flavor | default('m1.small') }}
            image:  rhel-7.5-server-x86_64-released
            count: 1
            keypair: test-keypair
            networks:
              - {{ networks | default('provider_net_ipv6_only') }}


The variable data can now be passed in one of two ways.

Raw JSON
--------

You can pass in the data raw as a JSON dictionary

.. code-block:: bash

    teflo run -s scenario.yml -t provision --vars-data '{"flavor": "m2.small", "name": "test"}'

Variable File
-------------

You can pass in a variable file defining the variable data you need. The variable file
needs to be placed in the teflo workspace. Below is an example of the contents of a
variable file.

.. code-block:: yaml

    ---
    flavor: m2.small
    networks: provider_net_cci_5
    name: test

You can pass in the variable file directly

.. code-block:: bash

    teflo run -s scenario.yml -t provision --vars-data template_file.yml