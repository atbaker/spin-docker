from flask import Flask
from flask.ext.restful import Api

app = Flask(__name__)
api = Api(app)

import spindocker.views
