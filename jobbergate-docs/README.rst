.. figure:: https://github.com/omnivector-solutions/jobbergate/blob/main/jobbergate-docs/src/images/logo.png
   :alt: Logo
   :align: center
   :width: 80px

   An Omnivector Solutions initiative

===========================
 Jobbergatge Documentation
===========================

This repository contains the source for the Jobbergate Documentation page.

It is built using [sphinx](https://www.sphinx-doc.org/en/master/) to render the source into
a static website.


Build the Docs
==============

To build the documentation static site, run the following command::

    $ make docs


Other Commands
==============

To lint the python files in the ``src`` directory, run::

    $ make lint


To clean up build artifacts, run::

    $ make clean
