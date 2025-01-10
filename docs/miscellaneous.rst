=============
Miscellaneous
=============

Activating staging ACME servers
===============================

During development it is not advised to generate certificates against production ACME servers,
as one could reach easily the weekly limit of Let's Encrypt and could not generate certificates for a certain period
of time. Staging ACME servers do not have this limit.

To use them, set the parameter ``acme.staging`` to ``true`` in your DNSroboCert YAML configuration file.

You will need to wipe content of /etc/letsencrypt volume before container re-creation when enabling or disabling
staging. Otherwise accounts and/or certificates may be in conflict between their staging and production versions.

Executing the DNSroboCert docker in a specific timezone
=======================================================

The default timezone is UTC.
You can set a local timezone in the docker `adferrand/dnsrobocert` by populating the ``TIMEZONE`` environment variable.
In this case, automated renewal will be done in this timezone, and logs will use the local date.

Migration from docker-letsencrypt-dns
=====================================

In this section we will discuss about how to migrate from ``adferrand/letsencrypt-dns`` to ``adferrand/dnsrobocert``.

Indeed DNSroboCert started as a pure Docker implementation named ``adferrand/letsencrypt-dns``. It was coded in bash,
and was using both environment variables and a file named ``domains.conf`` for its configuration. ``domains.conf`` was
holding the list of certificates to create and renew, and also the ``autorestart`` and ``autocmd`` features for each
certificate. On the other hand, environment variables were configuring the DNS provider to use, the specific options
for Let's Encrypt (account email address, staging servers) and some custom operations on the certificate assets
(like specific users and permissions).

DNSroboCert supports all these features, improves them, and stores its configuration in one structured central file,
located by default at ``/etc/dnsrobocert/config.yml``. As said by DNSroboCert in the logs, usage of the old environment
variables and the ``domains.conf`` file is deprecated, and **you should move as soon as possible to the** ``config.yml``
**file**. You should also use ``adferrand/dnsrobocert`` instead of ``adferrand/letsencrypt-dns`` starting from now.

If you followed the link displayed in logs from ``adferrand/letsencrypt-dns``, then this section is for you:
your instance of ``letsencrypt-dns`` has been upgraded to DNSroboCert, and you should migrate
to ``adferrand/dnsrobocert``.

Let's see this migration in details now.

Tool-assisted migration
-----------------------

Writing configuration files is boring. Do you agree? If so, you will be pleased to know that DNSroboCert handles
this migration for you. Indeed if you start an ``adferrand/dnsrobocert`` instance with the legacy configuration
(environment variables + ``domains.conf``), DNSroboCert will automatically pick them and generate the new configuration
file dynamically.

Its location is `/etc/dnsrobocert/config-generated.yml`. It contains the necessary configuration to make DNSroboCert
behave **exactly** like your ``adferrand/docker-letsencrypt-dns`` instance before.

Here are the steps to achieve the migration.

1. Pull the latest version of ``adferrand/docker-letsencrypt-dns`` and ``adferrand/dnsrobocert``:

.. code-block:: console

    docker pull adferrand/docker-letsencrypt-dns
    docker pull adferrand/docker-dnsrobocert

2. Restart your up-to-date instance of ``adferrand/docker-letsencrypt-dns`` appropriately with ``docker``
   or ``docker-compose`` to ensure the new configuration file has been generated:

3. Extract this file from the docker into your host machine (assuming your docker is named ``letsencrypt-dns``):

.. code-block:: console

    mkdir -p /etc/dnsrobocert
    docker cp letsencrypt-dns:/etc/dnsrobocert/config-generated.yml /etc/dnsrobocert/config.yml

4. Restart your Docker container with the new configuration file mounted at the right place:

   * With docker command line, add the following flag:

    .. code-block:: console

        --volume /etc/dnsrobocert/config.yml:/etc/dnsrobocert/config.yml

   * Or with docker-compose, add the mount directive in your ``docker-compose.yml``

    .. code-block:: yaml

        volumes:
        - /etc/dnsrobocert/config.yml:/etc/dnsrobocert/config.yml

**DNSroboCert will automatically pick the new configuration file.**

5. Once you confirmed that everything is working as before, you can restart the Docker without the environment
   variables and ``domains.conf`` mount. Please take this occasion to change the image name from
   ``adferrand/letsencrypt-dns`` to ``adferrand/dnsrobocert``. For instance:

.. code-block:: console

    docker run \
        --name dnsrobocert \
        --volume /var/docker-data/letsencrypt:/etc/letsencrypt \
        --volume /etc/dnsrobocert/config.yml:/etc/dnsrobocert/config.yml \
        adferrand/dnsrobocert

.. note::

    Docker image ``adferrand/letsencrypt-dns`` is deprecated and is replaced by ``adferrand/dnsrobocert``.

Manual migration
----------------

If you want to go berserk, you can migrate yourself by writing the new ``config.yml`` file to fit your needs, following
the documentation of the `User guide`_ and `Configuration reference`_.

Once done, you can follow the previous section to restart your Docker container.

Former configuration of ``adferrand/letsencrypt-dns``
-----------------------------------------------------

If needed, the former configuration for ``adferrand/letsencrypt-dns`` is available on GiHub_.

What is new?
------------

At this point, you may ask yourself what you gain by migrating from ``adferrand/letsencrypt-dns``
to ``adferrand/dnsrobocert``.

Well, thanks to this migration a lot of new features are planned, since this is a complete refactoring of the tool into
a proper programming language, Python. Basically it becames a real program that I name DNSroboCert, with code
quality control and good extensibility to add all the features the community asks for.

You can check in particular the `Project V3 specifications`_ that drove this migration and gives key points for
the incoming features.

But beyond promises you will get immediate advantages that I already implemented in DNSroboCert:

* **the big one**: you can now define multiple DNS providers in one single instance of DNSroboCert
* the custom deploy scripts and PFX exports are defined per certificate
* force renew can be set for specific certificates

Stay tuned for the new features!


.. _User guide: https://adferrand.github.io/dnsrobocert/user_guide.html
.. _Configuration reference: https://adferrand.github.io/dnsrobocert/configuration_reference.html
.. _Project V3 specifications: https://github.com/adferrand/docker-letsencrypt-dns/wiki/Project-V3-specifications,-aka-DNSroboCert
.. _GiHub: https://github.com/adferrand/dnsrobocert/blob/legacy/README.md
