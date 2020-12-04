Configuration
=============

This topic will cover configuring teflo by a configuration file and how you
can configure existing tools that teflo uses.

.. code-block:: none

    ├── ansible
    └── teflo

ansible
-------

Ansible is heavily used throughout teflo. It is the primary tool used for
performing configuration against remote machines. It is recommend that you
create an ansible configuration file to be used during a teflo run. This
allows you to control how you want to configure ansible and teflo will just
consume it. Please see the `ansible <ansible>`_ directory for a sample
ansible configuration file.

Please visit ansibles documentation for `configuring ansible <https://
docs.ansible.com/ansible/latest/installation_guide/intro_configuration.html>`_

teflo
------

Teflo requires you to create a configuration file to control various settings
teflo needs. This is where you can define default settings teflo accepts,
provider credentials, orchestrator settings and much more. Please see the
`teflo <teflo>`_ directory for a sample teflo configuration file. The
example file will have all the available configuration settings you can set.
You can take this file and modify it to your needs.
