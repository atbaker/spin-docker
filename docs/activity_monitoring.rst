.. _activity_monitoring:

Activity monitoring
===================

Spin-docker's activity monitoring feature automatically stops containers that aren't reporting any active connections. This helps you reduce the computing resources you need to run your PaaS by only running containers that are actually in use.

If you would prefer to disable this feature and instead stop your containers manually with HTTP calls to the :ref:`containers endpoint <containers_endpoint>`, see the :ref:`disabling_monitoring` section of the quickstart.

Container self-reporting
------------------------

To keep spin-docker compatible with as many applications as possible it relies on the containers themselves to report their activity back to spin-docker, rather than spin-docker actively monitoring the containers' activity itself.

This self-reporting is done by making a POST request to a container's default gateway at the ``/v1/check-in`` URL. Read :doc:`/check_in` to learn more about the check-in URL.

A container's activity is tracked in its ``active`` field. When this field has any value other than 0, the container is considered active.

To learn more about how to write automated scripts to monitor your containers, read :doc:`/creating_sd_images`.

Stopping idle containers (example workflow)
-------------------------------------------

As each container is started, an asynchronous celery task is added to check on the container's activity. This task is scheduled to occur after the container has been running for the number of seconds listed in the ``sd_initial_timeout_interval`` setting.

When the initial timeout interval has elapsed and the first activity check occurs, spin-docker references the ``active`` field for the container.

If the ``active`` field is 0, then the container is idle. Spin-docker will schedule one last check on the container using the ``sd_timeout_interval`` setting. If the container is still inactive after this second check, spin-docker will stop (but not delete) the container.

If during any check the ``active`` field is not 0, then spin-docker will schedule another activity check to occur after the number of seconds in the ``sd_timeout_interval`` setting. This will continue indefinitely until the container is found to be idle.

Once stopped, a container can always be started again with a PATCH request to the :ref:`containers endpoint <containers_endpoint>`. Keep in mind that the container will likely have different ports exposed when it starts up again.

Read :doc:`/administer` to continue learning about how to run your own spin-docker server.


