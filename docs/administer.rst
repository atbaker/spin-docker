.. _administer:

Administering spin-docker
=========================

Configuration
-------------

Spin-docker uses only a few configurable settings. They are all in the Ansible playbook in the spin_docker.yml file:

.. code-block:: yaml

    # Spin-docker configuration settings
    sd_environment: 'development'
    sd_password: 'spindocker'
    sd_disable_timeouts: False
    sd_initial_timeout_interval: 7200
    sd_timeout_interval: 1800

**sd_environment** - Set to ``production`` to disable spin-docker's debug mode.

**sd_password** - The password used for basic HTTP authentication for the ``admin`` user.

**sd_disable_timeouts** - When set to ``True`` spin-docker will never stop a container with no active connections. See :doc:`/activity_monitoring` for more details.

**sd_initial_timeout_interval** - How many seconds spin-docker should wait before the first time it checks a container's activity. Use this setting to control the minumum amount of time a container will stay running.

**sd_timeout_interval** - How many seconds spin-docker should wait between each activity check. Increasing this value will extend the amount of time a container stays running without activity.

After changing these settings, you will need to provision your spin-docker server again (using ``vagrant provision`` or ``ansible-playbook -i hosts spin_docker.yml``) to apply them.

Adding new images
-----------------

Spin-docker does not currently support adding new images to the server. Until this feature exists (pull requests welcome!) you will need to add new images manually using the docker command line interface.

Use `docker pull <http://docs.docker.io/en/latest/reference/commandline/cli/#pull>`_ to get new images from the `docker index <https://index.docker.io/>`_. Use `docker build <http://docs.docker.io/en/latest/reference/commandline/cli/#build>`_ to compile `your own Dockerfiles <http://docs.docker.io/en/latest/reference/builder/>`_.

Spin-docker is compatible with all docker images, but it can only monitor the activity of images that report their activity back to spin-docker at the ``/v1/check-in`` URL. 

To see the list of publicly available spin-docker images, visit the spin-docker namespace on the docker registry: https://index.docker.io/u/atbaker/

.. warning::

    Unless you plan to only run spin-docker images on your spin-docker server, you should :ref:`disable container monitoring <disabling_monitoring>` in your configuration settings. Otherwise, all containers you create will be stopped after two and a half hours whether they are in use or not.

Learn how to create your own spin-docker compatible images in :doc:`/creating_sd_images`.

Auditing containers
-------------------

On rare occasions spin-docker's information about containers can get out of sync with docker's. This usually only happens when you have been messing with docker on the machine manually.

Spin-docker can perform an audit of all containers it is aware of if you add an ``audit=true`` parameter on a GET request to ``/v1/containers``. You can do this using curl:

.. code-block:: bash

    curl http://localhost:8080/v1/containers -X GET -u admin:spindocker -d "audit=true"

Before spin-docker returns the full list of containers it will check each one and update its fields. It will also reset its ``active`` field to 0 to ensure the container properly reports any activity.

Spin-docker automatically audits containers each time it starts, so it will automatically pick up any container changes that occur because of a server reboot.

SSH known hosts issues
----------------------

If you work on spin-docker long enough, docker will eventually reuse a port for a new container which it had previously used for another container. Because each container generates its own SSH host keys, your SSH client may refuse to connect you to an instance because it suspects foul play:

.. code-block:: none

    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    @    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
    Someone could be eavesdropping on you right now (man-in-the-middle attack)!
    It is also possible that a host key has just been changed.
    The fingerprint for the RSA key sent by the remote host is
    2e:3e:ce:d9:10:29:d2:34:48:ea:0d:ba:6b:21:f2:be.
    Please contact your system administrator.
    Add correct host key in /Users/atbaker/.ssh/known_hosts to get rid of this message.
    Offending RSA key in /Users/atbaker/.ssh/known_hosts:16
    RSA host key for [localhost]:49153 has changed and you have requested strict checking.
    Host key verification failed.

The easiest way to fix this is to edit your ``known_hosts`` file and remove all entries for spin-docker containers you have connected to in the past.

Now that you know how to administer a spin-docker server, read :doc:`/creating_sd_images` to learn how to make your own apps fully compatible with spin-docker.

