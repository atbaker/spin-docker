from docker import APIError
from flask import request
from flask.ext.httpauth import HTTPBasicAuth
from flask.ext.restful import reqparse, abort, Resource, fields, marshal, types
from spindocker.tasks import audit_containers, start_container, stop_container, remove_container
from spindocker.utils import r, client, RUNNING, STOPPED, STOPPING

from spindocker import app, api

import os

auth = HTTPBasicAuth()

users = {
    "admin": os.environ['SPIN_DOCKER_PASSWORD'],
}

@app.before_first_request
def startup_audit():
    audit_containers()

@auth.get_password
def get_pw(username):
    """Returns the password specified in 'SPIN_DOCKER_PASSWORD'."""
    if username in users:
        return users[username]
    return None

container_fields = {
    'container_id': fields.String,
    'name': fields.String,
    'image': fields.String,
    'ssh_port': fields.String,
    'app_port': fields.String,
    'status': fields.String,
    'active': fields.String,
    'uri': fields.Url('container'),
}


def abort_if_container_doesnt_exist(container_id):
    """Checks that a container is found before proceeding with a request."""
    if not r.exists('containers:%s' % container_id):
        abort(404, message="Container %s doesn't exist" % container_id)


class ImageList(Resource):
    decorators = [auth.login_required, ]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(ImageList, self).__init__()

    def get(self):
        """Gets a list of all tagged images for the /images endpoint."""
        images = []

        for image in client.images():
            if image['RepoTags'] != [u'<none>:<none>']:
                images += image['RepoTags']

        return images


class ContainerList(Resource):
    decorators = [auth.login_required, ]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(ContainerList, self).__init__()

    def get(self):
        """Returns all containers for the /containers endpoint."""
        self.reqparse.add_argument('audit', type=types.boolean, default=False,)
        args = self.reqparse.parse_args()

        if args['audit']:
            audit_containers()

        containers = []
        for container in r.keys('containers:*'):
            containers.append(r.hgetall(container))

        return [marshal(c, container_fields) for c in containers]

    def post(self):
        """Creates a new container based on a POST to /containers."""
        self.reqparse.add_argument(
            'image', type=str, required=True, help='Image cannot be blank')
        args = self.reqparse.parse_args()

        # Check that image exists
        try:
            image = client.inspect_image(args['image'])
        except APIError:
            abort(500, message="Image %s not found on this server" %
                  args['image'])

        if not image['container_config']['ExposedPorts']:
            abort(500, message="This image does not expose any ports. \
                Use the EXPOSE command in your dockerfile to specify some.")

        # Create and start the container
        try:
            result = client.create_container(image=args['image'],
                                             detach=True,
                                             )
            container_id = result['Id']
            container = start_container(container_id)
        except APIError as exception:
            abort(500, message=exception.explanation)

        return marshal(container, container_fields), 201


class Container(Resource):
    decorators = [auth.login_required, ]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('status', type=str)
        super(Container, self).__init__()

    def get(self, container_id):
        """Returns information about a single container."""
        abort_if_container_doesnt_exist(container_id)
        container = r.hgetall('containers:%s' % container_id)
        return marshal(container, container_fields)

    def patch(self, container_id):
        """Updates information on a single container. Currently just status."""
        args = self.reqparse.parse_args()

        if 'status' in args:
            if args['status'] == STOPPED:
                stop_container.delay(container_id)
                r.hset('containers:%s' % container_id, 'status', STOPPING)
            elif args['status'] == RUNNING:
                try:
                    start_container(container_id)
                except APIError as exception:
                    abort(500, message=exception.explanation)

        container = r.hgetall('containers:%s' % container_id)
        return marshal(container, container_fields)

    def delete(self, container_id):
        """Stops and deletes a single container."""
        abort_if_container_doesnt_exist(container_id)
        remove_container.delay(container_id)
        return '', 204

# Setup the Api resource routing here
api.add_resource(ImageList, '/v1/images', endpoint='images')
api.add_resource(ContainerList, '/v1/containers', endpoint='containers')
api.add_resource(
    Container, '/v1/containers/<string:container_id>', endpoint='container')


@app.route('/v1/check-in', methods=['POST'])
def check_in():
    """Processes activity reports from the containers."""
    active = request.form['active']
    container_ip = request.remote_addr
    container_id = r.get('ips:%s' % container_ip)
    if container_id is not None:
        r.hset('containers:%s' %
               container_id, 'active', active)
    return ''
