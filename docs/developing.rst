.. _developing:

Developing for spin-docker
==========================

Contributing to spin-docker development is easy! `Fork the GitHub repository <https://github.com/atbaker/spin-docker>`_ and you're halfway there!

Development environment setup
-----------------------------

The easiest way to set up a spin-docker development environment is to follow the instructions in :ref:`vagrant_setup`.

Once you have provisioned your vagrant box, you can run the Flask development server with these steps:

#. ``vagrant ssh`` into the box
#. Switch to the root user (necessary to start the development server on port 80, which is forwarded by Vagrant)
#. Stop the nginx, gunicorn, and celery services: 
    
    .. code-block:: bash

        $ service nginx stop 
        $ service gunicorn stop 
        $ service celery stop 

#. ``cd`` to the ``/var/www``
#. Activate the spin-docker virutal environment: ``source venv/bin/activate``
#. ``cd`` into the ``spin-docker`` directory
#. Apply the spin-docker environment variables with ``source .env``
#. Start the Flask development server: ``python runserver.py``

Activity monitoring, stopping, and deleting containers are managed by Celery. You can start the Celery worker in a separate terminal session (but still as root, because docker is currently configured only for root):

#. ``cd`` to the ``/var/www``
#. Activate the spin-docker virutal environment: ``source venv/bin/activate``
#. ``cd`` into the ``spin-docker`` directory
#. Apply the spin-docker environment variables with ``source .env``
#. Run the command ``celery -A spindocker.tasks.celery worker -l info``

Running tests
-------------

To run the spin-docker tests and view current code coverage, follow these steps (again as root):

#. ``cd`` to the ``/var/www``
#. Activate the spin-docker virutal environment: ``source venv/bin/activate``
#. ``cd`` into the ``spin-docker`` directory
#. Apply the spin-docker environment variables with ``source .env``
#. Install the test requirements in you haven't already: ``pip install -r requirements/test.txt``
#. Run the command ``coverage run --source=spindocker tests.py``

After the tests run, you can view current coverage with ``coverage report`` and generate an HTML report with ``coverage html``.

Building the docs
-----------------

If you make changes to the spin-docker documentation, you can check your work by building the docs with ``make html`` in the ``docs`` directory.
