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

*Section example:*

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

    ``files_mode``
        * The permissions to apply to files, defined in POSIX octal notation
        * *type*: ``integer`` defined in octal notation (eg. ``0644``)
        * *default*: ``0640``

    ``dirs_mode``
        * The permissions to apply to directories, defined in POSIX octal notation
        * *type*: ``integer`` defined in octal notation (eg. ``0644``)
        * *default*: ``0750``

    ``user``
        * The user that should be owner of the certificates
        * *type*: ``string``
        * *default*: ``null`` (user running DNSroboCert will be owner of the certificates)

    ``group``
        * The group that should group owner of the certificates
        * *type*: ``string``
        * *default*: ``null`` (group running DNSroboCert will group owner of the certificates)

``crontab_renew``
    * A cron pattern defining the frequency for certificates renewal check
    * *type*: ``string`` representing a valid cron pattern
    * *default*: ``12 01,13 * * *`` (twice a day)

*Section example:*

.. code-block:: yaml

    acme
      email_account: my.email@example.net
      staging: false
      api_version: 2
      # If directory_url is set, values of staging and api_version are ignored
      directory_url: https://example.net/dir
      certs_permissions:
        files_mode: 0644
        dirs_mode: 0755
        user: nobody
        group: nogroup
      crontab_renew: 12 01,13 * * *

``profiles`` Section
====================

This section holds *an array of profiles*. Each profile is an `object` that describes the
credentials and specific configuration to apply to a DNS provider supported by Lexicon in order
to fulfill a DNS-01 challenge.

Each profile is referenced by its ``name``, which can be used in one or more certificates in the
``certificates`` section. Multiple profiles can be defined for the same DNS provider. However, each profile ``name``
must be unique.

``profile`` properties
----------------------

``name``
    * The name of the profile, used to reference this profile in the ``certificates`` section.
    * *type*: ``string``
    * **mandatory property**

``provider``
    * Name of the DNS provider supported by Lexicon
    * *type*: ``string``
    * **mandatory property**

``provider_options``
    * An `object` defining all properties to use for the DNS provider defined for this profile
    * *type*: ``object``
    * *default*: ``null``

    Each property that should be added in ``provider_option`` depends on the actual provider used.
    You can check all properties available for each provider in the
    `Lexicon Providers configuration reference`_ page.
    As an example for Aliyun it will be:

    .. code-block:: yaml

        provider_options:
          auth_key_id: MY_KEY_ID
          auth_secret: MY_SECRET

``sleep_time``
    * Time in seconds to wait after the TXT entries are inserted into the DNS zone to perform the DNS-01 challenge
      of a certificate
    * *type*: ``integer``
    * *default*: ``30``

``max_checks``
    * Maximum number of checks to verify that the TXT entries have been properly inserted into the DNS zone before
      performing the DNS-01 challenge of a certificate. DNSroboCert will wait for the amount of time defined in
      ``sleep_time`` between each check. Set to ``0`` to disable these checks.
    * *type*: integer
    * *default*: ``0`` (no check is done)

``delegated_subdomain``
    * If the zone that should contain the TXT entries for the DNS-01 challenges is not a SLD (Second-Level Domain), for
      instance because a SLD delegated your subdomain to a specific zone, this options tells to DNSroboCert that your
      subdomain is actually the zone to modify, and not the SLD.

      For instance: the zone is ``sub.example.net``, certificate is for ``www.sub.example.net``, then
      ``delegated_subdomain`` should be equal to ``sub.example.net``.
    * *type*: ``string``
    * *default*: ``null`` (there is no subdomain delegation)

``certificates`` Section
========================






.. _GitHub: https://raw.githubusercontent.com/adferrand/docker-letsencrypt-dns/dnsrobocert/src/dnsrobocert/schema.yml
.. _Lexicon Providers configuration reference: https://dnsrobocert.readthedocs.io/en/dnsrobocert/lexicon_providers_config.html