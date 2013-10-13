.. _stack:

Spin-docker technical architecture
==================================

Spin-docker is a Python application built with the following components:

- `Docker <https://www.docker.io/>`_ for lightweight virtualization
- `Flask-RESTful <http://flask-restful.readthedocs.org/en/latest/>`_ (and `Flask <http://flask.pocoo.org/>`_) for easy API development
- `Celery <http://www.celeryproject.org/>`_ for asynchronous tasks
- `Redis <http://redis.io/>`_ for a fast and persistent data store

Spin-docker is deployed with the `gunicorn <http://gunicorn.org/>`_ WSGI server and `Nginx <http://wiki.nginx.org/Main>`_ reverse proxy.

It is provisioned with `Ansible <http://www.ansible.com/home>`_ and virtualized locally with `Vagrant <http://www.vagrantup.com/>`_. 
