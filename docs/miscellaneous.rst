=============
Miscellaneous
=============

Migration from docker-letsencrypt-dns
=====================================

DNSroboCert started as a pure Docker implementation named ``adferrand/docker-letsencrypt-dns``. It was coded in bash,
and used both environment variables and a file named ``domains.conf`` for its configuration.

If you followed the link displayed in logs from ``adferrand/docker-letsencrypt-dns``, then this section is for you:
your instance of ``docker-letsencrypt-dns`` have been upgraded to DNSroboCert, and a migration path is proposed.

Indeed to recall, ``domains.conf`` was holding the list of certificates to create and renew, and also the
``autorestart`` and ``autocmd`` features for each certificate. On the other hand, environment variables were
configuring the DNS provider to use, the specific options for Let's Encrypt (account email address, staging servers)
and some custom operations on the certificate assets (like specific users and permissions).

DNSroboCert supports all these features, improves them, and stores its configuration in one central file, located
by default at ``/etc/dnsrobocert/config.yml``. As said by DNSroboCert in the logs, usage of the old environment
variables and the ``domains.conf`` file is deprecated, and **you should move as soon as possible to the ``config.yml``
file**.

Let's see how to do that.

Assisted migration
------------------

I hate writing configuration files. Do you? If so, you will be pleased to know that DNSroboCert handles this migration
for you. As you may seen from the logs, DNSroboCert picked automatically the relevant environment variables you set
and your ``domains.conf`` to generate the new configuration file dynamically.

Its location is `/etc/dnsrobocert/config-generated.yml`. It contains all necessary configuration to make DNSroboCert
behave **exactly** like your ``adferrand/docker-letsencrypt-dns`` before.

Here are the remaining steps to finish the migration:
1. Extract the file from the docker into your host machine (assuming your docker is named ``letsencrypt-dns``)

.. code-block:: bash

    $ mkdir -p /etc/dnsrobocert
    $ docker cp letsencrypt-dns:/etc/dnsrobocert/config-generated.yml /etc/dnsrobocert/config.yml

2. Restart your Docker container with the new configuration file mounted at the right place
   (adapt the command to your actual DNS provider configuration):

.. code-block:: bash

    $ docker run \
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

.. code-block:: bash

    $ docker run \
        --name dnsrobocert \
        --volume /var/docker-data/letsencrypt:/etc/letsencrypt \
        --volume /etc/dnsrobocert/config.yml:/etc/dnsrobocert/config.yml \
        adferrand/dnsrobocert

Manual migration
----------------

If you want to go wild, you can migrate yourself by writing the new ``config.yml`` file to fit your needs, following
the documentation of the `User guide`_ and `Configuration reference`_.

Once done, you can follow the previous section to restart your Docker container.


.. _User guide: https://dnsrobocert.readthedocs.io/en/dnsrobocert/user_guide.html
.. _Configuration reference: https://dnsrobocert.readthedocs.io/en/dnsrobocert/configuration_reference.html
