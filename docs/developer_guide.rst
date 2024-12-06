===============
Developer guide
===============

Thanks a lot for your involvement. You will find here some tips to quickly setup a suitable development environment,
and useful tools to ensure code quality in the project.

General design principles
=========================

DNSroboCert is coded entirely in Python, and uses features available starting with Python 3.6+.

It sits on top of Certbot_ and Lexicon_. Here are the repartition of the roles:

* Certbot_ takes care of the actual certificate issuances and renewals against the ACME CA server, in a compliant
  and secured processing that respects the `RFC-8555`_ protocol,
* Lexicon_ provides the central interface to communicate with the DNS API providers, and inserts the required TXT
  entries for the DNS-01 challenges,
* DNSroboCert

  * holds and validates the central configuration for users,
  * couples Certbot_ and Lexicon_ through the auth/cleanup hook system of `Certbot's manual plugin`_,
    to issue/renew DNS-01 challenged based certificates,
  * orchestrates the post-deploy processing (``autocmd``, ``autorestart``, files rights...),
  * executes a a cron job to trigger regularly the `Certbot renewal process`_.

.. _Certbot: https://github.com/certbot
.. _RFC-8555: https://tools.ietf.org/html/rfc8555
.. _Lexicon: https://github.com/AnalogJ/lexicon
.. _Certbot's manual plugin: https://certbot.eff.org/docs/using.html#manual
.. _Certbot renewal process: https://certbot.eff.org/docs/using.html#renewing-certificates

Setting up a development environment
====================================

DNSroboCert uses UV_ to manage the development environment & dependencies, build the project, and push wheel/sdist to PyPI.

1. First, install UV_, following this guide: `UV installation`_.

2. Now UV should be available in your command line. Check that the following command is displaying UV version:

.. code-block:: console

    uv --version

3. Fork the upstream `GitHub project`_ and clone your fork locally:

.. code-block:: console

    git clone https://github.com/myfork/dnsrobocert.git

.. note::

    | A widely used development pattern in Python is to setup a virtual environment.
    | Python virtual environments allow to manage a dedicated and isolated Python runtime for a specific project.
    | It allows in particular to have a separated set of dependencies for the project that will not interfere with
      the OS Python packages installed globally.

4. Setup the virtual environment for DNSroboCert using UV:

.. code-block:: console

    cd dnsrobocert
    uv sync

5. Activate the virtual environment:

* For Linux/Mac OS X:

.. code-block:: console

    source .venv/bin/activate

* For Windows (using Powershell):

.. code-block:: console

    .\.venv\Scripts\activate

At this point, you are ready to develop on the project. You can run the CLI that will use the local source code:

.. code-block:: console

    dnsrobocert --help

.. _UV: https://docs.astral.sh/uv/
.. _UV installation: https://docs.astral.sh/uv/getting-started/installation/
.. _GitHub project: https://github.com/adferrand/docker-letsencrypt-dns

Code quality
============

The project DNSroboCert tries to follows the up-to-date recommended guideline in Python development:

* DNSroboCert logic is tested with a pyramidal approach (unit tests + integration tests) using Pytest_.
* The code is formatted using Black_ and Isort_ to keep as possible unified and standardized writing conventions.
* The code is linted with Flake8_ and statically checked using MyPy_.

Please ensure that your code is compliant with this guideline before submitting a PR:

1. Ensure that tests are passing:

.. code-block:: console

    pytest test

.. warning::

    On Windows you must run the tests from an account with administrative privileges to make them pass.

2. Ensure that linting and static type checking are passing:

.. code-block:: console

    flake8 src test utils
    mypy src

3. Reformat your code:

.. code-block:: console

    isort -rc src test utils
    black src test utils

Submitting a PR
===============

Well, you know what to do ;)

.. _Pytest: https://docs.pytest.org/en/latest/
.. _Black: https://github.com/psf/black
.. _Isort: https://pypi.org/project/isort/
.. _Flake8: https://flake8.pycqa.org/en/latest/
.. _MyPy: http://mypy-lang.org/
