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

SERVER_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
STATIC_DIR = os.path.join(SERVER_PATH, "static")
TEMPLATE_DIR = os.path.join(SERVER_PATH, "template")

app = Flask(
    "modelce", static_url_path=STATIC_DIR, template_folder=TEMPLATE_DIR)
cache = Cache(
    app, config={
        'CACHE_TYPE': 'filesystem',
        'CACHE_DIR': './_cache'
    })
db = MongoDB(config.db_name)


@app.route('/')
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
def commit_details():
    commit = request.args.get('commit')

    page, snips = build_commit_detail_page()

    logics = snips[0].logic(commit)
    return render_template_string(page, **logics)


@app.route('/commit/compare', methods=["GET"])
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
    print('page', page)
    logics = merge_logics(select_snip.logic(), result_snip.logic(cur, base))
    return render_template_string(page, **logics)


if __name__ == '__main__':
    host = '0.0.0.0'
    port = 8020
    app.run(debug=True, host=host, port=port)
