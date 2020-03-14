Lexicon providers configuration reference
=========================================

aliyun
------

* `auth_key_id`: Specify access key id for authentication
* `auth_secret`: Specify access secret for authentication

aurora
------

* `auth_api_key`: Specify api key for authentication
* `auth_secret_key`: Specify the secret key for authentication

azure
-----

* `auth_client_id`: Specify the client id (aka application id) of the app registration
* `auth_client_secret`: Specify the client secret of the app registration
* `auth_tenant_id`: Specify the tenant id (aka directory id) of the app registration
* `auth_subscription_id`: Specify the subscription id attached to the resource group
* `resource_group`: Specify the resource group hosting the dns zone to edit

cloudflare
----------

* `auth_username`: Specify email address for authentication
* `auth_token`: Specify token for authentication

cloudns
-------

* `auth_id`: Specify user id for authentication
* `auth_subid`: Specify subuser id for authentication
* `auth_subuser`: Specify subuser name for authentication
* `auth_password`: Specify password for authentication
* `weight`: Specify the srv record weight
* `port`: Specify the srv record port

cloudxns
--------

* `auth_username`: Specify api-key for authentication
* `auth_token`: Specify secret-key for authentication

conoha
------

* `auth_region`: Specify region. if empty, region `tyo1` will be used.
* `auth_token`: Specify token for authentication. if empty, the username and password will be used to create a token.
* `auth_username`: Specify api username for authentication. only used if --auth-token is empty.
* `auth_password`: Specify api user password for authentication. only used if --auth-token is empty.
* `auth_tenant_id`: Specify tenand id for authentication. only used if --auth-token is empty.

constellix
----------

* `auth_username`: Specify the api key username for authentication
* `auth_token`: Specify secret key for authenticate=

digitalocean
------------

* `auth_token`: Specify token for authentication

dinahosting
-----------

* `auth_username`: Specify username for authentication
* `auth_password`: Specify password for authentication

directadmin
-----------

* `auth_password`: Specify password for authentication (or login key for two-factor authentication)
* `auth_username`: Specify username for authentication
* `endpoint`: Specify the directadmin endpoint

dnsimple
--------

* `auth_token`: Specify api token for authentication
* `auth_username`: Specify email address for authentication
* `auth_password`: Specify password for authentication
* `auth_2fa`: Specify two-factor auth token (otp) to use with email/password authentication

dnsmadeeasy
-----------

* `auth_username`: Specify username for authentication
* `auth_token`: Specify token for authentication

dnspark
-------

* `auth_username`: Specify api key for authentication
* `auth_token`: Specify token for authentication

dnspod
------

* `auth_username`: Specify api id for authentication
* `auth_token`: Specify token for authentication

dreamhost
---------

* `auth_token`: Specify api key for authentication

easydns
-------

* `auth_username`: Specify username for authentication
* `auth_token`: Specify token for authentication

easyname
--------

* `auth_username`: Specify username used to authenticate
* `auth_password`: Specify password used to authenticate

euserv
------

* `auth_username`: Specify email address for authentication
* `auth_password`: Specify password for authentication

exoscale
--------

* `auth_key`: Specify api key for authentication
* `auth_secret`: Specify api secret for authentication

gandi
-----

* `auth_token`: Specify gandi api key
* `api_protocol`: (optional) specify gandi api protocol to use: rpc (default) or rest

gehirn
------

* `auth_token`: Specify access token for authentication
* `auth_secret`: Specify access secret for authentication

glesys
------

* `auth_username`: Specify username (cl12345)
* `auth_token`: Specify api key

godaddy
-------

* `auth_key`: Specify the key to access the api
* `auth_secret`: Specify the secret to access the api

googleclouddns
--------------

* `auth_service_account_info`: 
        specify the service account info in the google json format:
        can be either the path of a file prefixed by 'file::' (eg. file::/tmp/service_account_info.json)
        or the base64 encoded content of this file prefixed by 'base64::'
        (eg. base64::eyjhbgcioyj...)

gransy
------

* `auth_username`: Specify username for authentication
* `auth_password`: Specify password for authentication

gratisdns
---------

* `auth_username`: Specify email address for authentication
* `auth_password`: Specify password for authentication

henet
-----

* `auth_username`: Specify username for authentication
* `auth_password`: Specify password for authentication

hetzner
-------

* `auth_account`: Specify type of hetzner account: by default hetzner robot (robot) or hetzner konsoleh (konsoleh)
* `auth_username`: Specify username of hetzner account
* `auth_password`: Specify password of hetzner account
* `linked`: If exists, uses linked cname as a|aaaa|txt record name for edit actions: by default (yes); further restriction: only enabled if record name or raw fqdn record identifier 'type/name/content' is specified, and additionally for update actions the record name remains the same
* `propagated`: Waits until record is publicly propagated after succeeded create|update actions: by default (yes)
* `latency`: Specify latency, used during checks for publicly propagation and additionally for hetzner robot after record edits: by default 30s (30)

hostingde
---------

* `auth_token`: Specify api key for authentication

hover
-----

* `auth_username`: Specify username for authentication
* `auth_password`: Specify password for authentication

infoblox
--------

* `auth_user`: Specify the user to access the infoblox wapi
* `auth_psw`: Specify the password to access the infoblox wapi
* `ib_view`: Specify dns view to manage at the infoblox
* `ib_host`: Specify infoblox host exposing the wapi

internetbs
----------

* `auth_key`: Specify api key for authentication
* `auth_password`: Specify password for authentication

inwx
----

* `auth_username`: Specify username for authentication
* `auth_password`: Specify password for authentication

linode
------

* `auth_token`: Specify api key for authentication

linode4
-------

* `auth_token`: Specify api key for authentication

localzone
---------

* `filename`: Specify location of zone master file

luadns
------

* `auth_username`: Specify email address for authentication
* `auth_token`: Specify token for authentication

memset
------

* `auth_token`: Specify api key for authentication

namecheap
---------

* `auth_token`: Specify api token for authentication
* `auth_username`: Specify username for authentication
* `auth_client_ip`: Client ip address to send to namecheap api calls
* `auth_sandbox`: Whether to use the sandbox server

namesilo
--------

* `auth_token`: Specify key for authentication

netcup
------

* `auth_customer_id`: Specify customer number for authentication
* `auth_api_key`: Specify api key for authentication
* `auth_api_password`: Specify api password for authentication

nfsn
----

* `auth_username`: Specify username used to authenticate
* `auth_token`: Specify token used to authenticate

nsone
-----

* `auth_token`: Specify token for authentication

onapp
-----

* `auth_username`: Specify email address of the onapp account
* `auth_token`: Specify api key for the onapp account
* `auth_server`: Specify url to the onapp control panel server

online
------

* `auth_token`: Specify private api token

ovh
---

* `auth_entrypoint`: Specify the ovh entrypoint
* `auth_application_key`: Specify the application key
* `auth_application_secret`: Specify the application secret
* `auth_consumer_key`: Specify the consumer key

plesk
-----

* `auth_username`: Specify username for authentication
* `auth_password`: Specify password for authentication
* `plesk_server`: Specify url to the plesk web ui, including the port

pointhq
-------

* `auth_username`: Specify email address for authentication
* `auth_token`: Specify token for authentication

powerdns
--------

* `auth_token`: Specify token for authentication
* `pdns_server`: Uri for powerdns server
* `pdns_server_id`: Server id to interact with
* `pdns_disable_notify`: Disable slave notifications from master

rackspace
---------

* `auth_account`: Specify account number for authentication
* `auth_username`: Specify username for authentication. only used if --auth-token is empty.
* `auth_api_key`: Specify api key for authentication. only used if --auth-token is empty.
* `auth_token`: Specify token for authentication. if empty, the username and api key will be used to create a token.
* `sleep_time`: Number of seconds to wait between update requests.

rage4
-----

* `auth_username`: Specify email address for authentication
* `auth_token`: Specify token for authentication

rcodezero
---------

* `auth_token`: Specify token for authentication

route53
-------

* `auth_access_key`: Specify access_key for authentication
* `auth_access_secret`: Specify access_secret for authentication
* `private_zone`: Indicates what kind of hosted zone to use. if true, use only private zones. if false, use only public zones
* `auth_username`: Alternative way to specify the access_key for authentication
* `auth_token`: Alternative way to specify the access_secret for authentication

safedns
-------

* `auth_token`: Specify the api key to authenticate with

sakuracloud
-----------

* `auth_token`: Specify access token for authentication
* `auth_secret`: Specify access secret for authentication

softlayer
---------

* `auth_username`: Specify username for authentication
* `auth_api_key`: Specify api private key for authentication

subreg
------

* `auth_username`: Specify username for authentication
* `auth_password`: Specify password for authentication

transip
-------

* `auth_username`: Specify username for authentication
* `auth_api_key`: Specify api private key for authentication

vultr
-----

* `auth_token`: Specify token for authentication

yandex
------

* `auth_token`: Specify pdd token (https://tech.yandex.com/domain/doc/concepts/access-docpage/)

zeit
----

* `auth_token`: Specify your api token

zilore
------

* `auth_key`: Specify the zilore api key to use

zonomi
------

* `auth_token`: Specify token for authentication
* `auth_entrypoint`: Use zonomi or rimuhosting api

