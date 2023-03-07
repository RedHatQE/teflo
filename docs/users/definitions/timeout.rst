Timeout settings for Teflo Tasks
==================================

This feature will allow users to set  a time limit for all the teflo tasks. This can be done in either of the following two ways

1. defining the **timeout** fields in teflo.cfg. These values will be applied throughout the scenario descriptor file:

    .. code-block:: bash

        [timeout]
        provision=500
        cleanup=1000
        orchestrate=300
        execute=200
        report=100
        validate=10

2. defining the **timeout** fields in SDF. Here you can define below timeouts for individual task blocks within the SDF:

    **validate_timeout, provision_timeout, orchestrate_timeout, execute_timeout, report_timeout, cleanup_timeout, notification_timeout**

    .. code-block:: bash

        ---
        name: example
        description: An example scenario for timeout

        provision:
        - name: test
            group: client
            provisioner: linchpin-wrapper
            provider:
            name: openstack
            credential: openstack
            image: rhel-7.4-server-x86_64-released
            flavor: m1.small
            keypair: {{ key }}
            networks:
                - provider_net_cci_4
            ansible_params:
            ansible_user: cloud-user
            ansible_ssh_private_key_file: /home/junqizhang/.ssh/OCP
            # you define provision_timeout, orchestrate_timeout, cleanup_timeout, report_timeout here from SDF
            provision_timeout: 200

        report:
        - name: SampleTest.xml
            description: import results to polarion
            executes: junitTestRun
            provider:
            credential: polarion-creds
            name: polarion
            project_id: Teflo1
            testsuite_properties:
                polarion-lookup-method: name
                polarion-testrun-title: e2e-tests
            report_timeout: 120

.. note:: **If the timeout values are defined from SDF, it
            will overwrite the timeout values defined from
            teflo.cfg**
