Carbon Examples
===============

The primary purpose of this repository is to provide you with working
`teflo <https://code.engineering.redhat.com/gerrit/gitweb?p=teflo.git>`_
examples. The examples are light weight and simple. The goal here is for you
to use these as a getting started with teflo. Once you have a understanding
on how teflo works using them, you can easily expand upon them to build your
own.

The repository contains different directories which make up different tasks
of teflo. Below is the main structure for this project and details about
each one.

.. code-block:: none

    ├── configuration
    ├── e2e
    ├── execute
    ├── lib
    ├── orchestrate
    ├── provision
    ├── report
    └── resource_check


configuration
-------------

This directory contains examples on how you setup your teflo configuration
file. Please see the `configuration <configuration>`_ directory for
more details.

e2e (end to end)
----------------

This directory contains a complete scenario descriptor file (SDF) showing all
teflo tasks configured. Please see the `e2e <e2e>`_ directory for
more details.

execute
-------

This directory contains examples on how you can use teflos execute task.
Please see the `execute <execute>`_ directory for more details.

lib
---

This directory can be ignored. It contains helper functions used throughout
the examples.

orchestrate
-----------

This directory contains examples on how you can use teflos orchestrate task.
Please see the `orchestrate <orchestrate>`_ directory for more details.

provision
---------

This directory contains examples on how you can use teflos provision task.
Please see the `provision <provision>`_ directory for more details.

report
------

This directory contains examples on how you can use teflos report task.
Please see the `report <report>`_ directory for more details.

resource_check
--------------

This directory contains examples on how you can use teflos resource check
functionality. Please see the `resource check <resource_check>`_ directory
for more details.