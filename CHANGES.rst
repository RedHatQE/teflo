Version 2.3.0 (2023-02-06)
--------------------------

Bug Fixes
~~~~~~~~~
* Changed min python to v3.9 and ansible version to 2.14.0
* fix to get collection playbook installed in default path

Version 2.2.9 (2022-11-15)
--------------------------

Bug Fixes
~~~~~~~~~
* Fix install rsync on different versions

Version 2.2.8 (2022-11-7)
--------------------------

Enhancements
~~~~~~~~~~~~
* Added Support of Teflo aliases.

Bug Fixes
~~~~~~~~~
* Fix invalid value error for command show --show-graph -im.
* Added repo install if failed to find rsync package.
* Fix allow roles to be installed correctly from req files with only a list.

Version 2.2.7 (2022-09-19)
--------------------------

Documentation
~~~~~~~~~~~~~
* update Teflo and Teflo plugins copyright to 2022.

Enhancements
~~~~~~~~~~~~
* Improvements to downloading ansible roles/collections
* Upgrade urllib3

Bug Fixes
~~~~~~~~~
* Beaker Provisioner: append to authorized_keys rather than overwrite it
* Fix on_start trigger

Version 2.2.6 (2022-07-25)
--------------------------

Documentation
~~~~~~~~~~~~~
* Added comments in the pipeline.py to clarify the usage of filters.

Enhancements
~~~~~~~~~~~~
* Added strict validation to bkr_client schema.
* Added support of git ssh to clone remotes.
* Added coverage xml file in Unittest

Bug Fixes
~~~~~~~~~
* Fix running ansible collection

Version 2.2.5 (2022-05-16)
--------------------------

Enhancements
~~~~~~~~~~~~
* Added support of ansible group_vars files.
* Add support to grab ipv4 when node has multiple addresses.
* Add unit tests for notification problem

Version 2.2.4 (2022-04-18)
--------------------------

Bug Fixes
~~~~~~~~~
* Fixed the jinja template issue
* Upgrade Sphinx to be compatible with jinja2 v3.1.1
* Silence notify messages when no notifications enabled
* Fixed for Teflo does not take into account provision resources that do not match the supplied teflo label
* Fixed for DISPLAY_SKIPPED_HOSTS option is deprecated 

Version 2.2.3 (2022-03-11)
--------------------------

Bug Fixes
~~~~~~~~~
* Fixed issue with centos 8 image for unit tests
* Fixed ansible warnings in stderr
* Fixed preserve whitespace when dumping ansible output

Version 2.2.2 (2022-01-31)
--------------------------

Enhancements
~~~~~~~~~~~~
* make scenario graph size a static attribute
* Allow ANSIBLE_EXTRA_VARS_FILES option for orchestrate/execute task to pick up variable files provided via cli

Bug Fixes
~~~~~~~~~
* Allow IPv6 addresses SSH connection validation
* Fixed nested var issue
* Fixed duplicate resource name issue

Version 2.2.0 (2021-12-11)
--------------------------

Features
~~~~~~~~
* From this release, users are able to define remote_workspace in sdf file and use remote scenario

Enhancements
~~~~~~~~~~~~
* Make env variables available during Orchestrate and execute stage of Teflo run 
* Added __hash__ and __eq__ for Teflo Resource class

Bug Fixes
~~~~~~~~~
* Fixed notification to display passed and failed tasks for the entire scenario_graph 
* Fixed "for running You have to provide a valid scenario file. fails with 'skip-fail' KeyError" 


Version 2.1.0 (2021-11-05)
--------------------------

Documentation
~~~~~~~~~~~~~
* Modified quickstart page and flowchart for teflo

Enhancements
~~~~~~~~~~~~
* Make the data folder and results folder available to users in the form of environment variables 
* Added support usage of variables in the variables files in message notification templating
* Add skip failures ability during the graph run 
* Allow iterate_method from cli 
* Added check for installing ansible roles when running ansible playbooks under resource_check method 

Bug Fixes
~~~~~~~~~
* Fixed syntax warnings in CI
* Fix same file error 
* Fixed test result summary does not take into account error test case elements 
* Fixed the ansible nested var issue 
* Fix issues of jinja templating in include


Version 2.0.0 (2021-08-02)
--------------------------

Features
~~~~~~~~
* Recursive include of child scenarios is supported with scenario graph implementation
* Replaced scenario_streams with the newly added scenario graph
* teflo show -s sdf_file.yml --show-graph added, users can see the whole scenario graph structure
* Added term color to display log messages red(for errors) and green for other information
* Added support for selecting the scenario execution order __by_level__ and __by_depth__ using the *included_sdf_iterate_method* parameter in teflo.cfg

Enhancements
~~~~~~~~~~~~
* Redesigned teflo execution pipeline
* Redesigned the cleanup logic for scenarios
* Redesigned the validate logic for scenarios
* Redesigned the results generation
* Redesigned the inventory generation(output inventory stays the same, the logic behind the scene changed)
* Added typing for many functions(e.x *def func(param:list=[]):->str*)
* Added tostring,path,pullpath,inventory methods to scenario class

Documentation
~~~~~~~~~~~~~
* Added explanation about how to use scenario graph
* Added explanation about how *include* works with scenario graph

Version 1.2.5 (2021-11-05)
--------------------------

Enhancements
~~~~~~~~~~~~
* Enabled ci for version 1.2.x

Bug Fixes
~~~~~~~~~
* Fix for: custom resource_check does not honor the ansible_galaxy_options
* Fixed the ansible nested var issue with ansible_facts


Version 1.2.4 (2021-09-23)
--------------------------

Enhancements
~~~~~~~~~~~~
* beaker provisioner total attempts to an integer data type 
* add space to beaker warning 
* Allow users to set ansible verbosity using ansible environment variable 

Bug Fixes
~~~~~~~~~
* invalid inventory generated when groups contains the machine name \
* Report task fails when executes attribute is used and No asset is present 

Version 1.2.3 (2021-08-02)
--------------------------

Features
~~~~~~~~~~~~
* Add the var-file declared by user as an extra_vars in the ansible orchestrate and execute task
* teflo_rppreproc_plugin to support RPV5 instances

Enhancements
~~~~~~~~~~~~
* support --vars-data w/show command
* Added support bkr's ks-append(s) option in beaker-client plugin

Bug Fixes
~~~~~~~~~
* Added a generic exception handling during ssh to hosts
* Added fix for resource ordering issue in results.yml
* update import_results list when is not None
* Using variable files with variables as list/dict causes an exception

Documentation
~~~~~~~~~~~~~
* Correction in documentation to point to fixed gh_pages
* Added release cadence to Contribution.rst
* Added workaround(use of shell script) to allow make docs-wiki work correctly using makefile

Version 1.2.2 (2021-07-16)
--------------------------

Features
~~~~~~~~~~~~
* Added teflo init command (It will generate a genralized teflo workspace for you with examples)
* Added openstack instance metadata field for os_libcloud_plugin

Version 1.2.1 (2021-06-28)
--------------------------

Features
~~~~~~~~~~~~
* Introduced teflo_notify_service_plugin, users can use this plugin to send out messages to many platforms now

Enhancements
~~~~~~~~~~~~
* Added new default location for the usage of variables, you can now put varfile in default locations without specifying the with --vars-data
* Added nested recursive variable support, now the users can use variable inside a variable in your variable file
* Added ability to pass multiple files to the extra_vars module
* Create root users ssh directory for beaker provisioner when non existing
* Added teflo_notify_service_plugin, terraform-plugin and webhook-notification-plugin to setup.py extra require, users can do something like 'pip install teflo[teflo_notify_service_plugin]' now

Bug Fixes
~~~~~~~~~
* Fixed Ansible version bug

Documentation
~~~~~~~~~~~~~
* Updated compatibility matrix
* Updated some installation guide for some plugins
* Update teflos package classifiers

Version 1.2.0 (2021-05-10)
--------------------------

Features
~~~~~~~~~~~~
* Introduced teflo_terraform_plugin, users can use terraform during provision phase now

Enhancements
~~~~~~~~~~~~
* Use pyssh over paramiko library

Bug Fixes
~~~~~~~~~
* Hosts are not correctly resolved when groups are mentioned in the orchestrate task 
* Change the copyright license to 2021
* Fix the ansible stderr issue

Documentation
~~~~~~~~~~~~~
* Modified compatibility matrix
* removed jenkins folder
* Added example in execute.rst

Version 1.1.0 (2021-03-29)
--------------------------

Enhancements
~~~~~~~~~~~~
* Improved error messaging for syntax errors in SDF
* Allow jinja templating within teflo.cfg
* Allow multiple --vars-data arguments
* Removed backward compatibility support for using name field under orchestrate block as script/playbook path
* Removed backward compatibility support for using ansible_script as a boolean
* Removed backward compatibility support to remove role attribute from assets, and use only groups

Bug Fixes
~~~~~~~~~
* Modified ansible-base version in setup.py
* Fixed issue during generation inentory for static host with no groups attribute
* Fixed issue where Teflo was improperly exiting with a return code of 0 when the
  scenario descriptor file was invalid

Documentation
~~~~~~~~~~~~~
* Added more details and diagram on the teflo readme page
* Corrected the vars-data info page
* Use github pages for teflo plugins

Version 1.0.1 (2021-02-10)
--------------------------

Enhancements
~~~~~~~~~~~~
* Update teflo config code to not make defaults section mandatory
* For Openstack, display instance IDs
* Alter error message to not contain the words "fail" and "success" simultaneously
* The openstack lincloud schema needs two additional keys project_id and project_domain_id

Bug Fixes
~~~~~~~~~
* asset delete fails when using native provisioner (os libcloud) without provider attribute

Documentation
~~~~~~~~~~~~~
* Updated provision and examples docs to remove provider key and update examples
* Updated contribution page to add plugin template info

Version 1.0.0 (2021-01-07)
--------------------------

This is the first version of Teflo project (formerly known as Carbon)
