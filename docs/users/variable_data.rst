Using Jinja Variable Data
=========================

Teflo uses Jinja2 template engine to be able to template variables
within a scenario file. Teflo allows template variable data to be
set as environmental variables as well as pass variable data via command line.

You can also store the variable data in a file and provide the file path in teflo.cfg

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
            count: {{ count | default('1') }}
            keypair: test-keypair
            networks:
              - {{ networks | default('provider_net_ipv6_only') }}


The variable data can now be passed in one of three ways.

Raw JSON
--------

You can pass in the data raw as a JSON dictionary

.. code-block:: bash

    teflo run -s scenario.yml -t provision --vars-data '{"flavor": "m2.small", "name": "test"}'


.. code-block:: bash

    teflo run -s scenario.yml -t provision --vars-data '{"flavor": "m2.small", "name": "test"}'
    --vars-data '{"count": "2"}'

Variable File
-------------

You can pass in a variable file in yaml format defining the variable data you need. The variable file
needs to be placed in the teflo workspace as **var_file.yml** or as yaml files under **vars directory**

User can also set **var_file** as a parameter in the **defaults section of teflo.cfg**.
This way user can avoid passing variable data via command line at every run

Following is the precedence of how Teflo looks for variable data:

#. Via command line
#. defaults section of teflo.cfg
#. var_file.yml under the teflo workspace
#. yml files under the directory vars under teflo workspace


Below is an example of the contents of a variable file template_file.yaml.

.. code-block:: yaml

    ---
    flavor: m2.small
    networks: provider_net_cci_5
    name: test

You can pass in the variable file directly

.. code-block:: bash

    teflo run -s scenario.yml -t provision --vars-data template_file.yml --vars-data '{"count": "2"}'

If using teflo.cfg this can be set as below. The var_file param can be a path to the variable file or path to
the directory where the variable file is stored. If Teflo identifies it a directory then recursively it looks for all
files with .yml or .yaml extension within that directory.

.. code-block:: bash

   [defaults]
   var_file=~/template_file.yml


.. code-block:: bash

   [defaults]
   var_file=~/var_dir

The above example will look like

.. code-block:: bash

    teflo run -s scenario.yml -t provision

Directory with multiple .yml files
-----------------------------------

You can pass in a directory path containing multiple .yml files.
The code will look for files ending with '.yml'

.. code-block:: bash

    teflo run -s scenario.yml -t provision --vars-data ~/files_dir
    --vars-data '{"count": "2", "key": "val"}'


Nested Variable Usage
----------------------
Currently teflo supports nested variable using any of above methods

**Note**:
The nested variable can only be string after parsing

For example:

A nested variable can look like below:

#. nested_var: "hello"
#. nested_var: {{ hey }}
#. nested_var: "hello{{ hey }}"



You can

#. Use multiple layer nested vars
    .. code-block:: yaml

        name: {{ hello }}
        hello: {{ world }}
        world: {{ Hey }}
        Hey: "I'm a developer"

#. Use multiple nested variables inside one filed
    .. code-block:: yaml

        name: "{{ hello }} {{ world }}"
        hello: "asd"
        world: {{ Hey }}
        Hey: "I'm a developer"

#. Use nested variable in a list or dict
    .. code-block:: yaml

        name: 
            Tom: {{ TomName }}
            Jack: {{ JackName }}
        TomName: "Tom Biden"
        JackName: "Jack Chen"
        adress:
            - {{ street }}
            - {{ city }}
            - {{ state }}
        street: "Boston Street"
        city: "Boston"
        state: "Massachusetts"

.. note::

   **TEFLO_DATA_FOLDER** , **TEFLO_RESULTS_FOLDER** and **TEFLO_WORKSPACE** are TEFLO
    environmental variables that are made available during a teflo run,
    which can be used in scripts and playbooks. They provide the absolute path for teflo's
    data folder, results folder and workspace respectively