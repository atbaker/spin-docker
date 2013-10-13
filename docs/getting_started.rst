.. _getting_started:

Getting started
===============

Standing up your own spin-docker server locally or in the cloud takes minutes. Setup also includes the PostgreSQL, MongoDB, and Django spin-docker images.

Grabbing the source
-------------------

First download the spin-docker source code - either by `cloning the repository on GitHub <https://github.com/atbaker/spin-docker>`_ or `downloading and extracting the current version <https://github.com/atbaker/spin-docker/archive/v1.0.0.zip>`_.

Whether you want to run spin-docker in a local virtual machine or on a server, you need `Ansible <http://www.ansible.com/home>`_ to provision it. `Installing Ansible <http://docs.ansible.com/intro_installation.html#installing-the-control-machine>`_ is easy. You can download the source, get it from apt or yum, or just use `pip <http://pip.readthedocs.org/en/latest/installing.html>`_:

.. code-block:: bash

    $ sudo pip install ansible

.. _vagrant_setup:

Running locally with Vagrant
----------------------------

The easiest way to run spin-docker is using a local virtual machine with `Vagrant <http://www.vagrantup.com/>`_. 

`Install Vagrant <http://docs.vagrantup.com/v2/getting-started/index.html>`_ using the instructions on their site. Like those instructions, this guide will also assume you're using `Virtualbox <http://www.virtualbox.org/>`_ as your provider.

Before you start your virtual server, add this environment variable to your session if you want your spin-docker containers to be accessible outside of your virtual machine:

.. code-block:: bash

    $ export FORWARD_DOCKER_PORTS='True'

Now ``cd`` into your spin-docker code and start the vagrant box with ``vagrant up``. Vagrant will download `Phusion's docker-ready Ubuntu 12.04 server box <http://blog.phusion.nl/2013/11/08/docker-friendly-vagrant-boxes/>`_ and run an ansible playbook to install and configure spin-docker.

.. note::

    If you get a vagrant error when starting your box saying that some forwarded ports are unavailable, you will need to quit the application that's using them. I've noticed that Chrome in particular can sit on ports around 49200. Quitting Chrome, starting the vagrant box, and then starting Chrome again usually works for me.

Once the vagrant box is running, you can use ``vagrant ssh`` to get in and poke around. If you're ready to learn more about spin-docker, check out the :doc:`/api` or :doc:`/administer`.

Deploying to a server using Ansible
-----------------------------------

Spin-docker comes with a complete `Ansible <http://www.ansible.com/home>`_ playbook that can provision any Ubuntu 12.04 server to run spin-docker. `DigitalOcean <https://www.digitalocean.com/>`_ and `Amazon EC2 <http://aws.amazon.com/ec2/>`_ are always good choices.

Once you have an Ubuntu 12.04 server ready, edit the hosts file in the ansible_playbook subdirectory and add the correct hostname, SSH user, and SSH key for your server.

.. code-block:: yaml

    ec2-54-137-143-5.compute-1.amazonaws.com vagrant_box=False ansible_ssh_user=ubuntu ansible_ssh_private_key_file=/Users/atbaker/.ssh/foo.pem

Take care not to accidentally delete the ``vagrant_box=False`` variable.

Now you're ready to run the Ansible play to install and configure spin-docker:

.. code-block:: bash

    $ ansible-playbook -i hosts spin_docker.yml

Ansible will upgrade the linux kernel, install docker, and install spin-docker with its dependencies. It will also pull down the spin-docker PostgreSQL, MongoDB, and Django images from the docker registry so you can start using the server immediately.

.. note::

    Keep an eye on your server resources. If you're running spin-docker on an AWS micro instance, for example, you may experience issues running more than one container. Using the ephemeral instance storage as additional swap space can help: http://serverfault.com/questions/218750/why-dont-ec2-ubuntu-images-have-swap

When you're ready to learn more about spin-docker, check out the :doc:`/api` or :doc:`/administer`.

.. _disabling_monitoring:

Disabling container monitoring
------------------------------

By default spin-docker is configured to stop idle containers after two and a half hours. You may want to disable this feature if you don't want to adapt your containers to report their activity to spin-docker. 

To do this, edit the spin_docker.yaml file in the ansible_playbook directory. Set the ``sd_disable_timeouts`` variable to False:

.. code-block:: yaml

    sd_disable_timeouts: False

Then reprovision your spin-docker server. If you're using vagrant, run ``vagrant provision``. If you're running your own server run ``ansible-playbook -i hosts spin_docker.yml``.

Learn more about how spin-docker monitors container activity by reading :doc:`/activity_monitoring`.
