lib_shell
=========

|Pypi Status| |license| |maintenance|

|Build Status| |Codecov Status| |Better Code| |code climate| |snyk security|

.. |license| image:: https://img.shields.io/github/license/webcomics/pywine.svg
   :target: http://en.wikipedia.org/wiki/MIT_License
.. |maintenance| image:: https://img.shields.io/maintenance/yes/2019.svg
.. |Build Status| image:: https://travis-ci.org/bitranox/lib_shell.svg?branch=master
   :target: https://travis-ci.org/bitranox/lib_shell
.. for the pypi status link note the dashes, not the underscore !
.. |Pypi Status| image:: https://badge.fury.io/py/lib-shell.svg
   :target: https://badge.fury.io/py/lib_shell
.. |Codecov Status| image:: https://codecov.io/gh/bitranox/lib_shell/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/bitranox/lib_shell
.. |Better Code| image:: https://bettercodehub.com/edge/badge/bitranox/lib_shell?branch=master
   :target: https://bettercodehub.com/results/bitranox/lib_shell
.. |snyk security| image:: https://snyk.io/test/github/bitranox/lib_shell/badge.svg
   :target: https://snyk.io/test/github/bitranox/lib_shell
.. |code climate| image:: https://api.codeclimate.com/v1/badges/325cf1bd771fb210b2db/maintainability
   :target: https://codeclimate.com/github/bitranox/lib_shell/maintainability
   :alt: Maintainability

some convenience functions for calling the world

supports python 3.7 and possibly other dialects.

`100% code coverage <https://codecov.io/gh/bitranox/lib_shell>`_, mypy static type checking, tested under `Linux, OsX, Windows and Wine <https://travis-ci.org/bitranox/lib_shell>`_, automatic daily builds  and monitoring

----

- `Installation and Upgrade`_
- `Basic Usage`_
- `Requirements`_
- `Acknowledgements`_
- `Contribute`_
- `Report Issues <https://github.com/bitranox/lib_shell/blob/master/ISSUE_TEMPLATE.md>`_
- `Pull Request <https://github.com/bitranox/lib_shell/blob/master/PULL_REQUEST_TEMPLATE.md>`_
- `Code of Conduct <https://github.com/bitranox/lib_shell/blob/master/CODE_OF_CONDUCT.md>`_
- `License`_
- `Changelog`_

----

Installation and Upgrade
------------------------

From source code:

.. code-block:: bash

    # normal install
    python setup.py install
    # test without installing
    python setup.py test

via pip latest Release:

.. code-block:: bash

    # latest Release from pypi
    pip install lib_shell

    # test without installing
    pip install lib_shell --install-option test

via pip latest Development Version:

.. code-block:: bash

    # upgrade all dependencies regardless of version number (PREFERRED)
    pip install --upgrade https://github.com/bitranox/lib_shell/archive/master.zip --upgrade-strategy eager
    # normal install
    pip install --upgrade https://github.com/bitranox/lib_shell/archive/master.zip
    # test without installing
    pip install https://github.com/bitranox/lib_shell/archive/master.zip --install-option test

via requirements.txt:

.. code-block:: bash

    # Insert following line in Your requirements.txt:
    # for the latest Release:
    lib_shell
    # for the latest Development Version :
    https://github.com/bitranox/lib_shell/archive/master.zip

    # to install and upgrade all modules mentioned in requirements.txt:
    pip install --upgrade -r /<path>/requirements.txt

via python:

.. code-block:: python

    # for the latest Release
    python -m pip install upgrade lib_shell

    # for the latest Development Version
    python -m pip install upgrade https://github.com/bitranox/lib_shell/archive/master.zip

Basic Usage
-----------

TBA

Requirements
------------
following modules will be automatically installed :

.. code-block:: bash

    git+https://github.com/bitranox/lib_detect_encoding.git
    git+https://github.com/bitranox/lib_list.git
    git+https://github.com/bitranox/lib_log_utils.git
    git+https://github.com/bitranox/lib_parameter.git
    git+https://github.com/bitranox/lib_regexp.git

Acknowledgements
----------------

- special thanks to "uncle bob" Robert C. Martin, especially for his books on "clean code" and "clean architecture"

Contribute
----------

I would love for you to fork and send me pull request for this project.
- `please Contribute <https://github.com/bitranox/lib_shell/blob/master/CONTRIBUTING.md>`_

License
-------

This software is licensed under the `MIT license <http://en.wikipedia.org/wiki/MIT_License>`_

---

Changelog
=========

0.0.1
-----
2019-07-22: Initial public release

