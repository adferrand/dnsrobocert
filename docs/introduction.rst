============
Introduction
============

.. contents:: Table of Contents
   :local:

Features
========

DNSroboCert is designed to manage `Let's Encrypt`_ SSL certificates based on `DNS challenges`_.

* Let's Encrypt wildcard and regular certificates generation by Certbot_ using DNS challenges,
* Integrated automated renewal of almost expired certificates,
* Standardized API through Lexicon_ library to insert the DNS challenge with various DNS providers,
* Centralized YAML configuration file to maintain several certificates with configuration validity control,
* Modification of container configuration without restart,
* Flexible hooks upon certificate creation/renewal including containers restart, commands in containers
  or custom hooks,

Why use this Docker
===================

If you are reading these lines, you certainly want to secure all your dockerized services using Let's
Encrypt SSL certificates, which are free and accepted everywhere.

If you want to secure Web services through HTTPS, there is already plenty of great tools. In the Docker
world, one can check Traefik_, or nginx-proxy_ + letsencrypt-nginx-proxy-companion_. Basically, theses tools
will allow automated and dynamic generation/renewal of SSL certificates, based on TLS or HTTP challenges,
on top of a reverse proxy to encrypt everything through HTTPS.

So far so good, but you may fall in one of the following categories:

1. You are in a firewalled network, and your HTTP/80 and HTTPS/443 ports are not opened to the outside world.
2. You want to secure non-Web services (like LDAP, IMAP, POP, etc.) were the HTTPS protocol is of no use.
3. You want to generate a wildcard certificate, valid for any sub-domain of a given domain.

For the first case, ACME servers need to be able to access your website through HTTP (for HTTP challenges)
or HTTPS (for TLS challenges) in order to validate the certificate. With a firewall these two challenges -
which are widely used in HTTP proxy approaches - will not be usable: you need to ask a DNS challenge.
Please note that traefik embed DNS challenges, but only for few DNS providers.

For the second case, there is no website to use TLS or HTTP challenges, and you should ask a DNS challenge.
Of course you could create a "fake" website to validate the domain using a HTTP challenge, and reuse the
certificate on the "real" service. But it is a workaround, and you have to implement a logic to propagate
the certificate, including during its renewal. Indeed, most of the non-Web services will need to be
restarted each time the certificate is renewed.

For the last case, the use of a DNS challenge is mandatory. Then the problems concerning certificates
propagation that have been discussed in the second case will also occur.

The solution is a dedicated and specialized Docker service which handles the creation/renewal of
Let's Encrypt certificates, and ensure their propagation in the relevant Docker services. It is the
purpose of this container.


.. _Let's Encrypt: https://letsencrypt.org/
.. _DNS challenges: https://tools.ietf.org/html/draft-ietf-acme-acme-01#page-44
.. _Certbot: https://github.com/certbot/certbot
.. _Lexicon: https://github.com/AnalogJ/lexicon
.. _Traefik: https://hub.docker.com/_/traefik/
.. _nginx-proxy: https://hub.docker.com/r/jwilder/nginx-proxy/
.. _letsencrypt-nginx-proxy-companion: https://hub.docker.com/r/jrcs/letsencrypt-nginx-proxy-companion/
