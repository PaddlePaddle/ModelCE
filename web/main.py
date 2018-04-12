import os
import sys
from flask import Flask, request, redirect, send_from_directory, render_template
from flask.ext.cache import Cache
sys.path.append('..')
from db import MongoDB
from datetime import datetime, timedelta
import config
import json
import pprint
from kpi import Kpi

SERVER_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
STATIC_DIR = os.path.join(SERVER_PATH, "static")
TEMPLATE_DIR = os.path.join(SERVER_PATH, "template")

app = Flask(
    "modelce", static_url_path=STATIC_DIR, template_folder=TEMPLATE_DIR)
cache = Cache(
    app, config={'CACHE_TYPE': 'filesystem',
                     'CACHE_DIR': './_cache'})
db = MongoDB(config.db_name)


#@cache.cached(timeout=60)
@app.route('/')
def search():
    #db = MongoDB(config.db_name)
    # get commits
    records = db.finds(config.table_name, {'type': 'kpi'})
    records_ = []
    commit_set = set()
    for rcd in records:
        if rcd['commitid'] not in commit_set:
            commit_set.add(rcd['commitid'])
            rcd_ = objdict()
            rcd_.commit = rcd['commitid']
            rcd_.shortcommit = rcd['commitid'][:7]
            rcd_.date = datetime.utcfromtimestamp(int(rcd['date'])) + \
                            timedelta(hours=8)
            records_.append(rcd_)

    # get infos of the latest kpi
    latest_commit = records_[-1].commit
    task_kpis = db.finds(config.table_name, {'type':'kpi', 'commitid':latest_commit})
    task_kpis = wrap_rcd(task_kpis)

    latest_kpi = objdict()
    latest_kpi.commit = latest_commit
    latest_kpi.passed = tasks_success(task_kpis)
    latest_kpi.kpis = task_kpis

    records_ = [v for v in reversed(records_)]
    return render_template('pypage-search.html', records=records_, latest_kpi=latest_kpi)


#@cache.cached(timeout=60)
@app.route('/kpi/compare', methods=["GET"])
def kpi_compare():
    cur = request.args.get('cur')
    base = request.args.get('base')
    cur_rcds = db.finds(config.table_name, {'type':'kpi', 'commitid':cur})
    base_rcds = db.finds(config.table_name, {'type':'kpi', 'commitid':base}) 

    cur_tasks, base_rcds = wrap_rcd(cur_rcds), wrap_rcd(base_rcds)

    # get ratios
    res = []
    for name in cur_tasks.keys():
        print('task',name)
        cur_task = cur_tasks.get(name, None)
        base_task = base_rcds.get(name, None)
        # if eithor do not have some task, skip it.
        if not (cur_task or base_task): continue

        record = objdict()
        res.append(record)
        record.name = name
        record.kpis = []
        for kpi in cur_task.kpis.keys():
            print('kpi', kpi)
            cur_kpi = cur_task.kpis.get(kpi, None)
            base_kpi = base_task.kpis.get(kpi, None)
            if not (cur_kpi or base_kpi): continue
            kpi_ = objdict()
            kpi_type = Kpi.dic.get(cur_kpi[1])

            kpi_.name = kpi
            kpi_.ratio = kpi_type.compare_with(cur_kpi[0], base_kpi[0]) * 100. # get a percentage
            record.kpis.append(kpi_)

    return render_template(
            'pypage-kpi.html', cur_commit = cur[:7], base_commit = base[:7], tasks = res)

def wrap_rcd(rcds):
    '''
    rcds: records from MongoDB.
    '''
    tasks = {}
    for rcd in rcds:

        task = objdict()
        task.name = rcd['task']
        task.passed = rcd['passed']
        kpi_vals = json.loads(rcd['kpis-values'])
        task.kpis = {}
        infos = parse_infos(rcd['infos'])
        for i in range(len(rcd['kpis-keys'])):
            kpi_type = Kpi.dic.get(rcd['kpi-types'][i])
            kpi = rcd['kpis-keys'][i]
            task.kpis[kpi] = (
                    kpi_vals[i], 
                    rcd['kpi-types'][i],
                    '%.4f' % kpi_type.cal_kpi(data=kpi_vals[i]),
                    infos[kpi],)
        task.infos = rcd['infos']
        tasks[task.name] = task
    return tasks

def tasks_success(rcds):
    for rcd in rcds.values():
        print('rcd', rcd)
        if not rcd['passed']: return False
    return True

def parse_infos(infos):
    '''
    input format: [kpi0] xxxx [kpi1] xxx

    return dic of (kpi, info)
    '''
    res = {}
    for info in infos:
        lb = info.find('[') + 1
        rb = info.find(']', lb)
        kpi = info[lb:rb]
        info = info[rb+2:]
        res[kpi] = info
    return res


class objdict(dict):
    def __setattr__(self, key, value):
        self[key] = value
    def __getattr__(self, item):
        return self[item]


if __name__ == '__main__':
    host = '0.0.0.0'
    port = 8020
    app.run(debug=False, host=host, port=port)
