from flask import Flask
from flask_migrate import Migrate
from app.models import db
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Alternatively you can set environment variable "PYTHONPATH" to project root directory, eg. `export PYTHONPATH=./app`
#sys.path.append(os.getcwd())

HOST = os.environ.get('SERVER_HOST', 'localhost')
try:
    PORT = int(os.environ.get('SERVER_PORT', '5001'))
except ValueError:
    PORT = 5001

db_url = os.environ.get("CONNECT")
if db_url is None or db_url == "":
    raise ValueError("Environment Variable 'CONNECT' has to be set in the .env file")

app = Flask(__name__, instance_relative_config=True)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# Routes
from app.views import *
