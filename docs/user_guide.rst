==========
User guide
==========

Preparation
===========

In order to work properly, DNSroboCert requires a configuration file, which is written in YAML. To avoid
any problem, you should create it before starting DNSroboCert (the file can be empty at this point).

The path of this file is configurable. We will assume in this user guide that it is ``/etc/dnsrobocert/config.yml``.

On Linux for instance, run:

.. code-block:: console

    mkdir /etc/dnsrobocert
    touch /etc/dnsrobocert/config.yml

DNSroboCert will store the certificates in a specific folder. Here also a good idea is to create it
before starting DNSroboCert.

The path of this folder is configurable. We will assume in this user guide that it is ``/etc/letsencrypt``.

On Linux for instance, run:

.. code-block:: console

    mkdir -p /etc/letsencrypt

Installation
============

DNSroboCert can be installed in two ways:

1) On the host using a python package manager
2) As a Docker container

Installation on the host
------------------------

.. note::

    * DNSroboCert requires Python 3.6+.
    * It can be installed on Linux, Mac OS or Windows.
    * For Linux and Mac OS, running as a privileged user (eg. root) is recommended.
    * For Windows, running as a privileged user (eg. Administrator) is required.

The recommended way is to use Pipx_, a tool that extends Pip_ and is specifically designed to
install a Python program in a isolated and dedicated environment.

You need Python 3.6+ installed on your machine.

Install `pipx` using `pip`:

.. code-block:: console

    python3 -m pip install pipx
    python3 -m pipx ensurepath

Then install DNSroboCert on the desired version (eg. ``3.0.0``):

.. code-block:: console

    python3 -m pipx install dnsrobocert==3.0.0

At this point DNSroboCert is installed and available in the ``PATH``. You can display the inline help using:

.. code-block:: console

    dnsrobocert --help

And run DNSroboCert with:

.. code-block:: console

    dnsrobocert -c /etc/dnsrobocert/config.yml -d /etc/letsencrypt

DNSroboCert will continue to run in the foreground. To stop it, press CTRL+C.

Running as a Docker container
-----------------------------

An up-to-date Docker image is available in DockerHub_. In order to persist DNSroboCert configuration and
the generated certificates, you should mount its configuration and the dedicated folder for certificates
from the host into the container.

* For the configuration file, expected path is ``/etc/dnsrobocert/config.yml``
* For the certificates folder, expected path is ``/etc/letsencrypt``

.. note::

    Both paths are configurable in the container through the environment variables ``CONFIG_PATH`` and
    ``CERTS_PATH`` respectively.

Finally you can run this typical command for the desired version (eg. 3.0.0):

.. code-block:: console

    docker run --rm --name dnsrobocert
        --volume /etc/dnsrobocert/config.yml:/etc/dnsrobocert/config.yml
        --volume /etc/letsencrypt:/etc/letsencrypt
        adferrand/dnsrobocert:3.0.0

The Docker container will continue to run in the foreground. To stop it, press CTRL+C.

.. note::

    DNSroboCert also work on Podman

Configuration
=============

This guide focuses only on the bare minimum to make use of DNSroboCert: create one or more certificates.
For an advanced configuration, in order to use more of DNSroboCert capabilities, please have a look to the
`Configuration reference`_.

Configuring DNSroboCert consists in writing its unique configuration file (we assume its location at
``/etc/dnsrobocert/config.yml``). In particular 3 things need to be set up, and correspond to the 3
main sections of the configuration file:

* in ``acme``, we define the Let's Encrypt account that will be used to issue certificates
* in ``profiles``, we describe the DNS credentials and the DNS provider associated to the DNS zone to fulfill
  DNS-01 challenges
* and finally in ``certificates``, we list the certificates that DNSroboCert will issue and regularly renew.

We can write the configuration file in draft mode: in this case, DNSroboCert will validate the configuration
file, but will not do anything with it. This is quite suitable during the initial configuration phase.

So let's start with a ``config.yml`` whose content is:

.. code-block:: yaml

    draft: true

Configuring ``acme`` section
----------------------------

Basically we need to decide which email will be associated to the Let's Encrypt account. This email is used
by Let's Encrypt administrators to broadcast important messages, and particularly when your certificates
are about to expire. This email is put in the `acme.email_account` property.

.. note::

    During DNSroboCert configuration, you will certainly want to test things without targeting the Let's Encrypt
    production servers, since these servers have certificate rate creation limits. This can be done by setting
    the property ``acme.staging`` to ``true``: in this case Let's Encrypt staging servers will be used.

At this point, our ``config.yml`` looks like this:

.. code-block:: yaml

    draft: true
    acme:
      email_account: john.doe@example.net
      staging: true

Configuring ``profiles`` section
--------------------------------

It is time to set the credentials and other specific configuration entries for the DNS provider that is
holding the DNS zone for the domains you want to include in your certificate. This constitute a so-called
"profile" in DNSroboCert.

Please have a look to the `Lexicon Providers configuration reference`_ page to see what are the DNS providers
supported by DNSroboCert (through the Lexicon tool), and what are the relevant configuration parameters
for your provider.

We need to create a profile, and add it in the list holded by the ``profiles`` property. This profile needs:

* a name, on the property ``profiles[].name``
* the Lexicon provider, as defined in the `Lexicon Providers configuration reference`_ page,
  on the property ``profiles[].provider``
* the provider options described in the aforementioned page for your provider, exposed as an object in the
  ``profiles[].provider_options`` where each key is an option, and the value is the value option.

Typically a profile looks like the following:

.. code-block:: yaml

    profiles:
    - name: my_profile
      provider: a_provider
      provider_options:
        one_option: one_value
        another_option: another_value

We assume here that the ``henet`` provider will be used. It requires two options: ``auth_username`` and
``auth_password``.

Given the format for ``profiles``, our existing ``config.yml`` and the use of ``henet`` provider, our
configuration file will look like this now:

.. code-block:: yaml

    draft: true
    acme:
      email_account: john.doe@example.net
      staging: true
    profiles:
    - name: henet_profile
      provider: henet
      provider_options:
        auth_username: USER
        auth_password: PASSWD

.. note::

    You can declare multiple profiles to use different providers and/or the same provider with
    different credentials.

Configuring ``certificates`` section
------------------------------------

Everything is ready to get the certificates. What you want as certificates is defined in the ``certificates``
section. It contains a list of each certificate you want. The bare minimum content for a certificate is:

* the profile name to use for DNS-01 challenges, set in the ``certificates[].profile`` property
* the list of domains to add in the certificate, to give as a list in the ``certificates[].domains`` property

Typically a certificate entry will looks like:

.. code-block:: yaml

    certificates:
    - domains:
      - one.example.net
      - two.example.net
      profile: my_profile

We assume here that the DNS zone is ``example.net``, and two certificates need to be created:

* a regular certificate for ``mail.example.net`` and ``ldap.example.net``
* a wildcard certificate for ``*.example.net`` and ``example.net``

We will use the ``henet_profile`` configured previously.

Given this situation, we add the certificate configurations to our ``config.yml``.
The configuration file looks like this now:

.. code-block:: yaml

    draft: true
    acme:
      email_account: john.doe@example.net
      staging: true
    profiles:
    - name: henet_profile
      provider: henet
      provider_options:
        auth_username: USER
        auth_password: PASSWD
    certificates:
    - domains:
      - mail.example.net
      - ldap.example.net
      profile: henet_profile
    - domains:
      - "*.example.net"
      - example.net
      profile: henet_profile

Running DNSroboCert
===================

Our configuration is now ready: we can disable the draft mode, by setting ``draft`` parameter to ``false``.
We continue to assume that the certificates will be generated in the ``/etc/letsencrypt`` folder.

If DNSroboCert is already started, it will immediately proceed to issue and retrieve the certificates. If not,
see the Installation_ section to start DNSroboCert.

After a minute, your certificates will be issued (have a look to the log output to check that). Your certificates
are available in the ``/etc/letsencrypt`` folder and can be used. The layout of ``/etc/letsencrypt`` follows
the `Certbot layout convention`_. So given our example here, you will find:

* the regular certificate for ``mail.example.net`` and ``ldap.example.net`` at ``/etc/letsencrypt/live/mail.example.net``
* the wildcard certificate for ``*.example.net`` and ``example.net`` at ``/etc/letsencrypt/live/example.net``

.. note::

    If you used the Let's Encrypt staging servers to configure DNSroboCert, you can now go back to th
    production servers to get real certificates: in ``config.yaml``, change ``acme.staging`` value to
    ``false``. DNSroboCert will proceed immediately to replace the testing certificates by real certificates.

Dynamic configuration
---------------------

DNSroboCert check constantly for modifications in its configuration file. You can live edit it: DNSroboCert
will proceed to issue new certificates as soon as you configuration file is written to the disk.

Automated renewal
-----------------

Let's Encrypt certificates last only 3 months, and need to be renewed regularly. DNSroboCert includes this
functionality: while it is running it will regularly (twice a day) check for certificate renewal, and proceed
to all renewals if needed (this happens typically one month before the expiration of the current certificate).

Daemonize DNSroboCert
---------------------

Because of this regular renewal requirement, DNSroboCert should run constantly on your machine as a daemon.
The tool does not provide a specific daemon technology: the CLI will just constantly run on the foreground,
and reacts properly to the relevant exit signal codes like ``SIGTERM``. From that it is your reponsability
to daemonize DNSroboCert.

Here are some relevant ways depending on the context.

Systemd unit
````````````

If you run DNSroboCert directly on the host (eg. you followed the `Installation on the host`_ section), one
simple way is to define a systemd unit, and configure your Systemd to run DNSroboCert as a daemon at startup.

Docker-Compose
``````````````

If you run DNSroboCert in a Docker container (eg. you followed the `Running as a Docker container`_ section),
then Docker-Compose is a standard way to configure a Docker and ensure that is runs all the time as a daemon.

Create the following ``docker-compose.yml`` file:

.. code-block:: yaml

    version: '2'
    services:
      dnsrobocert:
        image: adferrand/dnsrobocert
        container_name: dnsrobocert
        volumes:
        - /etc/letsencrypt:/etc/letsencrypt
        - /etc/dnsrobocert:/etc/dnsrobocert
        restart: always

Then run it:

.. code-block:: console

    docker-compose up -d

At this point, your Docker container of DNSroboCert will be started and the Docker daemon will ensure it
continues to run upon your machine restart.

Run DNSroboCert in "one-shot" mode
----------------------------------

If the approach of DNSroboCert process running constantly does not fit your needs, you can also use the "one-shot" mode.

In this mode, DNSroboCert will process only once the provided configuration upon execution, then:

* create or update certificates if needed
* renew expired certificates
* delete certificates that do not match the current configuration

At the end it will exit immediately without setting up any config watch or automated renewal process:
it will be up to you to execute DNSroboCert on a regular basis (preferably twice a day as recommended by Let's Encrypt).

To use the "one-shot" mode, simply set the `--one-shot` flag to the command line. For instance:

.. code-block:: console

    dnsrobocert --config /path/to/config.yml --directory /path/to/letsencrypt --one-shot


.. _Pipx: https://github.com/pipxproject/pipx
.. _Pip: https://docs.python.org/fr/3.6/installing/index.html
.. _DockerHub: https://hub.docker.com/r/adferrand/dnsrobocert
.. _Configuration reference: https://adferrand.github.io/dnsrobocert/configuration_reference.html
.. _Lexicon Providers configuration reference: https://adferrand.github.io/dnsrobocert/providers_options.html#supported-providers
.. _Certbot layout convention: https://certbot.eff.org/docs/using.html#where-are-my-certificates
