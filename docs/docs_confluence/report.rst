Report
======

Overview
--------

Teflo's report section declares which test artifacts collected during execution 
are to be imported into a Report & Analysis system. The input for artifact import
will depend on the destination system. The Reporting systems currently supported are:
:ref:`Polarion<polarion_importing>` and :ref:`Report Portal<report_portal_importing>`

.. attention::
   To be able to use Polarion and Report Portal with teflo, teflo_polarion_plugin and teflo_rppreproc_plugin will
   have to be installed in your workspace prior to running any scenarios. Please see below for installation process

Report resource
---------------

Let us go over the basic structure that defines a Report resource.

.. code-block:: yaml

    ---
    report:
      - name: <name>
        description: <description>
        executes: <execute>
        importer: <importer>

.. attention::
   Also see :ref:`Teflo Matrix for Plugins <cbn_plugin_matrix_1>` to find the correct plugin versions supported by
   Teflo

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - name
        - The name of the test artifact to import. This can be a
          full name of an artifact, a shell pattern matching string, or
          a string using Teflo's data-passthru mechanism
        - String
        - True

    *   - description
        - A description of the artifact being imported
        - String
        - False

    *   - executes
        - The name of the execute block that collected
          the artifact.
        - List
        - False

    *   - importer
        - The name of the importer to perform the import process.
        - String
        - True


Executes
--------
Defining a Teflo execute resource is optional. Teflo uses the execute resource
for two reasons:

 * It uses the **artifact_locations**  key as a quick way to check if the artifact
   being requested was collected and where to find it.

 * It uses the Asset resources assigned to the Execute to perform the internal
   templating if a data-passthru string is being used in the name key
   as search criteria.

.. _finding_artifacts:

Finding the right artifacts
---------------------------

As noted in the table, the driving input will be the name key.
The name can be a string defining the exact file/folder name,
a shell matching pattern, or a teflo data-passthru pattern.
Depending on the pattern used it will narrow or widen the search
scope of the search. How teflo performs the search is by the following

 * Check if an execute resource was defined with the **execute**
   and then check **artifact_locations** key is defined for
   the execute in the execute section.

 * If there is an **execute** key and the artifact is listed as
   an item that was collected in the **artifact_locations** key, teflo
   will immediately validate the location.

 * If no **execute** key is defined, or an execute with no **artifact_location**
   key is used, or the artifacts is not shown as one of the items contained in the
   the artifact_location key, or the item location in the artifact_location key is
   no longer valid, it proceeds to walk the *data_folder/.results* folder.

 * If no artifacts are found after walking the *data_folder/.results*, teflo will abort the
   import process.

 * If artifacts are found, the list of artifacts will be processed and imported into
   the respective reporting system.

To stop finding duplicate artifacts during the import
-----------------------------------------------------

The driving factor is the name field of the report block. You can narrow and
restrict the search based on the shell pattern specified.

For example, if you specify an artifact like *SampleTest.xml* but the artifact
has been collected numerous times before its possible a list of the same file in
different locations within the teflo *<data_folder>* are going to be found.
You can restrict the search to a particular instance by doing something like
*test_driver/SampleTest.xml* with test_driver being a directory. Telling teflo
to look in that particular directory for the artifact.

For more information on the different patterns that can be used in the name field
refer to some of the examples for importing to Polarion and Report Portal below.

.. _polarion_importing:

Importing artifacts into Polarion
---------------------------------

Teflo_Polarion_Plugin
+++++++++++++++++++++

This plugin allows teflo to send test results to Polarion tool. Users need to install this
plugin separately in the workspace. You can read more about the plugin in the
`repo link <https://gitlab.cee.redhat.com/ccit/teflo/plugins/teflo_polarion_plugin.git>`__


Installation
++++++++++++

.. code-block:: bash

    # for ansible modules requiring selinux, you will need to enable system site packages
    $ virtualenv --system-site-packages polarion
    $ source polarion/bin/activate
    (polarion) $ pip install teflo_polarion_plugin@git+https://gitlab.cee.redhat.com/ccit/teflo/plugins/teflo_polarion_plugin.git@<tagged_branch>


Credentials
+++++++++++

To authenticate with Polarion, you will need to have your Polarion credentials
in your teflo.cfg file.

The following table is a list of required keys for
your credential section in your teflo.cfg file.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - polarion_url
        - The URL you use to log into Polarion. Do not append the xunit-queue
          to the end of it.
        - String
        - True

    *   - username
        - The username that has privileges to your Polarion project. It is
          recommended to have an automation user created with admin privileges
        - String
        - True

    *   - password
        - The password of your user to the Polarion project.
        - String
        - True

.. code-block:: bash

  [credentials:polarion-creds]
  polarion_url=<polarion_url>
  username=<username>
  password=<password>

The following is an example of a resource in the scenario descriptor file
that references this credential:

.. literalinclude:: ../../examples/docs-usage/report.yml
    :lines: 1-8


Polarion Artifact
+++++++++++++++++

The following shows all the possible keys for defining the artifact import
for the Polarion xUnit Importer:

.. code-block:: yaml

    ---
    report:
      - name: <name>
        description: <description>
        executes: <execute name>
        importer: polarion
        credential: polarion-creds
        project_id: <project_id>
        testsuite_properties: <ts_properties>
        testcase_properties: <tc_properties>
        testcase_csv_file: <path_to_csv>

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - credential
        - The name of the credentials to use to import the artifact
          into polarion. This is the one defined in the credentials 
          section of the teflo config file.
        - String
        - True

    *   - project_id
        - The Polarion project id
        - String
        - False (True for xUnit conversion)

    *   - testsuite_properties
        - These are the specific Polarion test suite
          properties to apply to the xUnit file before 
          importing. Any polarion-custom property can be used as well.
          format: <polarion-ts-property>: <value> 
        - Dictionary
        - False

    *   - testcase_properties
        - These are the specific testcases in the xUnit file and 
          associated Polarion test cases properties to apply to 
          the xUnit file before importing. Any polarion-custom 
          property can be used as well. format:
          <test_classname>.<name_attribute>: 
          <polarion-tc-property>: <value>
        - Dictionary
        - False

    *   - testcase_csv_file
        - An export csv file from Polarion that contains testcase
          work item fields - id, title, and testcaseid. Using this
          will allow teflo to dynamically assign the testcases
          the proper polarion-testcase-id based on the specified lookup
          method specified in testsuite_properties
        - String
        - False

.. attention::
   It's important to note when project_id, testsuite_properties, testcase_properties
   and/or testcase_csv_file are specified the importer will take those parameters and
   attempt to do the xUnit conversion. When supplying these provider
   parameters a minimum required parameter for xUnit conversion is project_id.

   If project_id, testsuite_properties, testcase_properties, and testcase_csv_file are
   not specified teflo will not perform the xUnit conversion. It will proceed with
   importing the artifact and monitoring for import status.

xUnit Test Case Properties
++++++++++++++++++++++++++
For the xUnit conversion process there are two options for tagging test cases with the
appropriate id, **testcase_properties** or **testcase_csv_file**. Teflo has opted to follow
the general guidelines set forth by Polarion.

testcase_csv_file
+++++++++++++++++
For a dynamic approach a user can export a csv file from Polarion containing the *id*, *title*,
and *testcaseid* fields. This file is used in conjunction with a lookup-method. The *testcaseid*
field is enabled by default in Polarion but is not available in the Form UI until it has been
explicitly enabled by a project administrator. Once enabled the field should contain the name
of the xUnit test case in the format of **<testclassname>.<name attribute>**.  For more
information about the *testcaseid* field refer to the following `Polarion
documentation <https://mojo.redhat.com/docs/DOC-1073077#jive_content_id_Polarion_Configuration>`_

If no lookup method is specified in the testsuite_properties the Polarion xUnit Importer will
default to looking for test cases using its id. Teflo will parse the *testcaseid* from the csv file
and see if it is in the xUnit file. When found it will add the **polarion-testcase-id** property value
to the *id*. The same applies if the lookup method was explicitly set to *id*.

If the lookup method is set to *custom*. Teflo will parse the *testcaseid* from the csv file and see if
it is in the xUnitfile. When found it will add the **polarion-testcase-id** property value to the
*testcaseid*.

If the lookup method is set to *name*. There is no need to specify this parameter since the Polarion
xUnit Importer will search for the test case by the *title* and a **polarion-testcase-id** is not required.
In order for Polarion to successfully find the test case the *title* has to be in the
**<testclassname>.<name attribute>** format.

testcase_properties
+++++++++++++++++++
This a static approach to defining what tags are to be applied to the xUnit test case. This
is the recommended approach when a test case needs to have iterations added before the import.
This is also the recommended method if Polarion projects have not enabled and are not using the
testcaseid field for automated test cases being imported.

 
Teflo Polarion Configuration
+++++++++++++++++++++++++++++

In the teflo configuration file, you can set some options related to Polarion.
These values should be set in the **[importer:polarion]** section of the
config file.  The following are the settings.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Default

    *   - save_file
        - configuration option to save a copy of the xUnit file
          before performing the xUnit conversion.
        - By default this is set to True to make a copy.

    *   - wait_timeout
        - configuration option to set how long teflo should 
          wait for the import process to complete.
        - By default, teflo will set the timeout to 15 minutes.
          This value can be overwritten but must be specified in
          seconds, i.e. 15 minutes = 900 seconds.
   
    *   - poll_interval
        - configuration option to set how often teflo should check 
          with the Polarion xUnit queue for import process status. 
        - By default, teflo will poll the xUnit queue every 1 minute.
          This value can be overwritten but must be specified in seconds
          i.e. 1 minute = 60 seconds.

    *   - concurrent_processing
        - configuration option on whether the polarion library
          should perform each activity (xunit translation/
          initial import/waiting for import completion)concurrently
          or serially.
        - By default this is set to True to perform the different
          actions concurrently.

.. _report_examples:

Examples
++++++++

Lets dive into a couple different examples. These examples show use of both provider key and no provider key

Example 1
+++++++++

You have an xUnit artifact that has already gone through conversion as part of 
the test process and needs to be imported into Polarion.

.. literalinclude:: ../../examples/docs-usage/report.yml
    :lines: 1-7

Example 2
+++++++++

You have an xUnit artifact that needs just some testsuite properties applied,
where the lookup method is set to name. Then the artifact is imported afterwards.

.. literalinclude:: ../../examples/docs-usage/report.yml
    :lines: 9-21

Example 3
+++++++++

You have an xUnit artifact that needs a full set of properties applied and  
imported afterwards. No lookup method is supplied because the id for the
test case has been explicitly defined and an iteration.

.. literalinclude:: ../../examples/docs-usage/report.yml
    :lines: 23-40

Example 4
+++++++++

You have an xUnit artifact that was named using Teflo's data pass-through in 
the execute phase that needs to have some testsuite properties applied to it and
imported afterwards.

.. literalinclude:: ../../examples/docs-usage/report.yml
    :lines: 41-52

Example 5
+++++++++

You have a set of xUnit files that have already gone through conversion 
during the test process and just need to be bulk imported.

.. literalinclude:: ../../examples/docs-usage/report.yml
    :lines: 54-60

Example 6
+++++++++

You have a set of xUnit files that have the same name
that have already gone through conversion during the test process 
but you only need one from a specific host in teflo's artifact directory.

.. literalinclude:: ../../examples/docs-usage/report.yml
    :lines: 62-69

Example 7
+++++++++

You have an xUnit file that needs to be properly tagged with testsuite
properties and the testcases should dynamically tagged with their polarion
id using the contents of the csv file. Then imported afterwards.

.. literalinclude:: ../../examples/docs-usage/report.yml
   :lines: 71-83


.. _report_portal_importing:

Importing artifacts into Report Portal
--------------------------------------

Teflo_Rppreproc_Plugin
++++++++++++++++++++++

This plugin allows teflo to send test results to Report Portal tool. You can read more about the plugin in the
`repo link <https://gitlab.cee.redhat.com/ccit/teflo/plugins/teflo_rppreproc_plugin.git>`__

Installation
++++++++++++

.. code-block:: bash

    # for ansible modules requiring selinux, you will need to enable system site packages
    $ virtualenv --system-site-packages reportportal
    $ source reportportal/bin/activate
    (reportportal) $ pip install teflo_rppreproc_plugin@git+https://gitlab.cee.redhat.com/ccit/teflo/plugins/teflo_rppreproc_plugin.git@<tagged_branch>

Credentials
+++++++++++

To authenticate with Report Portal, you will need to have your Report Portal credentials
in your teflo.cfg file

The following table is a list of required and optional keys for
your credential section in your teflo.cfg file.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - create_creds
        - This is to determine if teflo should use the credentials provided in the
          teflo.cfg file or use the ones that are given in the json config file
          user supplies in the report portal provider parameters
          If set to **True** teflo will make use the optional report portal credentials
          in this table to connect to the report portal instance

          If set to **False** teflo will assume these credentials are being provided by
          users in the report portal config json file, which can be given as a report
          portal provider parameter. For how to configure Report Portal json file refer
          `here <https://docs.engineering.redhat.com/pages/viewpage.action?pageId=81876674#CCITReportPortalUser's
          Guide[EADraft]-ConfigurationFileDescription>`_
        - String
        - True

    *   - rp_url
        - The URL to the report portal instance
        - String
        - False

    *   - api_token
        - api token from the  report portal instance for a user account
        - String
        - False

    *   - service_url
        - This param is to use the rp_preproc service for sending
          the launch to Report Portal. It takes the value of the URL to the RP
          PreProc REST API service OR **false** in case you do not want to use
          the rp_preproc service option
        - String
        - False

.. code-block:: bash

  [credentials:reportportal-creds]
  create_creds=<True/False>
  rp_url=<report_portal_url / False>
  api_token=<token>
  service_url=<service_url>

The following is an example of a resource in the scenario descriptor file
that references this credential:

.. literalinclude:: ../../examples/docs-usage/report.yml
          :lines: 85-91

CCIT Report Portal Client
+++++++++++++++++++++++++

Teflo uses CCIT Report Portal client to import artifacts to the Report Portal instance.
To know more about Report Portal Client, please refer
`here <https://docs.engineering.redhat.com/pages/viewpage.action?pageId=81876674>`__

.. note::

   The report portal client is only for internal RED HAT usage and not available publicly

Teflo Report Portal Configuration
+++++++++++++++++++++++++++++++++

The following shows all the possible keys for defining the artifact import
for the Report Portal Importer:

Without Provider:

.. code-block:: yaml

    ---
    report:
      - name: <name>
        description: <description>
        executes: <execute name>
        importer: reportportal
        credential: reportportal-creds
        rp_project: <project_name>
        launch_name: <launch_name>
        launch_description: <launch_description>
        simple_xml: <to just import XML file directly>
        auto_dashboard: <create dashboard>
        merge_launches: <merge multiple launches into single true/false>
        tags:
        - <tag1>
        - <tag2>
        json_path: <relative path for report portal config file>

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - credential
        - The name of the credentials to use to import the artifact
          into report portal. This is the one defined in the credentials 
          section of the teflo config file.
        - String
        - True

    *   - rp_project
        - The Report Portal project name
        - String
        - True

    *   - launch_name
        - The name of the launch(import session)
        - String
        - True

    *   - launch_description
        - The description of the launch
        - String
        - False

    *   - tags
        - Tags set for each launch
        - list
        - False

    *   - merge_launches
        - report portal client sends one xml file as one launch. To send multiple
          xml files as a single launch this option is used. If set to false there
          we can see multiple launches and multiple launch ids will be provided.
          (Default: True)
        - Boolean
        - False

    *   - auto_dashboard
        - report portal client creates dashboard and populate it with a basic 
          table widget filtered on the launch name specified. It returns a
          dashboard url. (Default: True)
        - Boolean
        - False

    *   - simple_xml
        - bypass the pre-processor and just import the XML file directly. Attachments,
          and other benefits of parsing into individual API calls, will not be available.
          (Default: False)
        - Boolean
        - False

    *   - json_path
        - relative path for json file for the report portal configuration. When this option
          is used, the rest of the provider params are ignored. User can set all the above
          params in a json config file and provide ts path here.
        - String
        - False

.. NOTE::
   At this time Report Portal Client can create a dashboard for the launches using a single widget 
   and one filter (name of the launch).

Report Portal Config File
+++++++++++++++++++++++++

Uers can provide a custom config json file using the key *json_path* under the provider 
section of the report section in the SDF.

Please refer report portal config section in the Report Portal client documentation to understand
more about the config json file
`here <https://docs.engineering.redhat.com/pages/viewpage.action?
pageId=81876674#CCITReportPortalUser'sGuide-rp_preproc>`__

Example for json config:

.. code-block:: json

   {
    "rp_preproc": {
        "service_url": "http://rp-preproc-downstream-ccit-reportportal.cloud.paas.psi.redhat.com/",
        "payload_dir": ""

    },
    "reportportal": {
        "host_url": "https://rp-ea.cloud.paas.psi.redhat.com",
        "api_token": "000-000-000-000",
        "project": "teflo_project",
        "merge_launches": false,
        "auto_dashboard": true,
        "simple_xml": false,
        "launch": {
            "name": "teflo1",
            "description": "teflo_launch_desc",
            "tags":[
                "tag1",
                "tag2"
            ]

        }
    }
   }

If config json file is not provided by the user then Teflo creates the file using the
different report portal provider parameters in the report section of the SDF as **<uuid>.json** and stores
it under a folder named **rp_config_files**. Here uuid is a unique id generated for every report portal block/run in
teflo. User has the option to save this Teflo created file for future use. By default the file gets deleted after
every run.

In the teflo configuration file, user can set the following parameter in the **[importer:reportportal]**
section to save the Teflo created reportportal config file.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Default

    *   - save_json_config
        - configuration option to save a copy of the reportportal config json file
          created by Teflo
        - By default this is set to False to delete the file after every run


.. NOTE:: 
   Even if the user provided config json file has a payload directory given, it gets overwritten 
   by the one created/validated by Teflo


**Example 1**

In the following example, *json_path* parameter is not provided, Teflo uses the reportportal provider's 
remaining params and creates the json file **<uuid>.json** in a directory **rp_config_files** under the workspace
directory and uses it to pass paylaod to the Report Portal Client

.. literalinclude:: ../../examples/docs-usage/report.yml
   :lines: 256-271

**Example 2**

In the following example, json_path is provided. Here Teflo uses the user provided config file to send
the payload to the Report Portal Client

.. literalinclude:: ../../examples/docs-usage/report.yml
   :lines: 273-282


**Example 3**

In the following example both json_path and other params are given. Here since json_path is provided
it will be used as the config file to send the payload, the other params are ignored

.. literalinclude:: ../../examples/docs-usage/report.yml
   :lines: 284-300

Setting up payload directory for Report Portal Client
+++++++++++++++++++++++++++++++++++++++++++++++++++++

The CCIT Report Portal client requires artifacts to be presented in a specific payload directory structure.
It needs all the xml files(test cases) to be in a folder named **results** and any specific test case related
logs to be in a folder named **attachments**. The results folder is required. The attachments folder is optional,
it is needed only when related items like pictures/logs need to be sent to Report Portal. The attachments folder
also has a set of rules regarding sub-folder structure. Please refer to the Report Portal Payload Directory structure
`Payload Structure
<https://docs.engineering.redhat.com/pages/viewpage.action?pageId=81876674#CCITReportPortalUser'sGuide-payloaddirectory>`_


There are a few ways Teflo can handle this:

**Structured**

 * User can pre create the artifacts payload directory as per the Report Portal requirement in the
   execute stage and collect it as part of the *artifacts*

 * User can pre-create the artifacts payload directory as per the Report Portal client requirements
   but they aren't collected as part of *artifacts*. Probably as an intermediate step between the
   Execute and Report phases, the user would have to place the payload directory under the *.results* folder.
   User can then put the name of the payload folder in the *artifact_location* key or let Teflo
   walk the data_folder directories.

**Unstructured**

 * User doesn't pre-create the payload directory and collects the unstructured artifacts they need in the execute
   phase using *artifacts*. Teflo will filter the list of artifacts for any .xml files,
   then create a new folder under Teflo's data folder named **<data folder>/rp_paylods/<uuid>/results**, and place
   the xml files in this directory. Here uuid is a unique id generated for every report portal block/run in
   teflo

 * User doesn't pre-create the payload directory and doesn't collect the unstructured artifacts in the execute
   phase using *artifacts*. Probably as an intermediate step between the Execute and Report phases.
   The user would have to place the artifacts under the teflo's *.results* folder. User can then put the name of the
   payload folder in the *artifact_location* key or let Teflo walk the data_folder directories.
   Teflo will filter the list of artifacts for any .xml files, then creates a new folder under Teflo's
   data folder named **<data folder>/rp_paylods/<uuid>/results**, and place the xml files in this directory.
   Here uuid is a unique id generated for every report portal block/run in
   teflo

Use Case 1
++++++++++

Using execute section to collect artifacts with correct structure and send them as payload to the Report Portal Client

In this use case the user needs to setup the execute section with an additional step to collect the artifacts and place
them in the required directory structure needed by the Report Portal Client. i.e all xmls under results folder and all 
logs related to the test cases under attachments folder.

In the example below, the execute stage is setup to collect artifacts from location /rp_examples/payload_eg in the required
structure. The report name in this case is a pattern payload/* to consider the payload_eg dir entirely as the payload
to be sent to the Report Portal Client

.. literalinclude:: ../../examples/docs-usage/report.yml
   :lines: 93-117

Use Case 2
++++++++++

Artifacts/payload to be sent is not collected using the execute section of Teflo and payload directory structure is 
as required by Report Portal client

In this usecase the artifacts/payload to be sent to Report Portal are not collected as a part of execute phase. 
Here the user can place the payload directory created separately under teflo’s *.results*  folder and use the key
*artifact_locations* under the execute section to let Teflo know to look in the .results folder for this payload 
directory. In this usecase the directory structure is as per requirement.

.. NOTE::
   Please refer :ref:`here<finding_locations>`  to know more about using artifact_locations key under execute section
   of Teflo's SDF


Teflo verifies that the given path has correct directory structure  and then passes that as the payload directory 
to the Report Portal client 

In the below example the payload_example_medium is a directory placed under *.results* folder and has the correct
directory structure of results and attachments folder under it. The name of the report used is payload_example/medium/*

.. literalinclude:: ../../examples/docs-usage/report.yml
   :lines: 119-145

Use Case 3
++++++++++

Artifacts are collected by the execute section of the Teflo SDF , but they are not stored in the correct directory 
structure as needed by the Report Portal client. 

In this case Teflo will create a separate directory named rp_payload under Teflo’s data folder. Here ONLY the 
xml files are copied from artifacts in execute phase  over to rp_payload/results. 

.. NOTE::
   In case attachments/logs were collected as part of artifacts they are ignored. At this time Teflo does not 
   support collecting additional logs and sending them as part of payload directory structure. To send the 
   additional logs as a part of payload please look at usecase 1 or 2 examples.

In the below example rp_examples/payload_uc3 is where artifacts are stored but not in correct format. Teflo looks through
this folder, copies all the xml files and puts them under .teflo/<data folder>/rp_payloads/<uuid>/results.

**.teflo/<data folder>/rp_payloads/<uuid>** is the payload directory path given to the Report Portal client

.. literalinclude:: ../../examples/docs-usage/report.yml
   :lines: 147-171

Use Case 4
++++++++++

Artifacts/payload to be sent are NOT collected using the execute section of teflo and payload directory structure 
is NOT as required  by Report Portal client

In this usecase the user can place the payload directory created separately under Teflo’s *.results*  folder
and can place the path of the payload directory under *artifact_locations* key of the execute section of the SDF.
Teflo will create a separate directory rp_payload as .teflo/<data folder>/rp_payload/results and since the
directory structure is NOT as required, will copy ONLY the xml files from payload directory which user has put
under *.results* folder. 

In the below example the payload_teflo is a directory placed under teflo’s  *.results* folder and does not have
the correct directory structure of results and attachments folder under it.Here teflo will create a separate 
directory rp_payloads if it is not already there and then create a folder with uuid as
.teflo/<data folder>/rp_payloads/<uuid>/results and copy all the xml files from .teflo/.results/payload_teflo/
The payload directory sent to report portal client will be **.teflo/.results/rp_payloads/uuid**

.. literalinclude:: ../../examples/docs-usage/report.yml
   :lines: 173-197

Use Case 5
++++++++++

Artifacts are collected by execute section (unstructured) of the SDF and there are other xml files
(seperate from artifacts) that are needed to be added to the payload

In this case the artifacts to be collected are put under the *artifact* key. The additional files to be added
to payload are placed under teflo’s *.results* folder and they are mentioned under the *artifact_locations* 
key

This case even is used when the artifacts and artifac_location files are unstructured. Teflo creates a directory
.teflo<data folder>rp_payload/results. It will then go through the paths in artifacts and artifact_locations and
collect all the xml files there. Any other files will be ignored.

The path for payload directory is **.teflo/<data folder>/rp_payloads/<uuid>**

In the below example the artifacts collected during execute phase are present under artifacts as
/home/teflo_develop/e2e-acceptance-tests/rp_examples/payload_example_medium and the other xml files not collected 
during execute are under artifact_locations and stored under Teflo's *.results* folder

.. literalinclude:: ../../examples/docs-usage/report.yml
   :lines: 199-229

Use Case 6
++++++++++

The execute stage keys, artifact or artifact_locations are not used to mention the payload,
but the xml files have been put under teflo’s .results folder

Here if the artifacts or artifact_locations are not populated, Teflo goes through teflo’s data folder
and teflo’s *.results* folder to find the artifacts matching the name provided in the report section's
name key.

If found, teflo creates a directory .teflo/<data folder>/rp_payloads/<uuid>/results and collects all the xml files
from the matching artifacts list . Any other files are ignored

The payload directory path given to the Report Portal client is  **.teflo/<data folder>/rp_payloads/uuid**

In the below example the  data folder directory and .results directory are walked and the pattern payload_example_medium/*
is  matched with files found in there. xml files are selected from the matched paths/files and added to the payload directory.

.. literalinclude:: ../../examples/docs-usage/report.yml
   :lines: 231-254
