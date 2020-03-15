=======================
Configuration reference
=======================

.. contents:: Table of Contents
   :local:

DNSroboCert configuration is defined in a central file, usually located at ``/etc/dnsrobocert/config.yml``.
Its location is defined by the ``-c`` flag when running DNSroboCert locally with the CLI, or with the
``CONFIG_PATH`` environment variable with Docker.

File format
===========

The configuration file must be a valid YAML and must conform to the JSON schema defined for DNSroboCert.
One can find the raw content of this schema on GitHub_. DNSroboCert will validate the file each time it is changed,
and output the errors (missing properties, wrong value type) if any.

The basic structure is the following:

.. code-block:: yaml

    draft: false
    acme: {}
    profiles: []
    certificates: []

``draft`` Section
=================

If the draft mode is enabled, DNSroboCert will validate dynamically the configuration file, but will not
reconfigure itself with it and will not proceed to any further action. This is useful to make wide modifications
in the file without DNSroboCert taking them into account immediately, then apply all modifications altogether
by disabling the draft mode.

Example (enable the draft mode):

.. code-block:: yaml

    draft: true

``acme`` Section
================

This section contains all general configuration parameters for Certbot (the underlying ACME client that
generates the certificates) and how these certificates are stored locally.

``email_account``
    * The email account used to create an account against Let's Encrypt
    * *type*: ``string``
    * *default*: ``null`` (no registration is done, and so no certificate is issued if an account does not exist yet)

``staging``
    * If ``true``, Let's Encrypt staging servers will be used (useful for testing purpose)
    * *type*: ``boolean``
    * *default*: ``false``

``api_version``
    * The ACME protocol version to use (deprecated ``1`` or current ``2``)
    * *type*: ``integer``
    * *default*: ``2``

``directory_url``
    * The ACME CA server to use
    * *type*: ``string`` representing a valid URL
    * *default*: ``null`` (ACME CA server URL is determined using ``staging`` and ``api_version`` values)

``certs_permissions``
    * An object describing the files and directories permissions to apply on generated certificates
    * *type*: ``object``
    * *default*: ``null`` (default permissions are applied: certificates are owned by the user/group running DNSroboCert,
      and are only accessible by this user/group)

    ``files_mode``:
    * The permissions to apply to files, defined in POSIX octal notation
    * *type*: ``integer`` defined in octal notation (eg. ``0o644``)
    * *default*: ``0o640``

    ``dirs_mode``:
    * The permissions to apply to directories, defined in POSIX octal notation
    * *type*: ``integer`` defined in octal notation (eg. ``0o644``)
    * *default*: ``0o750``

    ``user``:
    * The user that should be owner of the certificates
    * *type*: ``string``
    * *default*: ``null`` (user running DNSroboCert will be owner of the certificates)

    ``group``:
    * The group that should group owner of the certificates
    * *type*: ``string``
    * *default*: ``null`` (group running DNSroboCert will group owner of the certificates)

``crontab_renew``:
    * A cron pattern defining the frequency for certificates renewal check
    * *type*: ``string`` representing a valid cron pattern
    * *default*: ``12 01,13 * * *`` (twice a day)

.. _GitHub: https://raw.githubusercontent.com/adferrand/docker-letsencrypt-dns/dnsrobocert/src/dnsrobocert/schema.yml