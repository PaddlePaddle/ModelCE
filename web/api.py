__all__ = [
    "CommitRecord",
    "TaskRecord",
    "KpiRecord",
]

import sys
sys.path.append('pypage')
sys.path.append('..')
import config
import json
from db import MongoDB
from datetime import datetime, timedelta
from kpi import Kpi

db = MongoDB(config.db_name)


class objdict(dict):
    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, item):
        return self[item]


class CommitRecord:
    def __init__(self, commit=''):
        self.commit = commit
        self.short_commit = ""
        self.date = None  # datetime
        self.info = ""

    @staticmethod
    def get_all():
        ''' Get all commit records, and sort by latest to oldest.  
        returns: list of CommitRecord
        '''
        # sort by 'date' in ascending order
        commits = db.find_sections(config.table_name, 
            {'type': 'kpi'}, {'commitid': 1, "_id": 0}, "date")
        commit_ids = []
        for commit in commits:
            if commit['commitid'] not in commit_ids:
                commit_ids.append(commit['commitid'])
        
        records = []
        for commit in commit_ids:
            commitobj = CommitRecord(commit)
            tasks = commitobj.get_commit_record()
            commitobj.commit = commit
            commitobj.shortcommit = commit[:7]
            commitobj.date = datetime.utcfromtimestamp(int(tasks[0]['date'])) + \
                            timedelta(hours=8)

            commitobj.passed = tasks_success(tasks)
            records.append(commitobj)

        return records

    def get_commit_record(self):
        ''' get the corresponding TaskRecords.
        returns: list of TaskRecord
        '''
        return db.finds(config.table_name,
                        {'type': 'kpi',
                         'commitid': self.commit})


class TaskRecord(objdict):
    def __init__(self, commit, name, infos, passed):
        self.name = name
        self.task = name
        # dict of KpiRecord
        self.kpis = []
        self.infos = infos
        self.passed = passed
        self.commitid = commit

    def get_task_info(self):
        ''' get the corresponding TaskRecord.
        returns: dict of TaskRecord'''
        return db.find_one(config.table_name, {'type': 'kpi', \
                          'commitid': self.commitid, 'task': self.name})

    @staticmethod
    def get_tasks(commit):
        ''' Get the task details belong to a commit from the database. '''
        record = CommitRecord(commit)
        tasks = record.get_commit_record()
        print (tasks)
        res = objdict()
        for task in tasks:
            taskobj = TaskRecord(commit, task['task'], task['infos'],
                                 task['passed'])
            taskobj.kpis = taskobj.get_kpi_details()
            res[taskobj.name] = taskobj
        return res

    def get_kpi_details(self):
        '''Transfrom a mongodb kpi record from lists to a python dict.'''
        task_info = self.get_task_info()
        kpi_infos = {}
        for kpi in task_info['kpis-keys']:
            kpiobj = KpiRecord(kpi)
            kpi_infos[kpi] = kpiobj.get_kpi_info_by_key(task_info)
        return kpi_infos


class KpiRecord:
    def __init__(self, name):
        self.name = name
        # list of list of float
        self.values = []
        self.type = ""
        self.avg = 0
        self.activeds = False
        self.unit = ""
        self.desc = ""

    def get_kpi_info_by_key(self, task_info):
        '''Get the kpi infos according to the kpi key'''
        for i in range(len(task_info['kpis-keys'])):
            if self.name == task_info['kpis-keys'][i]:
                break
        def safe_get_fields(field):
            if field in task_info:
                return task_info[field]
            return None
        #To keep the kpi datas in order, we should process the data one by one.
        kpi_vals = json.loads(task_info['kpis-values'])
        self.values = kpi_vals[i]
        self.type = task_info['kpi-types'][i]
        self.avg = '%.4f' % Kpi.dic.get(self.type).cal_kpi(data=kpi_vals[i])
        infos = parse_infos(task_info['infos'])
        self.info = infos[self.name]
        
        activeds = safe_get_fields('kpi-activeds')
        self.activeds = activeds[i] if activeds else True

        unit_reprs = safe_get_fields('kpi-unit-reprs')
        self.unit =  "(%s)" % unit_reprs[i] if unit_reprs else ""   

        descs = safe_get_fields('kpi-descs')        
        self.desc = descs[i] if descs else ""

        return (self.values, self.type, self.avg, self.info, self.activeds,
                self.unit, self.desc)


class objdict(dict):
    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, item):
        return self[item]


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
    for task in tasks:
        if not task['passed']: return False
    return True
