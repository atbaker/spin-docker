.. _api:

API documentation
=================

Spin-docker is built using the excellent `Flask-RESTful <http://flask-restful.readthedocs.org/en/latest/>`_ `Flask <http://flask.pocoo.org/>`_ extension. Though the API is basic right now, it can be easily extended to keep pace as `docker <https://www.docker.io/>`_ evolves.

The spin-docker API currently has just two endpoints - :ref:`images` and :ref:`containers`:

Authentication
--------------

Spin-docker currently uses basic HTTP authentication for all requests. The username is ``admin`` and the default password is ``spindocker``. All requests to spin-docker need to use these credentials.

If you would like to change the password, edit the ``sd_password`` setting in asible_playbook/spin_docker.yaml.

.. code-block:: yaml

    sd_password: 'spindocker'

.. _images:

Images (/v1/images)
-------------------

The images endpoint exposes the tagged docker images available on a server. It currently only supports GET requests. 

A request to ``/v1/images`` yields:

.. code-block:: json

    [
      "atbaker/sd-mongo:latest", 
      "atbaker/sd-postgres:latest",
      "atbaker/sd-django:latest", 
      "phusion/baseimage:0.9.8"
    ]

This is useful for checking if an image exists on your server before attempting to create a container with it.

.. _containers:

Containers (/v1/containers)
---------------------------

The containers endpoint manages docker containers running on the server. It supports GET, POST, and PATCH requests.

Querying containers
^^^^^^^^^^^^^^^^^^^

A GET request to ``/v1/containers`` yields a list of all containers spin-docker has ever started on the server:

.. code-block:: json

    [
      {
        "status": "running", 
        "name": "/hungry_bell", 
        "active": "0",
        "ssh_port": "49155", 
        "image": "atbaker/sd-postgres", 
        "container_id": "2cd8a1b037d8752a481b373f225ac72ced9ec89ba784b7868dbb784072358f0e", 
        "uri": "/v1/containers/2cd8a1b037d8752a481b373f225ac72ced9ec89ba784b7868dbb784072358f0e", 
        "app_port": "49156"
      }, 
      {
        "status": "running", 
        "name": "/hopeful_ritchie",
        "active": "1",
        "ssh_port": "49157", 
        "image": "atbaker/sd-postgres", 
        "container_id": "ba87a9911beb99b9fab64c387267235bd157c7ab69f9eb15695ebbfffe393ccc", 
        "uri": "/v1/containers/ba87a9911beb99b9fab64c387267235bd157c7ab69f9eb15695ebbfffe393ccc", 
        "app_port": "49158"
      }, 
      {
        "status": "stopped", 
        "name": "/desperate_poincare", 
        "active": "0",
        "ssh_port": "", 
        "image": "atbaker/sd-postgres", 
        "container_id": "0145c3630dccc5529ecd3a61d0e7f04236ef3e7a91d06b2985f50e9aa4dc266d", 
        "uri": "/v1/containers/0145c3630dccc5529ecd3a61d0e7f04236ef3e7a91d06b2985f50e9aa4dc266d", 
        "app_port": ""
      }
    ]

Note that in this example, the last container is stopped and thus is not mapped to any ports.

To get information about just one container, make a GET request to that container's URI. Following our example, hitting this URL:

.. code-block:: none

    /v1/containers/2cd8a1b037d8752a481b373f225ac72ced9ec89ba784b7868dbb784072358f0e

yields

.. code-block:: json

    {
      "status": "running", 
      "name": "/hungry_bell", 
      "active": "0",
      "ssh_port": "49155", 
      "image": "atbaker/sd-postgres", 
      "container_id": "2cd8a1b037d8752a481b373f225ac72ced9ec89ba784b7868dbb784072358f0e", 
      "uri": "/v1/containers/2cd8a1b037d8752a481b373f225ac72ced9ec89ba784b7868dbb784072358f0e", 
      "app_port": "49156"
    }

Creating containers
^^^^^^^^^^^^^^^^^^^

A POST request to ``/v1/containers`` creates a new container. Only one data field is required: the name of the docker image to start. 

Spin-docker determines which ports to forward by referencing the ports exposed on the docker image. If port 22 is exposed, spin-docker will map it to the ssh_port field. If any other port is exposed, spin-docker will map it to the app_port field.

So a POST request to ``/v1/containers`` with this data:

.. code-block:: json

    {
      "image": "atbaker/sd-postgres"
    }

Or using curl:

.. code-block:: bash

  $ curl http://localhost:8080/v1/containers -X POST -u admin:spindocker -d "image=atbaker/sd-postgres"

Will create a new container and return its details:

.. code-block:: json

    {
      "status": "running", 
      "name": "/hungry_bell", 
      "active": "0",
      "ssh_port": "49155", 
      "image": "atbaker/sd-postgres", 
      "container_id": "2cd8a1b037d8752a481b373f225ac72ced9ec89ba784b7868dbb784072358f0e", 
      "uri": "/v1/containers/2cd8a1b037d8752a481b373f225ac72ced9ec89ba784b7868dbb784072358f0e", 
      "app_port": "49156"
    }

By default spin-docker will stop containers that haven't reported any activity to the :doc:`/check_in` URL in two and a half hours. See :doc:`/activity_monitoring` for more details.

.. _containers_endpoint:

Starting and stopping containers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once created, containers can be started or stopped manually through PATCH requests to their specific URIs. 

Following our example, a PATCH request to ``/v1/containers/2cd8a1b037d8752a481b373f225ac72ced9ec89ba784b7868dbb784072358f0e`` with this data:

.. code-block:: json

    {
      "status": "stopped"
    }

Will begin stopping that container and return:

.. code-block:: json

    {
      "status": "stopping", 
      "name": "/hungry_bell", 
      "active": "0",
      "ssh_port": "49155", 
      "image": "atbaker/sd-postgres", 
      "container_id": "2cd8a1b037d8752a481b373f225ac72ced9ec89ba784b7868dbb784072358f0e", 
      "uri": "/v1/containers/2cd8a1b037d8752a481b373f225ac72ced9ec89ba784b7868dbb784072358f0e", 
      "app_port": "49156"
    }

Stopping a container may take up to 10 seconds, so spin-docker does this asynchronously and returns the ``stopping`` status instead to acknowledge your stop order. Doing a GET request to this container's URI in a few seconds will show the container at rest:

.. code-block:: json

    {
      "status": "stopped", 
      "name": "/hungry_bell", 
      "active": "0",
      "ssh_port": "", 
      "image": "atbaker/sd-postgres", 
      "container_id": "2cd8a1b037d8752a481b373f225ac72ced9ec89ba784b7868dbb784072358f0e", 
      "uri": "/v1/containers/2cd8a1b037d8752a481b373f225ac72ced9ec89ba784b7868dbb784072358f0e", 
      "app_port": ""
    }

Starting the container again is easy. Make another PATCH request to the same URI, this time with:

.. code-block:: json

    {
      "status": "running"
    }

And spin-docker will start the container immediately, giving you new ports you can use to connect to it:

.. code-block:: json

    {
      "status": "running", 
      "name": "/hungry_bell", 
      "active": "0",
      "ssh_port": "49157", 
      "image": "atbaker/sd-postgres", 
      "container_id": "2cd8a1b037d8752a481b373f225ac72ced9ec89ba784b7868dbb784072358f0e", 
      "uri": "/v1/containers/2cd8a1b037d8752a481b373f225ac72ced9ec89ba784b7868dbb784072358f0e", 
      "app_port": "49158"
    }

Deleting containers
^^^^^^^^^^^^^^^^^^^

When you're ready to completely remove a container from your server, send a DELETE request to that container's URI. Using curl to continue our example:

.. code-block:: bash

    $ curl http://localhost:8080/v1/containers/2cd8a1b037d8752a481b373f225ac72ced9ec89ba784b7868dbb784072358f0e -X DELETE -u admin:spindocker

Spin-docker will stop the container if it is running, delete it, and return an empty 204 response.

Check-in (/v1/check-in)
-----------------------

The check-in URL isn't an endpoint - it's just a URL that containers can use to report their current activity back to spin-docker. This is covered in more detail :doc:`/creating_sd_images`, but the request itself is simple.

To report on your container's activity, have it regularly POST to the ``/v1/check-in`` URL with one data field: ``active-connections``. Authentication is not required for this URL.

You will also need to determine the appropriate IP address to POST to. To reach spin-docker from within a container, always send your check-ins to the container's default gateway IP address. You can determine the default gateway with ``ip route show``:

.. code-block:: bash

    default via 172.17.42.1 dev eth0 
    172.17.0.0/16 dev eth0  proto kernel  scope link  src 172.17.0.2

In this case, the container's default gateway is ``172.17.42.1``. If you wanted to use curl to report this container's activity, you would use this command:

.. code-block:: bash

    $ curl http://172.17.42.1/v1/check-in -X POST -d "active-connections=1"

But writing a script and using a cron job to report container activity is more practical. Read more about that in :doc:`/creating_sd_images`.

Or to learn more about administering spin-docker servers, continue to :doc:`/administer`.
