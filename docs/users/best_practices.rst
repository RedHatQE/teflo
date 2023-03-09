Best Practices
==============

Data pass-through
-----------------

Please visit the following `page <data_pass_through.html>`_ to understand how
you can pass data within teflo tasks.


Scenario Structure
------------------

The intended focus of this section is to provide a standard structure for
building multi product scenarios. This is just a standard that can be adopted,
as a best practice, but is not required for running teflo. Having a solid
structure as a foundation will help lead to easier maintenance during the
scenarios lifespan. Along with faster turn around for creating new multi
product scenarios.

.. note::

    The advantage to a standard structure allows for other users to easily
    re-run & update a scenario in their environment with minimal effort.
    It will also help with consistency in teflo's usage, making it easier
    to understand someone's scenario.


.. code-block:: bash

    template/
    ├── ansible
    ├── ansible.cfg
    ├── teflo.cfg
    ├── jenkins
    │   ├── build
    │   │   ├── ansible.cfg
    │   │   ├── auth.ini
    │   │   ├── build.sh
    │   │   ├── hosts
    │   │   └── site.yml
    │   ├── Jenkinsfile
    │   └── job.yml
    ├── keys
    ├── Makefile
    ├── README.rst
    ├── scenario.yml
    ├── common_scenario.yml
    └── tests


The above scenario structure has additional files that are not required for
executing teflo. The extra files are used for easily running the scenario
from a Jenkins job. Below are two sections which go into more detail regarding
each file.

Teflo Files
~~~~~~~~~~~~

Based on the standard scenario structure, lets review the directories and files
which teflo consumes.  For now, the jenkins directory and the Makefile will
be ignored as they are related to creating a Jenkins job and not required for
executing teflo.


.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Name
        - Description
        - Required

    *   - ansible
        - The ansible directory is where you can define any ansible files
          (roles, playbooks, etc) that your scenario needs to use. Teflo will
          load and use these files as stated within your scenario descriptor
          file.
        - No

    *   - ansible.cfg
        - The ansible.cfg defines any settings for ansible that you wish to
          override their default values. It is **highly** recommend for each
          scenario to define their own file.
        - No

    *   - teflo.cfg
        - This is a required teflo configuration file.  It is recommended to
          remove the credentials in the file so the credentials are not under
          source control; however, when running you can either update the
          credentials or save the credentials in another teflo.
        - Yes

    *   - keys
        - The keys directory is an optional directory to set ssh keys used for
          contacting the machines in the scenario.
        - No

    *   - scenario.yml
        - The scenario.yml is your scenario descriptor file. This file
          describes your entire E2E multi product scenario.
        - Yes

    *   - common_scenario.yml
        - This is the scenario file used in the include section of the scenario.yml.
        - No

    *   - tests
        - This is a directory where all the tests that are run during the
          execution are stored.
        - No

With this scenario structure you can easily run teflo from the command line
or from a Jenkins job.  See the following section for more details.


Handing Off A Scenario
----------------------

After you successfully created a scenario descriptor file that describes an
end to end scenario, it should take minimal effort to hand off the scenario
for someone else to run. Especially if you followed the previous topic for
a baseline for your `scenario structure
<best_practices.html#scenario-structure>`_. You need to send all your files in
the scenario structure, and tell them to make minor modifications, which are
described below:


If the person handing off the scenario is using the same tools for
provisioning (i.e. all your machines are provisioned using OpenStack
and you hand off to someone else to run the scenario who also plans
to provision their resources using OpenStack), it is really simple. You just
need to follow the following steps:

 #. Tell them to set their credentials for their resource in their `teflo.cfg
    <configuration.html#teflo-configuration>`_ file, using the same name that you
    used in your scenario descriptor file.  A good tip would be to give them
    your teflo.cfg file with your `credentials
    <definitions/credentials.html#credentials>`_  removed.  Also if using the
    recommend scenario structure, you should be able to tell the user to set
    their credentials in a separate teflo.cfg file that they refrence with the
    **TEFLO_SETTINGS** environment variable prior to running teflo.
 #. Tell them to update references to the ssh keys that you used for machine
    access.

If you are handing off to a person that plans to use a different tool for
provisioning this can be more complicated.  A good tip for this case would
be to tell them provision their systems first and inject the driver machine's
ssh key into all the machines, and then redefine their systems in teflo
as `static machines <definitions/provision.html#definining-static-machines>`_.
If this is not an option, the user would have to
redefine each of their systems with the correct keys for the provisioning
system they plan to use.  Please see the `provisioning
<definitions/provision.html#provision>`_ documentation for all options.


