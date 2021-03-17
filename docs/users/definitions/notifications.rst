Notification
============

Overview
--------

Teflo's notification section declares what messages are to be sent
and to whom when triggered. The current notification mechanism
is :ref:`email<email_notify>`.

First lets go over the basic structure that defines a notification task.

.. literalinclude:: ../../../examples/docs-usage/notification.yml
    :lines: 1-9

The above code snippet is the minimal structure that is required to create a
notification task within teflo. This task is translated into a teflo notification
object which is part of the teflo compound. You can learn more about this at
the `architecture <../../developers/architecture.html>`_ page. Please see the table below to
understand the key/values defined.

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required
        - Default

    *   - name
        - The name of the notification to define
        - String
        - Yes
        - n/a

    *   - description
        - A description of what the notification is trying to accomplish
        - String
        - No
        - n/a

    *   - notifier
        - The notifier to use to send notifications when triggered
          above
        - String
        - Yes
        - email-notifier

    *   - on_start
        - trigger to send a notification when a task is going to be executed
        - Boolean
        - No
        - False

    *   - on_success
        - trigger to send a notification when a task has executed successfully
        - Boolean
        - No
        - True

    *   - on_failure
        - trigger to send a notification when a task has executed unsuccessfully
        - Boolean
        - No
        - True

    *   - on_demand
        - disable automatic trigger of the notification. Must be manually triggered
        - Boolean
        - No
        - False

    *   - on_tasks
        - Filter for which tasks should trigger a notification
        - List
        - No
        - All Tasks (Validate, Provision, Orchestrate, Execute, Report, Cleanup)

.. _notify_triggers:

Triggers
--------

By default, Teflo implicitly triggers on both **on_success** and **on_failure** for all completed
task types. If you would like to set it for either/or, you can explicitly set either parameter to **true**.

If you would like to have teflo trigger notifications before the start of a task rather than after,
you can set **on_start** to **true**. The **on_start** option is mutually exclusive to
**on_success**/**on_failure**.

If you would like to have teflo not trigger notifications automatically and you would like to control
when to trigger notifications in your workflow, you can set the **on_demand** flag to true.

If you would like to filter so that only certain tasks trigger notifications, you can set **on_tasks**
to a list of any combination of supported teflo tasks. This does not apply to **on_demand**.

There are further capabilities to controling the triggering of any notifications from the command line.

For example, if you have defined different notifications in your scenario with different triggers but
are interested in triggering certain ones for a particular run, you can specify which ones to skip
using the **--skip-notify** option

.. code-block:: bash

    teflo run -s scenario.yml -w . -t provision --skip-notify notification_a --skip-notify notification_b

If you would like to temporarily disable triggering notifications for the entire scenario for a particular
run without permanently setting them to **on_demand**. You can use the **--no-notify** option

.. code-block:: bash

    teflo run -s scenario.yml -w . -t execute -t report --no-notify


.. _email_notify:

Sending Email Notifications
---------------------------

Credentials/Configure
+++++++++++++++++++++

To configure the email notification, you will need to have your SMTP
configuration in your teflo.cfg file, see `SMTP Configuration
<credentials.html#email-notification>`_ for more details.

Email
+++++

The following shows all the possible keys for defining an email
notification using the **email-notifier** notifier:

.. code-block:: yaml

    ---
    notifications:
      - name: <name>
        notifier: <notifier>
        to: <list_of_values>
        from: <from>
        cc: <list_of_values>
        subject: <subject>
        attachments: <list_of_values>
        message_body: <multiline value>
        message_template: <template_path>

.. list-table::
    :widths: auto
    :header-rows: 1

    *   - Key
        - Description
        - Type
        - Required

    *   - to
        - A list of email addresses that this notification should be sent to.
        - List
        - True

    *   - from
        - The email address the notification should be from.
        - String
        - True

    *   - cc
        - The list of email addresses that you want to send teflo copies to.
        - List
        - False

    *   - subject
        - The subject of the message that should be included.
        - String
        - False

    *   - attachments
        - List of attachments to include when the message is sent.
        - List
        - False

    *   - message_body
        - The text body of the message to include overriding Teflo's default message template.
        - String
        - False

    *   - message_template
        - A relative path to a text email body template in Teflo's workspace that should be used.
          It overrides Teflo's default message template.
        - String
        - False


Message Content
---------------

Teflo has a default messaging template that is sent when no **message_body** or **message_template**
parameter is used. Teflo uses some internal data about the tasks performed by the scenario.
Below is the list of data being rendered into the message

 * overall status of the Scenario execution
 * The list of Teflo tasks that passed and/or failed
 * The list of artifacts that were collected after test execution if any
 * The import result urls of any test artifacts that were imported into a reporting system

Teflo makes its scenario object avaialble along with the environmental variables to user when
designing their own messaging template. The key for teflo's scenario object is **scenario**

Examples
--------

Let's go into some examples of you can define your notification resources


Example 1
+++++++++

You want to trigger a notification on all successful tasks using the default template

.. literalinclude:: ../../../examples/docs-usage/notification.yml
    :lines: 1-9


Example 2
+++++++++

You want to trigger a notification before the start of all tasks using a messaging template

.. literalinclude:: ../../../examples/docs-usage/notification.yml
    :lines: 12-23

Teflo's scenario data could be used to format the template email_templ.txt as shown in the examples below:

a.

.. code-block:: bash

   Hello All,

   This is a Teflo Notification.

   Teflo scenario, {{ scenario.name }}, has provisioned  the asset:

   {{ scenario.assets[0].name }}

b.

.. code-block:: bash

   Hello All,

   This is a Teflo Notification for Execute task.

    {% if scenario.executes %}
        {% for execute in scenario.executes %}
        Execute task name: {{ execute.name }}
                {% if execute.artifact_locations %}
        Collected the following artifacts:
                {% for file in execute.artifact_locations %}
                - {{ file }}
                {% endfor %}
            {% endif %}
            {% if execute.testrun_results %}

        These are the test results of the scenario:

          Total Tests: {{ execute.testrun_results.aggregate_testrun_results.total_tests }}
          Passed Tests: {{ execute.testrun_results.aggregate_testrun_results.passed_tests }}
          Failed Tests: {{ execute.testrun_results.aggregate_testrun_results.failed_tests }}
          Skipped Tests: {{ execute.testrun_results.aggregate_testrun_results.skipped_tests }}

            {% endif %}
        {% endfor %}
    {% else %}
     No execute tasks were run
    {% endif %}

This is how the email sent using above template  will read:

.. code-block:: yaml

  Hello All,

   This is a Teflo Notification for Execute task.

        Execute task name: Test running playbook
        Collected the following artifacts:
                - artifacts/localhost/rp_preproc_qmzls.log
                - artifacts/localhost/junit_example_5_orig.xml

        These are the test results of the scenario:

          Total Tests: 6
          Passed Tests: 4
          Failed Tests: 2
          Skipped Tests: 0

        Execute task name: Execute2
        Collected the following artifacts:
                - artifacts/localhost/rp_preproc_qmzls.log
                - artifacts/localhost/junit_example_5_orig.xml

        These are the test results of the scenario:

          Total Tests: 6
          Passed Tests: 4
          Failed Tests: 2
          Skipped Tests: 0



Example 3
+++++++++

You want to trigger a notification regardless on failures of the Validate and Provision task
but you want to include a multiline string in the descriptor file.

.. literalinclude:: ../../../examples/docs-usage/notification.yml
    :lines: 25-44


Example 4
+++++++++

You want to trigger a notification regardless only on failures of all tasks
using the default template message but you want to include a file as an attachment.

.. literalinclude:: ../../../examples/docs-usage/notification.yml
    :lines: 46-56


Example 5
+++++++++

You don't want a notification to trigger automatically.

.. literalinclude:: ../../../examples/docs-usage/notification.yml
    :lines: 58-66

Example 6
+++++++++

Using custom template and using teflo's data for formatting

.. literalinclude:: ../../../examples/docs-usage/notification.yml
    :lines: 58-66


Sending Chat Notifications
---------------------------
Teflo_webhooks_notification_plugin allows users to send chat notification
during and/or post teflo run. To get more information about this plugin ,on how to install and use it
please visit `teflo_webhooks_notification_plugin
<https://redhatqe.github.io/teflo_webhooks_notification_plugin/index.html>`_
