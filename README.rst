Spin-docker: A lightweight RESTful docker PaaS
==============================================

**NOTE: spin-docker is no longer under active development.** If you need a Docker PaaS, I recommend looking at the `dokku <https://github.com/progrium/dokku>`_, `Deis <http://deis.io/>`_, or `Flynn <https://flynn.io/>`_ projects.

**Spin-docker** is a lightweight platform-as-a-service that runs on a RESTful API. Designed with simplicity in mind, spin-docker provides enough features to help you stand up your own `Docker <https://www.docker.io/>`_-powered PaaS in minutes.

Spin-docker was created by `Andrew T. Baker <http://www.andrewtorkbaker.com/>`_ as a side project this winter. It might not be the best Docker-based PaaS out there, but building it was a great learning experience. Check out my blog post about it: http://andrewtorkbaker.com/what-makes-a-good-side-project

Spin-docker is open source under the `MIT license <https://github.com/atbaker/spin-docker/blob/master/LICENSE>`_.

Full documentation is available on ReadTheDocs: http://spin-docker.readthedocs.org/

Example use
-----------

Spin-docker uses a RESTful API so you can easily start and stop docker containers with an HTTP request. Start a PostgreSQL database with:

.. code-block:: bash
    
    $ curl http://localhost:8080/v1/containers -X POST -u admin:spindocker -d "image=atbaker/sd-postgres"

And you'll receive back:

.. code-block:: json

    {
      "status": "running", 
      "name": "/desperate_poincare", 
      "active_connections": "0", 
      "ssh_port": "49153", 
      "image": "atbaker/sd-postgres", 
      "container_id": "0145c3630dccc5529ecd3a61d0e7f04236ef3e7a91d06b2985f50e9aa4dc266d", 
      "uri": "/v1/containers/0145c3630dccc5529ecd3a61d0e7f04236ef3e7a91d06b2985f50e9aa4dc266d", 
      "app_port": "49154"
    }

The ``atbaker/sd-postgres`` docker image runs a PostgreSQL database using `Phusion's base docker image <https://github.com/phusion/baseimage-docker>`_. Spin-docker images report their activity back to spin-docker so it can stop idle containers, but spin-docker is fully compatible with all docker images.

You can SSH into the container using Phusion's insecure key (included in the spin-docker root directory):

.. code-block:: bash
    
    $ ssh -i insecure_key root@127.0.0.1 -p 49153
    $ su postgres -c 'psql'

And of course you (or an app) can connect to the PostgreSQL database directly if you have the PostgreSQL client installed:

.. code-block:: bash

    $ psql -U postgres -h 127.0.0.1 -p 49154

And that's it! Here are a few ideas for how spin-docker could help your organization:

- Use the `PostgreSQL <https://github.com/atbaker/sd-postgres>`_, `MongoDB <https://github.com/atbaker/sd-mongo>`_, and `Django <https://github.com/atbaker/sd-django>`_ images available now to provide on-demand databases and webservers for developers and data scientists
- Create a docker image for your own app and use spin-docker to provide on-demand demo servers for your teams
- Jump start your next training or tutorial session by putting a sample environment in a docker image and using spin-docker to quickly expose those environments to your students

Or just play with spin-docker to learn more about how docker works! Using `Vagrant <http://www.vagrantup.com/>`_ and `Ansible <http://www.ansible.com/home>`_, you can deploy your own spin-docker server anywhere in minutes. Read `getting started with spin-docker <http://spin-docker.readthedocs.org/en/latest/getting_started.html>`_ for more information.
