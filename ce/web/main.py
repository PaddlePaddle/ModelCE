import os
import sys
from flask import (Flask, request, redirect, send_from_directory,
                   render_template, send_file)
from ce.web.view import FakeView
#from flask.ext.cache import Cache

SERVER_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
STATIC_DIR = os.path.join(SERVER_PATH, "html")
TEMPLATE_DIR = os.path.join(SERVER_PATH, "html")

app = Flask(
    "paddle-ce", static_url_path=STATIC_DIR, template_folder=TEMPLATE_DIR)


@app.route('/')
def index():
    return render_template('index.html', **FakeView.index())


@app.route('/report')
def report():
    return render_template('report.html', **FakeView.index())


@app.route('/')
def hello():
    return 'Hello, World!'


@app.route('/static/<path:path>')
def static_view(path):
    return send_from_directory(STATIC_DIR, path)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
