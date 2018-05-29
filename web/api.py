import sys
sys.path.append('pypage')
sys.path.append('..')
import config
import json
from db import MongoDB
from datetime import datetime, timedelta
from kpi import Kpi


db = MongoDB(config.db_name)

#TUDO: use multi tables in case of the table grows too big
class KpiRecord:
    def __init__(self):
        self.table = "kpi"
        self.name = None
        self.values = None
        self.type = None
        self.desc = None
        self.unit = None

        
#TUDO: use multi tables in case of the table grows too big
class TaskRecord:
    def __init__(self):
        self.table = "task"
        self.name = None
        self.kpis = []
        

class DetailRecord:
    '''the table contails all of the records'''
    '''an example for a record'''
    '''
	'kpis-keys': ['train_acc_top5_kpi', 'train_cost_kpi', 'train_acc_top1_kpi'],
	'infos': ['[train_acc_top1_kpi] failed, diff ratio: 0.9903790649141825 larger than 0.2.', '[train_acc_top5_kpi] failed, diff ratio: 0.9519000944325955 larger than 0.2.', '[train_cost_kpi] failed, diff ratio: 1.3212285037874993 larger than 0.2.'],
	'date': '1524828005',
	'passed': False,
	'kpi-activeds': [True, True, True],
	'kpis-values': '[[[0.02606865204870701]], [[6.907755374908447]], [[0.0032383420038968325]]]',
	'kpi-descs': [None, None, None],
	'type': 'kpi',
	'kpi-types': ['LessWorseKpi', 'GreaterWorseKpi', 'LessWorseKpi'],
	'kpi-unit-reprs': [None, None, None],
	'commitid': '6e0b47b38c653a383ac2e7d16453536205e15f2d',
	'task': 'image_classification',
	'_id': ObjectId('5ae92ad31bebb5a990cc53f0')
}
    '''

    def __init__(self, task='', commitid=''):
        self.table = "logs"
        self.id = None
        self.task = task
        self.date = None
        self.commitid = commitid
        self.task = None
        self.kpi_types = []
        self.kpi_keys = []
        self.kpi_values = []
        self.kpi_infos = []
        self.kpi_unit_reprs = []
        self.kpi_desc = []
        self.kpi_activeds = []
        self.passed = False
        self.type = 'kpi'

    def get_all_records(self):
        return  db.finds(self.table, {'type': 'kpi'})

    def get_records_by_commit(self):
        return db.finds(self.table, {'type': 'kpi', 'commitid': self.commitid})    

  
def query_commit_from_details(commit):
    ''' Get the task details belong to a commit from the database. '''
    details = DetailRecord(commitid=commit)
    tasks = details.get_records_by_commit()
    res = objdict()
    for task in tasks:
        task = db_task_record_to_py(task)
        task['task'] = task.name
        res[task.name] = task
    return res        


def query_all_commits_from_details():
    ''' get all the commits '''
    details = DetailRecord()
    records = details.get_all_records()
    print (records)
    # detact whether the task is passed.
    commits = {}
    for task in records:
        rcd = db_task_record_to_py(task)
        commits.setdefault(rcd.commitid, {})[rcd.name] = rcd

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
            rcd_.passed = tasks_success(commits[rcd_.commit])
            records_.append(rcd_)

    return records_ 


class objdict(dict):
    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, item):
        return self[item]


def db_task_record_to_py(task_rcd):
    ''' Transfrom a mongodb task record to python record. All the fields should be
    transformed.'''
    task = objdict(
        name=task_rcd['task'],
        passed=task_rcd['passed'],
        commitid=task_rcd['commitid'], )

    def safe_get_fields(field):
        if field in task_rcd:
            if type(task_rcd[field]) == list:
               return task_rcd[field]
            else:
                return json.loads(task_rcd[field])
        return None

    kpi_vals = json.loads(task_rcd['kpis-values'])
    task.kpis = {}
    infos = parse_infos(task_rcd['infos'])
    activeds = safe_get_fields('kpi-activeds')

    unit_reprs = safe_get_fields('kpi-unit-reprs')

    descs = safe_get_fields('kpi-descs')

    for i in range(len(task_rcd['kpis-keys'])):
        kpi_type = Kpi.dic.get(task_rcd['kpi-types'][i])
        kpi = task_rcd['kpis-keys'][i]
        task.kpis[kpi] = (
            # kpi details
            kpi_vals[i],
            # type
            task_rcd['kpi-types'][i],
            # kpi
            '%.4f' % kpi_type.cal_kpi(data=kpi_vals[i]),
            # info
            infos[kpi],
            # actived
            activeds[i] if activeds else True,
            # unit repr
                "(%s)" % unit_reprs[i] if unit_reprs else "",
            # desc
            descs[i] if descs else "", )
    task.infos = task_rcd['infos']
    return task


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
        info = info[rb + 2:]
        res[kpi] = info
    return res


def tasks_success(tasks):
    for task in tasks.values():
        if not task['passed']: return False
    return True
