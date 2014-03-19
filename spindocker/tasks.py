from celery import Celery
from docker import APIError
from spindocker.utils import r, client, RUNNING, STOPPED

import os

celery = Celery('spin_docker',
                broker='amqp://',)

# Timeout intervals
DISABLE_TIMEOUTS = os.environ.get('DISABLE_TIMEOUTS')
INITIAL_TIMEOUT_INTERVAL = int(os.environ['INITIAL_TIMEOUT_INTERVAL'])
TIMEOUT_INTERVAL = int(os.environ['TIMEOUT_INTERVAL'])


def get_container_ports(port_info):
    spin_docker_ports = {'ssh_port': '', 'app_port': ''}

    for port, value in port_info.iteritems():
        if value is not None:
            key = 'ssh_port' if port == '22/tcp' else 'app_port'
            spin_docker_ports[key] = value[0]['HostPort']

    return spin_docker_ports

def delete_container_ip(container_id):
    """Deletes a container's IP mapping in redis."""
    container_ip = client.inspect_container(
        container_id)['NetworkSettings']['IPAddress']
    r.delete('ips:%s' % container_ip)

def audit_containers():
    """Reviews all known containers and updates their information in redis."""
    for ip_address in r.keys('ips:*'):
        r.delete(ip_address)

    containers = [r.hgetall(container) for container in r.keys('containers:*')]

    for container in containers:
        container_id = container['container_id']
        try:
            docker_info = client.inspect_container(container_id)
        except APIError:
            r.delete('containers:%s' % container_id)
            break

        if docker_info['State']['Running']:
            ports = get_container_ports(docker_info['NetworkSettings']['Ports'])
            r.hmset('containers:%s' % container_id, {
                    'status': RUNNING, 'active': 0,
                    'ssh_port': ports['ssh_port'],
                    'app_port': ports['app_port']})
            r.set('ips:%s' %
                  docker_info['NetworkSettings']['IPAddress'], container_id)
        else:
            r.hmset('containers:%s' % container_id, {
                    'status': STOPPED, 'active': 0, 'ssh_port': '', 'app_port': ''})

def start_container(container_id):
    """Starts a container. Never actually invoked asynchronously."""
    client.start(container_id, publish_all_ports=True)

    container_details = client.inspect_container(container_id)

    # Gather info about the new container
    container = {'container_id': container_id,
                 'name': container_details['Name'],
                 'image': container_details['Config']['Image'],
                 'status': RUNNING,
                 'active': 0}

    # Get new container's ports
    ports = get_container_ports(container_details['NetworkSettings']['Ports'])
    container.update(ports)

    r.hmset('containers:%s' % container_id, container)

    container_ip = container_details['NetworkSettings']['IPAddress']
    r.set('ips:%s' % container_ip, container_id)

    if not DISABLE_TIMEOUTS:
        check_container_activity.apply_async(
            args=(container_id,), countdown=INITIAL_TIMEOUT_INTERVAL)

    return container


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def stop_container(self, container_id):
    """Stops a container asynchronously."""
    delete_container_ip(container_id)

    try:
        client.stop(container_id)
    except APIError as exception:
        raise self.retry(exc=exception)

    r.hmset('containers:%s' % container_id, {
            'status': STOPPED, 'active': 0, 'ssh_port': '', 'app_port': ''})


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def remove_container(self, container_id):
    """Deletes a container asynchronously."""
    delete_container_ip(container_id)

    try:
        client.stop(container_id)
        client.remove_container(container_id)
    except APIError as exception:
        raise self.retry(exc=exception)

    r.delete('containers:%s' % container_id)


@celery.task
def check_container_activity(container_id, final=False):
    """Checks a container's activity.

    Containers configured for spin-docker activity monitoring regularly POST to
    the /check-in URL indicating whether they are active or not.

    If spin-docker is configured to check container activity, this celery task
    is scheduled when the container is started to check on the container after
    the INITIAL_TIMEOUT_INTERVAL setting. For each check after that, it uses the
    TIMEOUT_INTERVAL setting.

    The first time this task finds no container activity, it schedules itself
    for one last check after another TIMEOUT_INTERVAL. If there is still no
    activity, it stops the container.
    """
    container = r.hgetall('containers:%s' % container_id)
    if container and container['status'] == RUNNING:
        inactive = container['active'] == '0'

        if inactive:
            if final:
                stop_container.delay(container_id)
                return 'stopping container'
            else:
                check_container_activity.apply_async(
                    args=(container_id,), kwargs={'final': True, }, countdown=TIMEOUT_INTERVAL)
                return 'container inactive'
        else:
            check_container_activity.apply_async(
                args=(container_id,), countdown=TIMEOUT_INTERVAL)
            return 'container active'
