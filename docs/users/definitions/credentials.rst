Credentials
===========

For each resource that needs to be provisioned or artifact that needs to be 
imported, credentials are required. These credentials will be set in the required 
`teflo.cfg file <../configuration.html#teflo-configuration>`_, and the credential 
name will be referenced in your scenario descriptor file in the provision section for each
resource or artifact that is defined.Or you can set the credentials from a separate file

Define credential from a separate file
--------------------------------------

You can also define the credentials by creating a credential file (For example,
credential.keys) and put all the credentials there. Users need to encrypt this
credentials file using ansible-vault. The path for this file needs to be provided
in the teflo.cfg as **CREDENTIAL_PATH**. The ansible-vault password needs to be provided
in the teflo.cfg file as **VAULTPASS**. These values are present under the default
section of the teflo.cfg file.

You need to define the **CREDENTIAL_PATH** and **VAULTPASS** fields 
in the **teflo.cfg**. 

.. note::
    **For the VAULTPASS, you can also export it to be an enviroment variable,
    so you can protect the password**

    the credentials can be either put in teflo.cfg OR put providing a separate credentials file. These are mutually exclusive

Example:

.. code-block:: yaml

  [defaults]
  log_level=debug
  data_folder=teflo_data/
  workspace=.
  inventory_folder=css_psi_customerzero/
  CREDENTIAL_PATH=credentials.key  
  VAULTPASS=abc 


Beaker Credentials
------------------

For Beaker, the following table is a list of required and optional keys for
your credential section in your teflo.cfg file.  You must set
either keytab and keytab_principal or username and password:

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - hub_url
        - The beaker server url.
        - String
        - True

    *   - keytab
        - name of the keytab file, which must be placed in the scenario
          workspace directory.
        - String
        - False

    *   - keytab_principal
        - The principal value of the keytab.
        - String
        - False

    *   - username
        - Beaker username.
        - String
        - False

    *   - password
        - Beaker username's password.
        - String
        - False

    *   - ca_cert
        - path to a trusted certificate file
        - String
        - False


Below is an example credentials section in the teflo.cfg file.  If the
credential was defined as below, it should be referenced in your teflo
scenario descriptor by the host as **credential: beaker-creds**:

.. code-block:: bash

  [credentials:beaker-creds]
  hub_url=<hub_url>
  keytab=<keytab>
  keytab_principal=<keytab_principal>
  username=<username>
  password=<password>
  ca_cert=<ca_cert_path>

The following is an example of a resource in the scenario descriptor file
that references this credential:

.. literalinclude:: ../../../examples/docs-usage/provision.yml
    :lines: 68-91

OpenStack Credentials
---------------------

For OpenStack, the following table is a list of required and optional keys for
your credential section in your teflo.cfg file.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - auth_url
        - The authentication URL of your OpenStack tenant. (identity)
        - String
        - True

    *   - tenant_name
        - The name of your OpenStack tenant.
        - String
        - True

    *   - username
        - The username of your OpenStack tenant.
        - String
        - True

    *   - password
        - The password of your OpenStack tenant.
        - String
        - True

    *   - region
        - The region of your OpenStack tenant to authenticate with.
        - String
        - False

    *   - domain_name
        - The name of your OpenStack domain to authenticate with.
          When not set teflo will use the 'default' domain
        - String
        - False

    *   - project_id
        - The id of your OpenStack project.
        - String
        - False

    *   - project_domain_id
        - The id of the project domain.
        - String
        - False


.. code-block:: bash

  [credentials:openstack-creds]
  auth_url=<auth_url>
  tenant_name=<tenant_name>
  username=<username>
  password=<password>
  region=<region>
  domain_name=<domain_name>
  project_id=<project id>
  project_domain_id=<project_domain_id>

The following is an example of a resource in the scenario descriptor file
that references this credential:

.. literalinclude:: ../../../examples/docs-usage/provision.yml
    :lines: 94-113

.. code-block:: yaml

    ---

    name: openstack resource
    description: define a teflo host openstack resource to be provisioned

    provision:
      - name: openstack-node
        role: node
        provider:
          name: openstack
          credential: openstack-creds
          image: rhel-7.5-server-x86_64-released
          flavor: m1.small
          networks:
            - '{{ network }}'
          floating_ip_pool: "10.8.240.0"
          keypair: '{{ keypair }}'
        ansible_params:
          ansible_user: cloud-user
          ansible_ssh_private_key_file: "keys/{{ keypair }}"


Email Credentials
-----------------

For email-notifier, the following table is a list of required and optional keys for
your credential section in your teflo.cfg file.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - smtp_host
        - The SMTP Server should be used to send emails.
        - String
        - True

    *   - smtp_port
        - The port number to use if not using the default port number.
        - String
        - False

    *   - smtp_user
        - The username to connect to your SMTP Server if authentication required
        - String
        - False

    *   - smtp_password
        - The password of the SMTP user to authenticate if required.
        - String
        - False

    *   - smtp_starttls
        - Whether to put the connection in TLS mode.
        - Boolean
        - False

.. code-block:: bash

  [credentials:email-creds]
  smtp_host=<smtp server fqdn>
  smtp_port=<port number>
  smtp_user=<user>
  smtp_password=<password>
  smtp_starttls=<True/False>
