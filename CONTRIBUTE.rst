Welcome!

The teflo development team welcomes your contributions to the project. Please
use this document as a guide to working on proposed changes to teflo. We ask
that you read through this document to ensure you understand our development
model and best practices before submitting changes.

Any questions regarding this guide, or in general? Please feel free to
file an `issue <https://github.com/RedHatQE/teflo/issues>`_

Release Cadence
---------------
The release cadence of the project follows the rules below,
all contributions are welcome and please be aware of the cadence.
For general usage users/contributors can fork the develop branch in order to use the latest changes

#. **Develop** is the branch contributions are made on
#. **Master** branch is the stable branch
#. Release a new version in every 5 weeks
    #. Changes will be evaluated and merged into master ,if suitable ,from develop branch and then released to the PyPi server
#. The release will be major/minor/patch based on :
    #. Major changes, e.g. major refactor or backward compatibility break, etc. (major release)
    #. Other changes like new features or code refactoring that are not major (minor)
    #. Bug fixes (patch)
#. Labels are recommended for issues and PRs in the following manner
    #. **Critical** : For any urgent blocking issues
    #. **Bug** : For any bugs
    #. **New_feature** : For any new feature request
#. Hotfix release may be available before usual release cycle based on issue severity. A hotfix release is considered if:
    #. It is blocking user automation and no workaround is available
    #. Develop branch installation does not unblock the user.

Branch Model
------------

Teflo has two branches
 - **develop** - all work is done here
 - **master** - stable tagged release that users can use

The master branch is a protected branch. We do not allow commits directly to
it. Master branch contains the latest stable release. The develop branch is
where all active development takes place for the next upcoming release. All
contributions are made to the develop branch.

Most contributors create a new branch based off of develop to create their
changes.

How to setup your dev environment
---------------------------------

Lets first clone the source code. We will clone from the develop branch.

.. code-block:: bash

    $ git clone https://github.com/RedHatQE/teflo.git -b develop

Next lets create a Python virtual environment for teflo. This assumes you
have virtualenv package installed.

.. code-block:: bash

    $ mkdir ~/.virtualenvs
    $ virtualenv ~/.virtualenvs/teflo
    $ source ~/.virtualenvs/teflo/bin/activate

Now that we have our virtual environment created. Lets go ahead and install
the Python packages used for development.

.. code-block:: bash

    (teflo) $ pip install -r teflo/test-requirements.txt

Let's create our new branch from develop. Do this step from teflo's root folder

.. code-block:: bash

    (teflo) $ cd teflo
    (teflo) $ git checkout -b <new branch>
    (teflo) $ cd ..

Finally install the teflo package itself using editable mode.

.. code-block:: bash

    (teflo) $ pip install -e teflo/.

You can verify teflo is installed by running the following commands.

.. code-block:: bash

    (teflo) $ teflo
    (teflo) $ teflo --version

You can now make changes/do feature development in this branch

How to run tests locally
------------------------

We have the following standards and guidelines

 - All tests must pass
 - Code coverage must be above 50%
 - Code meets PEP8 standards

Before any change is proposed to teflo we ask that you run the tests
to verify the above standards. If you forget to run the tests,
we have a github actions job that runs through these on any changes.
This allows us to make sure each patch meets the standards.

We also highly encourage developers to be looking to provide more tests
or enhance existing tests for fixes or new features they maybe submitting.
If there is a reason that the changes don't have any accompanying tests
we should be annotating the code changes with TODO comments with the
following information:

 - State that the code needs tests coverage
 - Quick statement of why it couldn't be added.

.. code-block:: bash

    #TODO: This needs test coverage. No mock fixture for the Teflo Orchestrator to test with.


How to run unit tests
~~~~~~~~~~~~~~~~~~~~~

You can run the unit tests and verify pep8 by the following command:

.. code-block:: bash

    (teflo) $ make test-functional

This make target is actually executing the following tox environments:

.. code-block:: bash

    (teflo) $ tox -e py3-unit

.. note::
    we use a generic tox python 3 environment to be flexible towards developer
    environments that might be using different versions of python 3. Note the
    minimum supported version of python is python 3.6.

How to run localhost scenario tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The local scenario test verify your changes don't impact core functionality in the framework
during provision, orchestrate, execute, or report. It runs a scenario descriptor file using
localhost, a teflo.cfg, some dummy ansible playbooks/scripts, and dummy test artifacts.
It does NOT run integration to real external system like OpenStack or Polarion.

.. code-block:: bash

    (teflo) $ make test-scenario

This make target is actually executing the following tox environments:

.. code-block:: bash

    (teflo) $ tox -e py3-scenario

.. note::
    If there is a need to test an integration with a real external system
    like OpenStack or Polarion, you could use this scenario as a basis of a
    more thorough integration test of your changes. It would require modifying
    the scenario descriptor and teflo.cfg file with the necessary parameters and
    information. But it is not recommended to check in this modified scenario
    as part of your patch set.

How to propose a new change
---------------------------

The teflo project resides in Red Hat QE github space. To send the new changes you will
need to create a PR against the develop branch .
Once the PR is sent, the github actions will runt the unit tests and will inform the
maintainers to review the PR.

At this point you have your local development environment setup. You made some
code changes, ran through the unit tests and pep8 validation. Before you submit
your changes you should check a few things

If the develop branch has changed since you last pulled it down. it
is important that you get the latest changes in your branch.
You can do that in two ways:

Rebase using the local develop branch

.. code-block:: bash

    (teflo) $ git checkout develop
    (teflo) $ git pull origin develop
    (teflo) $ git checkout <branch>
    (teflo) $ git rebase develop

Rebase using the remote develop branch

.. code-block:: bash

    (teflo) $ git pull --rebase origin/develop

Finally, if you have mutiple commits its best to squash them into a single commit.
The interactive rebase menu will appear and guide you with what you need to do.

.. code-block:: bash

    (teflo) $ git rebase -i HEAD~<the number of commits to latest develop commit>

Once you've completed the above you're good to go! All that is left is
to submit your changes to your branch and create a new PR against the develop branch

Submitting the PR
~~~~~~~~~~~~~~~~~

Once a set of commits for the feature have been completed and tested. It is time to
submit a Pull Request. Please see the github article to get an idea about
submitting a PR, `Creating a pull request <https://help.github.com/articles/creating-a-pull-request/>`_.

Guidelines for submitting the PR
================================

1. Submit the Pull Request (PR) against the **develop** branch.

2. Provide a ticket number if available in the title

3. Provide a description.

Once the PR is created, it will need to be reviewed, and CI automation testing
must be executed. It is possible that additional commits will be needed to
pass the tests, address issues in the PR, etc.

Once the PR is approved, it can be merged.

You can also install the github cli and send PRs using gh cli
More information on how to install and where to find binaries is `here <https://github.com/cli/cli/releases>`__

When using the cli first time from your terminal you may have to authenticate your device.
If web option is used it opens up a browser to put in the given code

.. code-block:: bash

    $ gh auth  login --web
    - Logging into github.com

    ! First copy your one-time code: ABCD-ABCD
    - Press Enter to open github.com in your browser...
    This tool has been deprecated, use 'gio open' instead.
    See 'gio help open' for more info.

    ✓ Authentication complete. Press Enter to continue...

    ✓ Logged in as user123

Once you are authenticated you can send in the PR, using the create command, It will ask certain questions
and then ask you to submit the PR.

More information on how to use `gh cli <https://cli.github.com/manual/>`_

.. code-block:: bash

   $ gh pr create --title "Feature umb importer" --reviewer rujutashinde --base develop
    Warning: 9 uncommitted changes
    ? Where should we push the 'tkt_218' branch? Skip pushing the branch

    Creating pull request for tkt_218 into develop in RedHatQE/teflo

    ? Body <Received>
    ? What's next? Submit
    https://github.com/RedHatQE/teflo/pull/01


.. note:: Merging is currently done only by the maintainers of the repo
          This will be opened up to contributors at a future time

Feature Toggles
---------------

Although this doesn't happen very often this does warrant a mention. If a feature
is too big to, where it would better suited to merge incrementally in a
'trunk' style of development. Then we should consider utilizing
feature toggles so as the develop branch can stay releasable at all times.

The teflo.cfg is capable of reading feature toggles and utilizing them.
It's a very rudimentary implementation of a feature toggle mechanism but it has worked in
the past on short notice. Below is the process when working at adding functionality to
one of the main resources (Host, Actions, Executions, Reports).


To the resource we are working on define the following feature toggle method

.. code-block:: python

    def __set_feature_toggles_(self):

    self._feature_toggles = None

    for item in self.config['TOGGLES']:
        if item['name'] == '<name of resource the feature belongs to>':
            self._feature_toggles = item


Then in the __init__ function of the resource you are working on add the
following lines of code. This will help to keep teflo running original code
path unless explicitly told to use the new feature

.. code-block:: python

    if self._feature_toggles is not None and self._feature_toggles['<name of new feature toggle>'] == 'True':
        <new feature path>
    else:
        <original code path>


Now in your teflo config file when you want to use the new code path
for testing or continued development you can do the following:

.. code-block:: bash

    [orchestrator:ansible]
    log_remove=False
    verbosity=v

    [feature_toggle:<resource name from step 1>]
    <feature toggle name specified in step 2>=True

How to build documentation
--------------------------

If you are working on documentation changes, you probably will want to build
the documentation locally. This way you can verify your change looks good. You
can build the docs locally by running the following command:

.. code-block:: bash

    (teflo) $ make docs

This make target is actually executing the following tox environments:

.. code-block:: bash

    (teflo) $ tox -e docs

.. _plugin_dev:

How to write an plugin for teflo
--------------------------------

For developers who wish to put together their own plugins can use Teflo's plugin templates to do so.
The plugin templates creates a directory with required imports from teflo project based on the
plugin type to be created ( provisioner/orchestrator/executor/importer/notification).
Once templates are in place developers can then go ahead with actual plugin work

How to use plugin templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use this template to create your plugin folder:

1. install cookiecutter

.. code-block:: bash

      pip install cookiecutter

2. Clone the teflo_examples repo

.. code-block:: bash

      git clone git@github.com:RedHatQE/teflo_examples.git

3. Go to the space where you want your plugin folder to be created then run the command

.. code-block:: bash

    cookiecutter <path to the cloned teflo_examples repo>/teflo_plugin_template

4. When you run this you will be prompted to provide values for the variables in the
   cookiecutter json file, Below are the variables and their description.
   User should provide the values it needs, else the default values will be taken

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Variable
        - Description
        - Default Value

    *   - teflo_plugin_type
        - type of teflo plugin to be created
          (provisioner or orchestrator or executor or importer or notification)
        - provisioner

    *   - directory_name
        - name to be give to the plugin repo directory.
        - teflo_provisionerX_plugin

    *   - plugin_name
        - name of the python file where your actual plugin code will reside
        - provx_plugin


    *   - plugin_class_name
        - the name of the class within the python file
        - ProvXProvisionerPlugin

    *   - test_class_name
        - name to be given to the unit test file under tests folder.
          This is auto generated if left blank
        - test_provx_plugin


    *   - plugin_description
        - Plugins description that goes into the setup.py
        - teflo provisioner plugin

    *   - jenkins_ci_job_link
        - jenkins ci job link once you have created that.
          This gets  updated in the jenkins/Jenkinsfile
        - your ci job link

    *   - plugin_url
        - plugin url needed to start the ci job. This gets  updated in the jenkins/Jenkinsfile
        - plugin url on gitlab/github

    *   - authors
        - The value that gets updated in the AUTHORS file
        - CCIT tools dev team <ci-ops-qe@redhat.com>

.. note::

    Here the variables **jenkins_ci_job_link** and **plugin_url** can be left default, and then these values can be updated
    in the jenkins/Jenkinsfile once user has the CI job url and repo url ready.
    These variables are meant to be more as a place holder for users to know where they can update
    later

.. note::

    Read `here <https://cookiecutter.readthedocs.io/en/1.7.2/index.html>`__ about cookiecutter package

Example
~~~~~~~

`Example <https://github.com/RedHatQE/teflo_examples/tree/master/teflo_plugin_template#example>`__ to use the plugin template


Template Guidelines
~~~~~~~~~~~~~~~~~~~
.. note::

    The above plugin template repo was created based on the following guidelines. These are meant for developers
    to understand. It is recommended for developers to make use of the template while working
    on Teflo Plugins

1. The new plugin will need to import one of these Teflo classes based on the plugin they wish to develop
   Teflo Plugin classes:
   **ProvisionerPlugin**
   **OrchestratorPlugin**
   **ExecutorPlugin**
   **ImporterPlugin**
   **NotificationPlugin**
   from the **teflo.core** module.

2. It should have the plugin name using variable **__plugin_name__**

3. It should implement the following key functions
     - For provisioner plugins implement the **create**, **delete**, and **validate** functions
     - For importer plugins implement the **import_artifacts** and **validate** functions


4. You should define a schema for Teflo to validate the required parameter inputs
   defined in the scenario file. Teflo use's
   `pyqwalify <https://pykwalify.readthedocs.io/en/master/>`__ to validate schema. Below is an
   example schema

   .. code-block:: yaml

        ---
        # default openstack libcloud schema

        type: map
        allowempty: True
        mapping:
          image:
            required: True
            type: str
          flavor:
            required: True
            type: str
          networks:
            required: True
            type: seq
            sequence:
              - type: str
          floating_ip_pool:
            required: False
            type: str
          keypair:
            required: False
            type: str
          credential:
            required: False
            type: map
            mapping:
              auth_url:
                type: str
                required: True
              username:
                type: str
                required: True
              password:
                type: str
                required: True
              tenant_name:
                type: str
                required: True
              domain_name:
                type: str
                required: False
              region:
                type: str
                required: False

   Once you've created your schema and/or extension files. You can define them in the plugin
   as the following attributes **__schema_file_path__** and **__schema_ext_path__**.

   .. code-block:: python

    __schema_file_path__ = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                        "files/schema.yml"))
    __schema_ext_path__ = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                       "files/lp_schema_extensions.py"))

   To validate the schema, you can import the **schema_validator** function from the **teflo.helpers**
   class

   .. code-block:: python

    # validate teflo plugin schema first
        schema_validator(schema_data=self.build_profile(self.host),
                         schema_files=[self.__schema_file_path__],
                         schema_ext_files=[self.__schema_ext_path__])

5.
   To enable logging you can create a logger using the **create_logger** function or calling python's **getLogger**

6. The plugin needs to add an entry point in its setup.py file so that it can register the plugin where
   Teflo can find it. For provsioners register the plugin to **provisioner_plugins** and for importers
   register to **importer_plugins**. Refer the example below:

.. code-block:: python

    from setuptools import setup, find_packages

    setup(
        name='new_plugin',
        version="1.0",
        description="new plugin for teflo",
        author="Red Hat Inc",
        packages=find_packages(),
        include_package_data=True,
        python_requires=">=3",
        install_requires=[
            'teflo@git+https://code.engineering.redhat.com/gerrit/p/teflo.git@master',
        ],
        entry_points={
                      'importer_plugins': 'new_plugin_importer = <plugin pckage name>:NewPluginClass'
                     }
    )

Please refer `here <https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins>`_
for more information on entry points

Example for plugin:

.. code-block:: python

    from teflo.core import ImporterPlugin

    class NewPlugin(ImporterPlugin):

        __plugin_name__ = 'newplugin'

        def __init__(self, profile):

            super(NewPlugin, self).__init__(profile)
            # creating logger for this plugin to get added to teflo's loggers
            self.create_logger(name='newplugin', data_folder=<data folder name>)
            # OR
            logger = logging.getLogger('teflo')

        def import_artifacts(self):
            # Your code

