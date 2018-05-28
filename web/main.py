import os
import sys
from flask import Flask, request, redirect, send_from_directory, render_template_string
from flask.ext.cache import Cache
sys.path.append('..')
from db import MongoDB
from datetime import datetime, timedelta
import config
import json
import pprint
from kpi import Kpi
from view import *
import pyecharts

SERVER_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
STATIC_DIR = os.path.join(SERVER_PATH, "static")
TEMPLATE_DIR = os.path.join(SERVER_PATH, "template")

app = Flask(
    "modelce", static_url_path=STATIC_DIR, template_folder=TEMPLATE_DIR)
cache = Cache(
    app, config={'CACHE_TYPE': 'filesystem',
                 'CACHE_DIR': './_cache'})
db = MongoDB(config.db_name)


@app.route('/')
@cache.cached(timeout=120)
def index():
    '''
    Show the status, the contents:

    a list of commitids and their status(passed or not, the info)
    '''
    page, snips = build_index_page()
    commits = get_commits()
    latest_commit = commits[-1].commit
    logics = merge_logics(snips[0].logic(), snips[1].logic(latest_commit))
    print('commits', snips[0].logic())
    return render_template_string(page, **logics)


@app.route('/commit/details', methods=["GET"])
@cache.cached(timeout=120)
def commit_details():
    commit = request.args.get('commit')

    page, snips = build_commit_detail_page()

    logics = snips[0].logic(commit)
    return render_template_string(page, **logics)


@app.route('/commit/compare', methods=["GET"])
@cache.cached(timeout=120)
def commit_compare():
    if 'cur' not in request.args:
        commits = get_commits()
        latest_commit = commits[-1]
        success_commits = [v for v in filter(lambda r: r.passed, commits)]
        latest_success_commit = success_commits[
            -1] if not latest_commit.passed else success_commits[-2]
        cur = latest_commit.commit
        base = latest_success_commit.commit
    else:
        cur = request.args.get('cur')
        base = request.args.get('base')

    page, (select_snip, result_snip) = build_compare_page()
    logics = merge_logics(select_snip.logic(), result_snip.logic(cur, base))
    return render_template_string(page, **logics)

#@cache.cached(timeout=120)
@app.route('/commit/draw_scalar', methods=["GET"])
def draw_scalar():
    task_name = request.args['task']

    page, (scalar_snap,) = build_scalar_page(task_name)
    logics = merge_logics(scalar_snap.logic())
    return render_template_string(page, **logics)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='CE Web')
    parser.add_argument('--port', type=int, default=80, required=False,
                    help='web service port')

    parser.add_argument('--host', type=str, default='0.0.0.0', required=False,
                    help='web service host')
    args = parser.parse_args()
    app.run(debug=True, host=args.host, port=args.port, threaded=True)
