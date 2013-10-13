.. _creating_sd_images:

Creating your own spin-docker images
====================================

Spin-docker is compatible with all docker images, but it can only use activity monitoring if it runs containers that are configured to report their activity back to spin-docker using the ``/v1/check-in`` URL.

To see the list of publicly available spin-docker images, visit the spin-docker namespace on the docker registry: https://index.docker.io/u/atbaker/. Someone may have created an image that meets your needs already.

Image requirements
------------------

A docker image must satisfy only three requirements to be fully compatible with spin-docker:

- Expose port 22 for SSH access
- Expose any other port for use by an application
- Regularly send HTTP POST requests to the server's ``/v1/check-in`` URL reporting its activity

How you meet these requirements is up to you. Sample Dockerfiles are available on GitHub to help guide you:

- **Template:** https://github.com/atbaker/sd-base
- **PostgreSQL:** https://github.com/atbaker/sd-postgres
- **MongoDB:** https://github.com/atbaker/sd-mongo
- **Django + Gunicorn:** https://github.com/atbaker/sd-django

Using the Phusion base image
----------------------------

The easiest way to build a custom spin-docker image is to start with `Phusion's baseimage-docker <https://github.com/phusion/baseimage-docker>`_. 

This image is based on Ubuntu 12.04 LTS and includes SSH, cron, and other helpful tools while staying lean. It uses `runit <http://smarden.org/runit/>`_ instead of Upstart to provide a correct init process for your containers without adding much overhead. All the spin-docker images use it.

Follow the instructions starting at `Using baseimage-docker as a base image <https://github.com/phusion/baseimage-docker#using-baseimage-docker-as-base-image>`_ to build your own spin-docker compatible Dockerfile.

Don't overlook the section on `adding additional daemons <https://github.com/phusion/baseimage-docker#adding-additional-daemons>`_ to configure your own app to work with runit.

.. warning::

    Note that all the spin-docker examples use `Phusion's insecure key <https://github.com/phusion/baseimage-docker#using-the-insecure-key-for-one-container-only>`_. The insecure key is enabled by the ``RUN /usr/sbin/enable_insecure_key`` line in the Dockerfiles.

    **This key should not be used in production** because the public and private keys are available to all. You should instead create your own SSH keys to load into containers and distribute to users who will need SSH access.

Using a provisioning tool
-------------------------

Dockerfiles are great for building simple images, but complex apps might be better served by a provisioning tool like `Ansible <http://www.ansible.com/home>`_ or `Puppet <http://puppetlabs.com/>`_ - especially if your app already uses one of these tools.

If you choose this route you should still use the ``sd-base`` Dockerfile and the Phusion base image to start a container with SSH, cron, and runit support. You can then start a container with that base image, run your provisioning tool, and then use ``docker commit`` to create a docker image out of that container's current state.

One drawback of this approach is that you must use the ``--run="{ ... }"`` option with ``docker commit`` to specify the correct init command (``"Cmd": ["/sbin/my_init"]``) and which ports to expose (``"PortSpecs": ["22", "80"]``).

Read up on `docker's commit command <http://docs.docker.io/en/latest/reference/commandline/cli/#commit>`_ for more information.

Reporting container activity
----------------------------

Your image can use any means you like to send HTTP POST requests back to the spin-docker server. See :doc:`/check_in` for details on how to create that request.

The easiest way to report on your container's activity is to write a small script which gathers the relevant information from your container and POSTs it back to spin-docker. The definition of activity is up to you - spin-docker considers any POST with non-zero ``active`` field to be from an active container.

The Phusion baseimage comes with cron installed, so once you have your script just add it to the crontab to keep it running regularly.

See the `sd-postgres script <https://github.com/atbaker/sd-postgres/blob/master/sd_postgres_client.py>`_ or the `sd-django script <https://github.com/atbaker/sd-django/blob/master/sd_gunicorn_client.py>`_ for a complete example.

Keeping it slim: container vs. virtual machine
----------------------------------------------

Running multiple processes inside a docker container is a controversial subject. Michael Crosby of Docker has said that `running an init process inside a container is almost always a mistake <http://crosbymichael.com/category/docker.html>`_. Docker CEO Solomon Hykes has said that `docker images like Phusions are legitimate <https://twitter.com/solomonstre/status/435986031024668672>`_, though the more overhead you put in one image the less efficient it becomes. One of the `Dockerfile examples in the Docker documentation <http://docs.docker.io/en/latest/examples/using_supervisord/>`_ uses supervisord to launch multiple processes in a container.

For now, the moral of the story is to keep your docker images as slim as possible. If you want to use spin-docker's activity monitoring, your containers will by necessity be heavier than if they ran a single process. Spin-docker is fully compatible with all docker images, so you are not limited if you choose run only a single process in your images.
