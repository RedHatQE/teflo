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
