Development
===========

If you are looking to get involved improving ``factur-x``, this
guide will help you get started quickly.

Development Guide
-----------------

1. Fork the `main repository <https://github.com/invoice-x/factur-x>`_. Click
on the 'Fork' button near the top of the page. This creates a copy of the code
under your account on the GitHub server.

2. Clone this copy to your local disk: 

::

    $ git clone https://github.com/invoice-x/factur-x
    $ cd factur-x

3. Create a branch to hold your changes and start making changes. Don't work
on ``master`` branch

::

    $ git checkout -b my_enhancement

4. Send Pull Request to ``master`` branch of this repository

Organization
------------

Major folders in the ``facturx`` package and their purpose:

-  ``flavors``: Has all the necessary resources of different flavors (Factur-x,
   Zugferd, UBL) and related code. ``xml_flavors.py`` detects the flavor of PDF
   invoice and gets relevant information based on the flavor. ``fields.yml``
   mentions all the fields that can be edited or viewed using facturx package.
    - ``factur-x``: Resources for Factur-X standard (xml, xmp, xsd)
    - ``zugferd``: Resources for Zugferd standard (xml, xmp, xsd)
    - ``standard_code``: Has standard ISO codes of currency and countries.

Testing
-------

Every new feature should have a test to make sure it still works after modifications done by you or someone else in the future.

To run tests using the current Python version: python -m unittest discover