import base64
import os
import unittest
import time

import redis
from docker import Client
from flask import json
from mock import Mock

# Disable timeouts for testing
CURRENT_DISABLE_TIMEOUTS = os.environ.get('DISABLE_TIMEOUTS')
os.environ['DISABLE_TIMEOUTS'] = 'True'

existing_containers = []

r = redis.StrictRedis(host='localhost', port=6379)
client = Client()

from spindocker import app
from spindocker.tasks import celery, check_container_activity

celery.conf.CELERY_ALWAYS_EAGER = True

class SpinDockerTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        for c in client.containers(all=True, quiet=True):
            existing_containers.append(c['Id'])
        r.flushall()

    @classmethod
    def tearDownClass(self):
        for c in client.containers(all=True, quiet=True):
            if c['Id'] not in existing_containers:
                client.kill(c['Id'])
                client.remove_container(c['Id'])

        if not CURRENT_DISABLE_TIMEOUTS:
            del os.environ['DISABLE_TIMEOUTS']

    def setUp(self):
        # Set HTTP basic authentication headers
        self.auth = {'Authorization': 'Basic ' + \
            base64.b64encode('admin' + ":" + os.environ['SPIN_DOCKER_PASSWORD'])}   
        self.app = app.test_client()

    def tearDown(self):
        r.flushall()

    def _get_containers(self):
        resp = self.app.get('/v1/containers', headers=self.auth)
        data = json.loads(resp.data)
        return data

    def _create_container(self, image='atbaker/sd-postgres'):
        resp = self.app.post('/v1/containers', 
            headers=self.auth,
            data={'image': image})
        data = json.loads(resp.data)
        return data

    def test_bad_authentication(self):
        resp = self.app.get('/v1/containers', 
            headers={'Authorization': 'Basic ' + \
            base64.b64encode('wrong' + ":" + 'user')})

        self.assertEqual(resp.status_code, 401)

    def test_no_authentication(self):
        resp = self.app.get('/v1/containers')

        self.assertEqual(resp.status_code, 401)

    def test_get_images(self):
        resp = self.app.get('/v1/images',
            headers=self.auth)     
        data = json.loads(resp.data)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('atbaker/sd-postgres:latest', data)

    def test_container_list_empty(self):
        data = self._get_containers()
        self.assertEqual(data, [])

    def test_container_list_one_container(self):
        container = self._create_container()

        data = self._get_containers()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], container)

    def test_container_list_multiple_containers(self):
        container_one = self._create_container()
        container_two = self._create_container()

        data = self._get_containers()

        self.assertEqual(len(data), 2)
        self.assertIn(container_one, data)
        self.assertIn(container_two, data)

    def test_create_container_bad_image_name(self):
        resp = self.app.post('/v1/containers',
            headers=self.auth, 
            data={'image': 'badimage'})
        data = json.loads(resp.data)

        self.assertEqual(500, resp.status_code)
        self.assertEqual('Image badimage not found on this server', data['message'])

    def test_container_get(self):
        container = self._create_container()
        container_id = container['container_id']

        resp = self.app.get('/v1/containers/%s' % container_id,
            headers=self.auth)
        data = json.loads(resp.data)

        self.assertEqual(container, data)
        self.assertIn('container_id', data.keys())
        self.assertIn('image', data.keys())
        self.assertIn('uri', data.keys())        
        self.assertIn('app_port', data.keys())
        self.assertIn('ssh_port', data.keys())
        self.assertIn('active', data.keys())

    def test_container_get_bad_container_id(self):
        self._create_container()
        bad_container_id = '1337'

        resp = self.app.get('/v1/containers/%s' % bad_container_id,
            headers=self.auth)
        data = json.loads(resp.data)

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(data['message'], "Container %s doesn't exist" % bad_container_id)

    def test_container_delete(self):
        container = self._create_container()
        container_id = container['container_id']

        resp = self.app.delete('/v1/containers/%s' % container_id,
            headers=self.auth)

        self.assertEqual(resp.status_code, 204)
        self.assertEqual(self._get_containers(), [])

    def test_container_stop(self):
        container = self._create_container()
        container_id = container['container_id']

        resp = self.app.patch('/v1/containers/%s' % container_id, 
            headers=self.auth,
            data=dict(status='stopped'))
        data = json.loads(resp.data)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['status'], 'stopping')

    def test_container_start(self):
        container = self._create_container()
        container_id = container['container_id']

        resp = self.app.patch('/v1/containers/%s' % container_id, 
            headers=self.auth,
            data=dict(status='stopped'))
        resp = self.app.patch('/v1/containers/%s' % container_id,
            headers=self.auth,
            data=dict(status='running'))
        data = json.loads(resp.data)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['status'], 'running')

    def test_container_start_already_running(self):
        container = self._create_container()
        container_id = container['container_id']

        resp = self.app.patch('/v1/containers/%s' % container_id,
            headers=self.auth,
            data=dict(status='running'))
        data = json.loads(resp.data)

        self.assertEqual(resp.status_code, 500)
        self.assertIn("Cannot start container %s" % container_id, data['message'])

    def test_container_audit_remove_container(self):
        container = self._create_container()
        container_id = container['container_id']

        client.kill(container_id)
        client.remove_container(container_id)

        resp = self.app.get('/v1/containers?audit=true',
            headers=self.auth)
        data = json.loads(resp.data)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data, [])

    def test_container_audit_stopped_container(self):
        container = self._create_container()
        container_id = container['container_id']

        client.stop(container_id)

        resp = self.app.get('/v1/containers?audit=true',
            headers=self.auth)
        data = json.loads(resp.data)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data[0]['status'], 'stopped')
        self.assertEqual(data[0]['ssh_port'], '')
        self.assertEqual(data[0]['app_port'], '')
        self.assertEqual(data[0]['active'], '0')

    def test_container_audit_started_container(self):
        container = self._create_container()
        container_id = container['container_id']

        resp = self.app.patch('/v1/containers/%s' % container_id,
            headers=self.auth,
            data=dict(status='stopped'))
        self.assertEqual(resp.status_code, 200)

        client.start(container_id)

        resp = self.app.get('/v1/containers?audit=true',
            headers=self.auth)
        data = json.loads(resp.data)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data[0]['status'], 'running')

    def test_check_activity_no_container(self):
        result = check_container_activity('bad_container_id')

        self.assertIsNone(result)

    def test_check_activity_not_running(self):
        container = self._create_container()
        container_id = container['container_id']

        resp = self.app.patch('/v1/containers/%s' % container_id,
            headers=self.auth,
            data=dict(status='stopped'))

        result = check_container_activity(container_id)

        self.assertIsNone(result)

    def test_check_activity_active_connections(self):
        container = self._create_container()
        container_id = container['container_id']
        r.hset('containers:%s' % container_id, 'active', '1')

        # Mock apply_async so we don't get stuck in infinite loop
        check_container_activity.apply_async = Mock()

        result = check_container_activity(container_id)

        self.assertEqual(result, 'container active')
        self.assertTrue(check_container_activity.apply_async.called)

    def test_check_activity_no_connections(self):
        container = self._create_container()
        container_id = container['container_id']

        result = check_container_activity(container_id)

        self.assertEqual(result, 'container inactive')

    def test_check_activity_no_connections_final(self):
        container = self._create_container()
        container_id = container['container_id']

        result = check_container_activity(container_id, final=True)

        self.assertEqual(result, 'stopping container')

    def test_check_in(self):
        container = self._create_container()
        container_id = container['container_id']

        self.app.post('/v1/check-in',
            headers=self.auth,
            data={'active': 1},
            environ_base={'REMOTE_ADDR': client.inspect_container(container_id)['NetworkSettings']['IPAddress'],})

        container_active = r.hget('containers:%s' % container_id, 'active')

        self.assertEqual(container_active, '1')

    def test_check_in_nonexistent_container(self):
        resp = self.app.post('/v1/check-in',
            headers=self.auth,
            data={'active': 1},
            environ_base={'REMOTE_ADDR': '127.0.0.99',})

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, '')

if __name__ == '__main__':
    unittest.main()
