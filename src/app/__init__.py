from flask import Flask
from flask_migrate import Migrate
from app.models import db
import os
from dotenv import load_dotenv

load_dotenv()

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

Flask.secret_key = "Ur0QxraCXGWZ37JzckYXxSJ9A8NIECUvvEKPADwPzy4w8Mc5YlHXoybq6YtM8SSKrIBi5rLmQqRJx8H9zDMJilZ5bvhKgJNO5xxUPXeu5I2gCGLEUaeiBhCLY7o5f0QsyuByoe9edXx23iAEZjrqcmhGNYFeUEytPtRuXmjyYBcpBxdN3FPjFpqFft6f7ckGLlkb8sKORlDNZDqWw4pIkgRAcP5q01diH08L14RtF1ZdxevZquHvn6iuglBMkkVhiEOh3VB4P5w4kW2SR7d2ZVobzUMK7XdP6UnfOkwh5oKW5qZW5DFUYLdx8eyYckk71pkVUbhMBJDNFMEG46SZUs8DEAqb8tzVsrNpQJKdzWA9kaNXrMyx6zXFcmun7PaBhmTRtN8IZ6V8eQZYjHQFIbag2dqYshkhM3ZQrp3SxS2Sdo8cKiV9CPZHRsYVMmqwMabDLaUgUnbI96mByz6WDxSaFZNR3IZfLBXjLo4uuiuokf2H2WVXt6mxDTbb04jkkkZcx8nt6gr4henp5uAp1VaMQt6s5Ucw1SYrlbTKPtpDEaoiAjKqXSXnW8bTTXVXNPI6VNiwqAR7eY4Okh0Nv8KXbsNtztGwmpwIWQxBpyWS13o4P2X7I74utiDMW0dmUKbp5n5vhAkFHdGMEyS6si0fX3tNbgY55rUH3qGuaIjctnlLbHU7AdFKHnPWwrUCCYSsWrM4Ugow49c5Db5R7zax7CkzdA3xo3VYvs0vN5KD32QmyaybAaH5COYYOSsd4ToQhqcbzXFkrx1DHqdGwJ7TurSlpsDSIexso4OKf5GVqcVb9LEvJCgX2bEsCG6iVztZ7QAA152JvigQRwJAyEZMUJ9FWJxQ9HkUcaBxDwYB5Mwk931QZP0ET7kiIQYD3v8Kbt9zNVwSpLlF4PpeletaViS5hhufZQ1w9AmyDejCj6DcwIYmzeree92FIiXXSWYwvXsFWikSZUdXEo6zagi18j9ZSgMjGbQuL58Z5obqQCRmnSb1mrbt0Jb3Cjlo"

db.init_app(app)
migrate = Migrate(app, db)

# Routes
from app.views import *
