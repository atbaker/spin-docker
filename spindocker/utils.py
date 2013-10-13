from docker import Client

import redis

r = redis.StrictRedis(host='localhost', port=6379)
client = Client()

# Status constants
RUNNING = 'running'
STOPPED = 'stopped'
STOPPING = 'stopping'
