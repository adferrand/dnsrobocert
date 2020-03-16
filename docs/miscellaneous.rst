=============
Miscellaneous
=============

Migration from docker-letsencrypt-dns
=====================================

DNSroboCert started as a pure Docker implementation named ``adferrand/letsencrypt-dns``. It was coded in bash,
and was using both environment variables and a file named ``domains.conf`` for its configuration.

If you followed the link displayed in logs from ``adferrand/letsencrypt-dns``, then this section is for you:
your instance of ``letsencrypt-dns`` has been upgraded to DNSroboCert, and a migration path is proposed.

To recall, ``domains.conf`` was holding the list of certificates to create and renew, and also the
``autorestart`` and ``autocmd`` features for each certificate. On the other hand, environment variables were
configuring the DNS provider to use, the specific options for Let's Encrypt (account email address, staging servers)
and some custom operations on the certificate assets (like specific users and permissions).

DNSroboCert supports all these features, improves them, and stores its configuration in one structured central file,
located by default at ``/etc/dnsrobocert/config.yml``. As said by DNSroboCert in the logs, usage of the old environment
variables and the ``domains.conf`` file is deprecated, and **you should move as soon as possible to the** ``config.yml``
**file**.

Let's see how to do that.

Assisted migration
------------------

Writing configuration files. Do you agree? If so, you will be pleased to know that DNSroboCert handles this migration
for you. As you may seen from the logs, DNSroboCert picked automatically the relevant environment variables you set
and your ``domains.conf`` to generate the new configuration file dynamically.

Its location is `/etc/dnsrobocert/config-generated.yml`. It contains the necessary configuration to make DNSroboCert
behave **exactly** like your ``adferrand/docker-letsencrypt-dns`` instance before.

Here are the remaining steps to finish the migration:

1. Extract the file from the docker into your host machine (assuming your docker is named ``letsencrypt-dns``)

.. code-block:: console

    mkdir -p /etc/dnsrobocert
    docker cp letsencrypt-dns:/etc/dnsrobocert/config-generated.yml /etc/dnsrobocert/config.yml

2. Restart your Docker container with the new configuration file mounted at the right place
   (adapt the command to your actual DNS provider configuration):

.. code-block:: console

    docker run \
        --name letsencrypt-dns \
        --volume /etc/letsencrypt/domains.conf:/etc/letsencrypt/domains.conf \
        --volume /var/docker-data/letsencrypt:/etc/letsencrypt \
        --volume /etc/dnsrobocert/config.yml:/etc/dnsrobocert/config.yml \
        --env 'LETSENCRYPT_USER_MAIL=admin@example.com' \
        --env 'LEXICON_PROVIDER=cloudflare' \
        --env 'LEXICON_CLOUDFLARE_AUTH_USERNAME=my_cloudflare_email' \
        --env 'LEXICON_CLOUDFLARE_AUTH_TOKEN=my_cloudflare_global_api_key' \
        adferrand/letsencrypt-dns

DNSroboCert will automatically pick the new configuration file. Once you confirmed that everything is working as
before, you can restart the Docker without the environment variables and ``domains.conf``. Please take this occasion
to change the image name from ``adferrand/letsencrypt-dns`` to ``adferrand/dnsrobocert``.

.. code-block:: console

    docker run \
        --name dnsrobocert \
        --volume /var/docker-data/letsencrypt:/etc/letsencrypt \
        --volume /etc/dnsrobocert/config.yml:/etc/dnsrobocert/config.yml \
        adferrand/dnsrobocert

.. note:

    Docker image ``adferrand/letsencrypt-dns`` is deprecated and is replaced by ``adferrand/dnsrobocert``.

Manual migration
----------------

If you want to go berserk, you can migrate yourself by writing the new ``config.yml`` file to fit your needs, following
the documentation of the `User guide`_ and `Configuration reference`_.

Once done, you can follow the previous section to restart your Docker container.

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


.. _User guide: https://dnsrobocert.readthedocs.io/en/dnsrobocert/user_guide.html
.. _Configuration reference: https://dnsrobocert.readthedocs.io/en/dnsrobocert/configuration_reference.html
.. _Project V3 specifications: https://github.com/adferrand/docker-letsencrypt-dns/wiki/Project-V3-specifications,-aka-DNSroboCert