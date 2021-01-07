Glossary
========

.. glossary::
    Ansible
        Open source software that automates software provisioning,
        configuration management, and application deployment.
        `Ansible <https:www.ansible.com>`_

    beaker
        Resource management and automated testing environment.

    Cachet
        An open source status page system. `Cachet <https:cachethq.io>`_

    teflo
        Test Execution Framework Libraries and Onjects

    credentials (section)
        Required credential definitions for each resource that needs to be
        provisioned. Credentials are set in teflo.cfg file. They are
        referenced by name in the scenario.

    dnf
        A software package manager that installs, updates, and removes packages
        on RPM-based Linux distributions.

    E2E
        end to end

    execute (section)
        Defines the location, setup, execution and collection of results and
        artifacts of tests to be executed for a scenario.

    git
        A version-control system for tracking changes in computer files and
        coordinating work on those files among multiple people.

    Jenkins
        Open source automation server, Jenkins provides hundreds of plugins to
        support building, deploying and automating any project.
        `Jenkins <https://jenkins.io/>`_

    orchestrate (section)
        Defines the configuration and setup to be performed on the resources of
        a scenario in order to test the system properly.

    pip
        A package management system used to install and manage software packages
        written in Python.

    provision (section)
        Defines a list of resources and there inputs to be provisioned.

    PyPI
        The Python Package Index (PyPI) is a repository of software for the Python
        programming language.

    report (section)
        Defines the reporting mechanism of a scenario.

    resource (teflo)
        A host/node to provision or take action on.

    resource (external)
        External components that a scenario requires to run.

    resource check (section)
        Specifies a list of external resource components to check status of before
        running scenario. If any component not available the scenario will not run.

    role (ansible)
         Ways of automatically loading certain vars_files, tasks, and handlers based
         on a known file structure. Grouping content by roles allows easy sharing of
         roles with other users.

    role (teflo)
         The function assumed or part played by a node/host. Specified in provision
         section.

    section (teflo)
        The major areas a scenario is broken into. Sections of a scenario relate to a
        particular component within teflo. Valid sections are 'Resource Check',
        Credentials, Provision, Orchestrate, Execute and Report.

    scenario (teflo)
        A teflo scenario descriptor file. Teflo input file. SDF.

    SDF
        scenario descriptor file

    task
         An action to be performed.

    task (ansible)
         A call to an ansible module.

    task (teflo)
         Actions that are run against a scenario. Valid tasks are validate, provision
         orchestrate, execute, report and cleanup.

    task (orchestrate)
         A configuration action that will then correlate to an orchestrators task.
         The default orchestrator for teflo is Ansible.

    tox
         A generic virtualenv management and test command line tool.

    virtualenv
        A tool to create isolated Python environments.
        `Virtualenv <https://virtualenv.pypa.io/en/stable/#>`_

    YAML
        A human-readable data serialization language. It is commonly used for
        configuration files, but could be used in many applications where data is
        being stored or transmitted.

    yum
        Yellowdog Updater, Modified (YUM) is an open-source command-line
        package-management utility for computers running the GNU/Linux
        operating system using the RPM Package Manager

