==========
User guide
==========

Preparation
===========

In order to work properly, DNSroboCert requires a configuration file, which is written in YAML. To avoid
any problem, you should create it before starting DNSroboCert (the file can be empty at this point).

The path of this file is configurable. We will assume in this user guide that it is `/etc/dnsrobocert/config.yml`.

On Linux for instance, run:

.. code-block:: bash

    $ mkdir /etc/dnsrobocert.yml
    $ touch /etc/dnsrobocert/config.yml

DNSroboCert will store the certificates in a specific folder. Here also a good idea is to create it
before starting DNSroboCert.

The path of this folder is configurable. We will assume in this user guide that it is `/etc/letsencrypt`.

On Linux for instance, run:

.. code-block:: bash

    $ mkdir -p /etc/letsencrypt

Installation
============

DNSroboCert can be installed in two ways:

1) On the host using a python package manager
2) As a Docker container

Installation on the host
------------------------

    - DNSroboCert requires Python 3.6+.
    - It can be installed on Linux, Mac OS or Windows.
    - For Linux and Mac OS, running as a privileged user (eg. root) is recommended.
    - For Windows, running as a privileged user (eg. Administrator) is required.

The recommended way is to use Pipx_, a tool that extends Pip_ and is specifically designed to
install a Python program in a isolated and dedicated environment.

You need Python 3.6+ installed on your machine.

Install `pipx` using `pip`:

.. code-block:: bash

    $ python3 -m pip install pipx
    $ python3 -m pipx ensurepath

Then install DNSroboCert on the desired version (eg. `3.0.0`):

.. code-block:: bash

    $ python3 -m pipx dnsrobocert==3.0.0

At this point DNSroboCert is installed and available in the `PATH`. You can display the inline help using:

.. code-block:: bash

    $ dnsrobocert --help

And run DNSroboCert with:

.. code-block:: bash

    $ dnsrobocert -c /etc/dnsrobocert.yml -d /etc/letsencrypt

DNSroboCert will continue to run in the foreground. To stop it, press CTRL+C.

Running as a Docker container
-----------------------------

An up-to-date Docker image is available in DockerHub_. In order to persist DNSroboCert configuration and
the generated certificates, you should mount its configuration and the dedicated folder for certificates
from the host into the container.

* For the configuration file, expected path is `/etc/letsencrypt/dnsrobocert.yml`
* For the certificates folder, expected path is `/etc/letsencrypt`

    Both paths are configurable in the container through the environment variables `CONFIG_PATH` and
    `CERTS_PATH` respectively.

Finally you can run this typical command for the desired version (eg. 3.0.0):

.. code-block:: bash

    docker run --rm --name dnsrobocert
        --volume /etc/dnsrobocert/config.yml:/etc/dnsrobocert/config.yml
        --volume /etc/letsencrypt:/etc/letsencrypt
        adferrand/dnsrobocert:3.0.0

The Docker container will continue to run in the foreground. To stop it, press CTRL+C.


.. _Pipx: https://github.com/pipxproject/pipx
.. _Pip: https://docs.python.org/fr/3.6/installing/index.html
.. _DockerHub: https://hub.docker.com/r/adferrand/letsencrypt-dns/
