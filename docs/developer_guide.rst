===============
Developer guide
===============

Thanks a lot for your involvement. You will find here some tips to quickly setup a suitable development environment,
and useful tools to ensure code quality in the project.

General design principles
=========================

DNSroboCert is coded entirely in Python, and uses features available starting with Python 3.11+.

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

Architecture overview
=====================

DNSroboCert runs several processes. This is important to keep in mind when working on the code, in particular for
logging and for the configuration, that is loaded again in each process.

.. code-block:: text

    dnsrobocert (main process)
    |-- watches the configuration file, validates it, and writes a runtime copy
    |-- a background thread triggers the renewal twice a day
    `-- for each action, starts a Certbot subprocess (register, certonly, revoke)
        `-- Certbot calls hooks, each one being a new ``dnsrobocert.core.hooks`` process
            |-- auth: creates the TXT entry with Lexicon, then waits for its propagation
            |-- cleanup: deletes the TXT entry with Lexicon
            `-- deploy: PFX export, permissions, autorestart, autocmd, deploy hook

The main modules are:

* ``main``: command line, configuration watch loop and one-shot mode,
* ``config``: loading, environment variables injection, validation (``schema.yml`` and business checks),
* ``certbot``: builds the Certbot command lines, and revokes the certificates removed from the configuration,
* ``hooks`` and ``challenge``: the Certbot hooks and the DNS operations. They run inside Certbot, so they
  write on the standard output to be captured by Certbot instead of using the logging of the main process,
* ``background``: the renewal scheduling,
* ``legacy``: migration of the former ``domains.conf`` configuration,
* ``utils``: subprocess execution, permissions, and snap helpers.

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
  The integration test runs DNSroboCert against Pebble_, a test ACME server downloaded on the first execution.
* The code is formatted, linted and import-sorted using Ruff_, and statically checked using MyPy_.

Please ensure that your code is compliant with this guideline before submitting a PR:

1. Ensure that tests are passing:

.. code-block:: console

    uv run pytest test

.. warning::

    On Windows you must run the tests from an account with administrative privileges to make them pass.

2. Ensure that linting and static type checking are passing:

.. code-block:: console

    uv run ruff check src test
    uv run mypy src

3. Reformat your code:

.. code-block:: console

    uv run ruff format src test

All these checks (and the tests with a minimal coverage of 85%) are also available through Tox_, as run
by the continuous integration:

.. code-block:: console

    uvx --with tox-uv tox

You can also run Ruff automatically before each commit using pre-commit_:

.. code-block:: console

    uvx pre-commit install

Changelog
=========

The changelog is built with Towncrier_ from small news fragments, instead of being edited directly (which
caused merge conflicts between pull requests). Each pull request that is visible for users adds a file in the
``newsfragments`` folder, named ``<pull request number>.<type>.md`` where the type is ``added``, ``changed``,
``fixed``, ``security`` or ``removed``. For instance:

.. code-block:: console

    uv run towncrier create 1234.fixed.md

The file contains a single sentence describing the change for the users. If there is no pull request number,
use an orphan fragment like ``+short-description.added.md``. You can preview the result with:

.. code-block:: console

    uv run towncrier build --draft --version X.Y.Z

Pull requests with no impact for users (tests, CI, internal refactoring) do not need a fragment: add the
``skip-changelog`` label to the pull request to skip the check done by the continuous integration.

When a release is created with ``utils/create_release.py``, the fragments are assembled into ``CHANGELOG.md`` and
removed.

Submitting a PR
===============

Well, you know what to do ;)

.. _Pytest: https://docs.pytest.org/en/latest/
.. _Pebble: https://github.com/letsencrypt/pebble
.. _Ruff: https://docs.astral.sh/ruff/
.. _MyPy: http://mypy-lang.org/
.. _Tox: https://tox.wiki/
.. _Towncrier: https://towncrier.readthedocs.io/
.. _pre-commit: https://pre-commit.com/
