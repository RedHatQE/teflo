Report
======

Overview
--------

Teflo's report section declares which test artifacts collected during execution
are to be imported into a Report & Analysis system. The input for artifact import
will depend on the destination system.

First, let's go over the basic structure that defines a Report resource.

.. code-block:: yaml

    ---
    report:
      - name: <name>
        description: <description>
        executes: <execute>
        importer: <importer>

.. important::
        The Reporting systems currently supported are Polarion and Report Portal. These systems
        can be accessed using teflo's plugins **teflo_polarion_plugin** and **teflo_rppreproc_plugin**
        These plugins are only available for internal RedHat use at this time. Users can put
        in tickets `here <https://github.com/RedHatQE/teflo/issues>`_ for new plugin development
        or contribute towards this effort.
        Please refer `Developers Guide <../../developers/development.html#how-to-write-an-plugin-for-teflo>`__
        on how to contribute towards the plugin.


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

More information on artifact_locations key refer :ref:`Finding Locations <finding_locations>`
