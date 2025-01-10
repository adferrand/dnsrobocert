=======================
Configuration reference
=======================

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

.. code-block:: yaml

    draft: true

``acme`` Section
================

This section contains all general configuration parameters for Certbot (the underlying ACME client that
generates the certificates) and how these certificates are stored locally.

.. code-block:: yaml

    acme:
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

``email_account``
~~~~~~~~~~~~~~~~~
    * The email account used to create an account against Let's Encrypt
    * *type*: ``string``
    * *default*: ``null`` (no registration is done, and so no certificate is issued if an account does not exist yet)

``staging``
~~~~~~~~~~~
    * If ``true``, Let's Encrypt staging servers will be used (useful for testing purpose)
    * *type*: ``boolean``
    * *default*: ``false``

``api_version``
~~~~~~~~~~~~~~~
    * The ACME protocol version to use (deprecated ``1`` or current ``2``)
    * *type*: ``integer``
    * *default*: ``2``

``directory_url``
~~~~~~~~~~~~~~~~~
    * The ACME CA server to use
    * *type*: ``string`` representing a valid URL
    * *default*: ``null`` (ACME CA server URL is determined using ``staging`` and ``api_version`` values)

``certs_permissions``
~~~~~~~~~~~~~~~~~~~~~
    * An object describing the files and directories permissions to apply on generated certificates
    * *type*: ``object``
    * *default*: ``null`` (default permissions are applied: certificates are owned by the user/group running DNSroboCert,
      and are only accessible by this user/group)

    ``files_mode``
        * The permissions to apply to files, defined in POSIX octal notation
        * *type*: ``integer`` or ``string`` defined in octal notation (eg. ``0644`` or ``"0755"``)
        * *default*: ``0640``

    ``dirs_mode``
        * The permissions to apply to directories, defined in POSIX octal notation
        * *type*: ``integer`` or ``string`` defined in octal notation (eg. ``0755`` or ``"0755"``)
        * *default*: ``0750``

    ``user``
        * The user name or uid that should be owner of the certificates
        * *type*: ``integer`` (for a uid, eg. ``1000``) or ``string`` (for a user name, eg. ``"myuser"``)
        * *default*: ``null`` (user running DNSroboCert will be owner of the certificates)

    ``group``
        * The group name or gid that should group owner of the certificates
        * *type*: ``integer`` (for a gid, eg. ``1000``) or ``string`` (for a user name, eg. ``"mygroup"``)
        * *default*: ``null`` (group running DNSroboCert will group owner of the certificates)

``crontab_renew``
~~~~~~~~~~~~~~~~~
    * A cron pattern defining the frequency for certificates renewal check
    * *type*: ``string`` representing a valid cron pattern
    * *default*: ``12 01,13 * * *`` (twice a day)

``profiles`` Section
====================

This section holds *a list of profiles*. Each profile is an `object` that describes the
credentials and specific configuration to apply to a DNS provider supported by Lexicon in order
to fulfill a DNS-01 challenge.

Each profile is referenced by its ``name``, which can be used in one or more certificates in the
``certificates`` section. Multiple profiles can be defined for the same DNS provider. However, each profile
``name`` must be unique.

.. code-block:: yaml

    profiles:
      - name: my_profile1
        provider: digitalocean
        provider_options:
          auth_token: TOKEN
        sleep_time: 45
        max_checks: 5
      - name: my_profile2
        provider: henet
        provider_options:
          auth_username: USER
          auth_password: PASSWORD

``profile`` properties
----------------------

``name``
~~~~~~~~
    * The name of the profile, used to reference this profile in the ``certificates`` section.
    * *type*: ``string``
    * **mandatory property**

``provider``
~~~~~~~~~~~~
    * Name of the DNS provider supported by Lexicon
    * *type*: ``string``
    * **mandatory property**

``provider_options``
~~~~~~~~~~~~~~~~~~~~
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
~~~~~~~~~~~~~~
    * Time in seconds to wait after the TXT entries are inserted into the DNS zone to perform the DNS-01 challenge
      of a certificate
    * *type*: ``integer``
    * *default*: ``30``

``max_checks``
~~~~~~~~~~~~~~
    * Maximum number of checks to verify that the TXT entries have been properly inserted into the DNS zone before
      performing the DNS-01 challenge of a certificate. DNSroboCert will wait for the amount of time defined in
      ``sleep_time`` between each check. Set to ``0`` to disable these checks.
    * *type*: integer
    * *default*: ``0`` (no check is done)

``ttl``
~~~~~~~
    * Time to live in seconds for the TXT entries inserted in the DNS zone during a DNS-01 challenge.
    * *type*: ``integer``
    * *default*: ``null`` (use any default TTL value specific to the DNS provider associated to this profile)

``certificates`` Section
========================

This sections handles the actual certificates that DNSroboCert needs to generate and renew regularly.
It takes the form of **a list of certificates**. Each certificate is an object that describe the domains
that needs to be included in the certificate, and the profile to use to handle the DNS-01 challenges: the
profile is referred by its name, and **must** exist in the ``profiles`` Section.

In parallel several actions can be defined when a certificate is created or renewed. These actions have to
be defined in each relevant certificate configuration.

.. code-block:: yaml

    certificates:
    - name: my-wildcard-cert
      domains:
      - "*.example.net"
      - example.net
      profile: my_profile1
      pfx:
        export: true
        passphrase: PASSPHRASE
      autorestart:
      - containers:
        - container1
      - swarm_services:
        - service1
      podman_containers:
        - podman1
      autocmd:
      - cmd: /usr/bin/remote_deploy.sh
        containers:
        - container2
    - domains:
      - www.sub.example.net
      profile: my_profile2
      deploy_hook: python /home/user/local_deploy.py
      force_renew: false
      follow_cnames: false
      reuse_key: false
      key_type: ecdsa

``certificate`` properties
--------------------------

``profile``
~~~~~~~~~~~
    * The profile name to use to validated DNS-01 challenges. This profile must exist in the ``profiles``
      section.
    * *type*: ``string``
    * **mandatory property**

``domains``
~~~~~~~~~~~
    * List of the domains to include in the certificate.
    * *type*: ``list[string]``
    * **mandatory property**

``name``
~~~~~~~~
    * Name of the certificate, used in particular to define where the certificate assets (key, cert, chain...)
      will be stored on the filesystem. For a certificate named ``my-cert``, files will be available in the
      directory whose path is ``[CERTS_PATH]/live/my-cert``. If the name is not specified, the effective
      certificate name will be the first domain listed in the ``domains`` property.
    * *type*: ``string``
    * *default*: ``null`` (in this case name is extracted from the first domain listed in ``domains``, for
      instance ``example.net`` for ``example.net`` or ``*.example.net``)

``pfx``
~~~~~~~
    * Configure an export of the certificate into the PFX (also known as PKCS#12) format upon creation/renewal.
    * *type*: ``object``
    * *default*: ``null`` (certificate is not exported in PFX format)

    ``export``
        * If `true`, the certificate is exported in PFX format.
        * *type*: ``boolean``
        * *default*: ``false`` (the certificate is not exported in PFX format)

    ``passphrase``
        * If set, the PFX file will be protected with the given passphrase.
        * *type*: ``string``
        * *default*: ``null`` (the PFX file is not protected by a passphrase)

``deploy_hook``
~~~~~~~~~~~~~~~
    * A command hook to execute locally when the certificate is created/renewed.
    * *type*: ``string``
    * *default*: ``null`` (no deploy hook is configured)

  .. note::

    Several additional environment variables are injected by DNSrobocCert in the command
    runs by ``deploy_hook``:
    
    * ``DNSROBOCERT_CERTIFICATE_NAME``: name of the current certificate in the configuration file,
    * ``DNSROBOCERT_CERTIFICATE_DOMAINS``: comma-separated list of the domains for the current certificate,
    * ``DNSROBOCERT_CERTIFICATE_PROFILE``: DNSroboCert profile associated with the current certificate.

``force_renew``
~~~~~~~~~~~~~~~
    * If ``true``, the certificate will be force renewed when DNSroboCert configuration changes. Useful
      for debugging purposes.
    * *type*: ``boolean``
    * *default*: ``false`` (the certificate is not force renewed)

``follow_cnames``
~~~~~~~~~~~~~~~~~
    * If ``true``, DNSroboCert will follow the chain of CNAME that may be defined for the challenge
      DNS names ``_acme-challenge.DOMAIN`` (where ``DOMAIN`` is the domain to validate and integrate
      in the certificate). This allows to delegate the validation to another DNS zone for security
      purpose. See this link_ for more details.
    * *type*: ``boolean``
    * *default*: ``false`` (CNAME chain is not followed)

``reuse_key``
~~~~~~~~~~~~~
    * If ``true``, the existing private key will be reused during certificate renewal instead of
      creating a new one each time the certificate is renewed.
    * *type*: ``boolean``
    * *default*: ``false`` (the private key is never reused for certificate renewal)

``key_type``
~~~~~~~~~~~~
    * Type of key to use when the certificate is generated. Must be ``rsa`` or ``ecdsa``.
    * *type*: ``string``
    * *default*: ``rsa`` (a RSA-type key will be used)


.. _link: https://letsencrypt.org/2019/10/09/onboarding-your-customers-with-lets-encrypt-and-acme.html#the-advantages-of-a-cname

.. _warning-container-config:

.. warning::

    The following paragraphs describe the ``autorestart`` and ``autocmd`` features. To allow them to work properly,
    DNSroboCert must have access to the Docker client socket file or the Podman socket. Usually at path:
    
    * `/var/run/docker.sock` for Docker,
    * `/run/podman/podman.sock` for rootful Podman,
    * `/run/user/$UID/podman/podman.sock` where $UID is your user id for rootless podman.

    If DNSroboCert is run directly on the host, this usually requires to use a user with administrative privileges,
    or member of the `docker` group.

    If DNSroboCert is run as a Docker, you will need to mount the Docker client socket file into the container.
    As an example the following command does that:

    .. code-block:: console

        $ docker run --rm --name dnsrobocert
            --mount /var/run/docker.sock:/var/run/docker.sock
            adferrand/dnsrobocert

    If DNSroboCert is run as a Podman, you will need to mount the podman socket into the container.
    As an example the following command does that:

    For rootless Podman:

    .. code-block:: console

        $ podman run --rm --name dnsrobocert
            --volume /run/user/$UID/podman/:/run/podman
            docker.io/adferrand/dnsrobocert

    For rootful Podman:

    .. code-block:: console

        $ sudo podman run --rm --name dnsrobocert
            --volume /run/podman/:/run/podman
            docker.io/adferrand/dnsrobocert

``autorestart``
~~~~~~~~~~~~~~~
    * Configure an automated restart of target containers when the certificate is created/renewed. This
      property takes a list of autorestart configurations. Each autorestart is triggered in the order
      they have been inserted here.
    * *type*: ``list[object]``
    * *default*: ``null`` (no automated restart is triggered)

    ``containers``
        * A list of Docker containers to restart.
        * *type*: ``list[string]``
        * *default*: ``null`` (no containers to restart)

    ``swarm_services``
        * A list of swarm services to force restart
        * *type*: ``list[string]``
        * *default*: ``null`` (no swarm services to restart)

    ``podman_containers``
        * A list of Podman containers to restart.
        * *type*: ``list[string]``
        * *default*: ``null`` (no containers to restart)

    **Property configuration example**

    .. code-block:: yaml

        autorestart:
        - containers:
          - container1
          - container2
          swarm_services:
          - service1

``autocmd``
~~~~~~~~~~~
    * Configure an automated execution of an arbitrary command on target containers when the certificate is
      is created/renewed. This property takes a list of autocmd configurations. Each autocmd is triggered
      in the order they have been inserted here.
    * *type*: ``list[object]``
    * *default*: ``null`` (no automated command is triggered)

    ``cmd``
        * The command to execute in each target container. Only commands of string type will be executed in a shell.
        * *type*: ``string`` or ``list[string]``
        * **Mandatory property**

    ``containers``
        * A list of Docker containers on which the command will be executed.
        * *type*: ``list[string]``
        * *default*: ``null`` (no containers to restart)

    **Property configuration example**

    .. code-block:: yaml

        autocmd:
        - containers:
          - container1
          - container2
          cmd: [echo, "Hello World!"]
        - containers:
          - container3
          cmd: env

    .. warning::

        The feature ``autocmd`` is intended to call a simple executable file with few potential arguments.
        It is not made to call some advanced bash script, and would likely fail if you do so. In fact, the command
        is not executed in a shell on the target, and variables would be resolved against the DNSroboCert container
        environment. If you want to operate advanced scripting, put an executable script in the target container,
        and use its path in the relevant ``autocmd[].cmd`` property.

Environment variables
=====================

You can inject environment variables in the configuration file using the ``${MY_VARIABLE}`` format.

For instance, given that an environment variable named ``AUTH_TOKEN`` with the value ``my-secret-token`` exists,
you can write the following file configuration content:

.. code-block:: yaml

    profiles:
      - name: my_profile
        provider: digitalocean
        provider_options:
          auth_token: ${AUTH_TOKEN}
    certificates: []

Then it will be resolved as:

.. code-block:: yaml

    profiles:
      - name: my_profile
        provider: digitalocean
        provider_options:
          auth_token: my-secret-token
    certificates: []

Non-existent variables declared in the configuration file will raise an error.

.. note::

    If you want to write a literal ``${NOT_A_VARIABLE}`` that should not be resolved, you can escape the ``${}``
    syntax by prepending a second dollar sign like so: ``$${NOT_A_VARIABLE}``.

.. _GitHub: https://raw.githubusercontent.com/adferrand/dnsrobocert/main/src/dnsrobocert/schema.yml
.. _Lexicon Providers configuration reference: https://dns-lexicon.github.io/dns-lexicon/providers_options.html
