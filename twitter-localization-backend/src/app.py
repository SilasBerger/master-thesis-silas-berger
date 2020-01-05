from flask import Flask
from src.api import Router
from flask_cors import CORS
from src.util import context

context.load_config("config_default.json")
context.load_credentials("credentials_default.json")

app = Flask(__name__)
CORS(app)

Router.route(app)

if __name__ == '__main__':
    app.run()
