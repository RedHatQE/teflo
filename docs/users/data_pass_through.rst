Data Pass-through
=================

This topic focuses on how you can pass data between different tasks of teflo.

Orchestrate
-----------

Teflo's orchestrate task is focused with one goal, to configure your test
environment. This configuration consists of install/configure products, test
frameworks, etc. This is all defined by the user. When you setup your scenario
descriptor file (SDF) orchestrate section, you define the actions you wish to
run. Lets look at an example below:

.. literalinclude:: ../../examples/docs-usage/orchestrate.yml
    :lines: 297-327

The orchestrate section above has two actions to be run. Both actions are
ansible playbooks. This example shows installing product a then product b.
Where product b requires return data from the installation of product a. How
can the second playbook installing product b get the return data from product
a playbook? The recommended way for this is to write return data from product
a to disk. This would make the data persistent since when a playbook exits,
anything wrote to memory goes out of scope. Using ansible custom facts to
write to disk allows the second playbook to have access to the return data
from product a install.

This example can be found at the following
`page <https://github.com/RedHatQE/teflo_examples/tree/master/orchestrate/ansible/data_pass_through>`_
for you to run.

.. note::

    Please note the example uses localhost so everything is wrote to the same
    machine. In a real use case where you want to access the data from a
    secondary machine where product b is installed. Inside your playbook to
    install product b, you would want to have a task to delegate to the
    product a machine to fetch the return data needed.

An optional way to pass data through from playbook to playbook is to have one
master playbook. Inside the master playbook you could have multiple plays that
can access the return data from various roles and tasks. Please note that this
way is not recommended by teflo. Teflos scenario descriptor file allows
users with an easy way to see all the configuration that is performed to setup
the environment. With having multiple playbooks defined under the orchestrate
section. It makes it easier to understand what the scenario is configuring.
When having just one action defined calling a master playbook. It then requires
someone to go into the master playbook to understand what actions are actually
taking place.

There are cases where you want to pass some data about the test machines as a
means of starting the configuration process rather during the configuration
process. For example, say you've tagged the test machine with metadata that
would be useful to be used in the configuration as extra variables or
extra arguments. Teflo has the ability to template this data as parameters.
Let's take a look at a couple examples:

.. code-block:: yaml

    ---
    provision:
      - name: host01
        groups: node
        provider:
          name: openstack
          ...
        ip_address:
          public: 1.1.1.1
          private: 192.168.10.10
        metadata:
          key1: 'value1'
          key2: 'value2'
          ...
        ansible_params:
          ansible_user: cloud-user
          ...

    orchestrate:
      - name: orc_playbook
        description: run configure playbook and do something with ip
        orchestrator: ansible
        hosts: host01
        ansible_playbook:
          name: ansible/configure_task_01.yml
        ansible_options:
          extra_vars:
            priv_ip: <NEED PRIVATE IP OF HOST>

      - name: orc_script
        description: run configure bash script and do something with metadata
        orchestrator: ansible
        hosts: host01
        ansible_script:
          name: scripts/configure_task_02.sh
        ansible_options:
          extra_args: X=<NEED METADATA> Y=<NEED METADATA>

We have two orchestrate tasks, one wants to use the private ip address of the machine
to configure something on the host. The other wants to use some metadata that was tagged
in the test resource. Here is how you could do that

.. code-block:: yaml

    ---
    provision:
      <truncated>

    orchestrate:
      - name: orc_task1
        description: run configure playbook and do something with ip
        orchestrator: ansible
        hosts: host01
        ansible_playbook:
          name: ansible/configure_task_01.yml
        ansible_options:
          extra_vars:
            priv_ip: '{ host01.ip_address.private }'

      - name: orc_task2
        description: run configure bash script and do something with metadata
        orchestrator: ansible
        hosts: host01
        ansible_script:
          name: scripts/configure_task_02.sh
        ansible_options:
          extra_args: X={ host01.metadata.key1 } Y={ host01.metadata.key2 }


Teflo will evaluate these parameters and inject the correct data before passing
these on as parameters for Ansible to use.

.. note::

   extra_vars used under ansible_options is a dictionary , hence the value being injected needs to be in single or
   double quotes else data injection will not take place
   e.g. '{  host01.ip_address.private }' or "{ host01.ip_address.private }"


Execute
-------

Teflo's execute task is focused with one goal, to execute the tests defined
against your configured environment. Some tests may require data about the
test machines. The question is how can you get information such as the IP
address as a parameter option for a test command? Teflo has the ability to
template your test command prior to executing it. This means it can update
any fields you set that require additional data. Lets look at an example
below:

.. code-block:: yaml

    ---
    provision:
      - name: driver01
        groups: driver
        provider:
          name: openstack
          ...
        ip_address: 0.0.0.0
        metadata:
          key1: value1
          ...
        ansible_params:
          ansible_user: cloud-user
          ...

      - name: host01
        groups: node
        provider:
          name: openstack
          ...
        ip_address: 1.1.1.1
        metadata:
          key1: value1
          ...
        ansible_params:
          ansible_user: cloud-user
          ...

    execute:
      - name: test
        executor: runner
        hosts: driver
        shell:
          - command: test_command --host <NEEDS_IP_OF_HOST01>

The above example has two test machines and the one of the tests requires a
parameters of the host01 machine ip address. This can easily be passed to the
test command using templating. Lets see how this is done:

.. code-block:: yaml

    ---
    provision:
    <truncated>

    execute:
      - name: test
        executor: runner
        hosts: driver
        shell:
          - command: test_command --host { host01.ip_address }

As you can see above you can reference any data from the host resource
defined above. You could also access some of the metadata for the test.

.. code-block:: yaml

    ---
    provision:
    <truncated>

    execute:
      - name: test
        executor: runner
        hosts: driver
        shell:
          - command: test_command --host { host01.ip_address } \
            --opt1 { host01.metadata.key1 }

Teflo will evaluate the test command performing the templating (setting the
correct data) and then executes the command. These are just a couple examples
on how you can access data from the host resources defined in the provision
section. You have full access to all the key:values defined by each host
resource.

.. Note::

    if the instance has been connected to multiple networks and you are using
    the linchpin-wrapper provisioner, the ip addresses assigned to the instance
    from both networks will be collected, and stored as a dictionary. Hence, to
    use the data-passthrough in this situation you would do something like the
    following:

    { host01.ip_address.public }
