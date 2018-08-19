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
            tasks = commitobj.__get_db_record()
            commitobj.commit = commit
            commitobj.shortcommit = commit[:7]
            commitobj.date = datetime.utcfromtimestamp(int(tasks[0]['date'])) + \
                            timedelta(hours=8)

            commitobj.passed = tasks_success(tasks)
            records.append(commitobj)
        return records

    @staticmethod
    def get_tasks(commit):
        ''' Get the task details belong to a commit. 
        returns:  dict of TaskRecord
                     keys: task name,
                     values: TaskRecord '''
        record = CommitRecord(commit)
        tasks = record.__get_db_record()
        print (tasks)
        res = objdict()
        for task in tasks:
            taskobj = TaskRecord(commit, task['task'], task['infos'],
                                 task['passed'])
            taskobj.kpis = taskobj.get_kpis()
            res[taskobj.name] = taskobj
        return res

    def __get_db_record(self):
        ''' get the corresponding tasks from database.
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

    def get_kpis(self):
        '''Get kpis details belong to a task.
        returns dict of KpiRecord
                    keys: kpi name,
                    values: KpiRecord'''
        task_info = self.__get_db_record()
        kpi_infos = {}
        for kpi in task_info['kpis-keys']:
            kpiobj = KpiRecord(kpi)
            kpi_infos[kpi] = kpiobj.get_kpi_info(task_info)
        return kpi_infos

    def __get_db_record(self):
        ''' get the corresponding kpis from database'''
        return db.find_one(config.table_name, {'type': 'kpi', \
                          'commitid': self.commitid, 'task': self.name})

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

    def get_kpi_info(self, task_info):
        '''Get the kpi infos according to the kpi name'''
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
        descs = safe_get_fields('kpi-descs')

        self.unit =  "(%s)" % unit_reprs[i] if unit_reprs else ""
        self.desc = descs[i] if descs else ""

        self.set_infos()

        return (self.values, self.type, self.avg, self.info, self.activeds,
                self.unit, self.desc)

    def set_infos(self):
        #key = ['acc', 'cost', 'loss', 'speed', 'memory', 'duration', 'ppl']
        types = ['train', 'test']
        for t in types:
            if '_acc' in self.name and t in self.name:
                if not self.desc:
                    self.desc = '%s accuracy, 0 to 1' % t
                if self.unit == "(None)":
                    self.unit = '(100%)'
            elif 'cost' in self.name and t in self.name:
                if not self.desc:
                    self.desc = '%s loss function value' % t
                if self.unit == "(None)":
                    self.unit = '(100%)'
            elif 'speed' in self.name and t in self.name:
                if not self.desc:
                    self.desc = '%s speed ' % t
                if self.unit == "(None)":
                    self.unit = '(images/s)'
            elif 'gpu_memory' in self.name:
                if not self.desc:
                    self.desc = 'gpu memory usage'
                if self.unit == "(None)":
                    self.unit = '(MiB)'
            elif 'duration' in self.name:
                if not self.desc:
                    self.desc = 'time takes for exec'
                if self.unit == "(None)":
                    self.unit = '(s)'
            elif 'ppl' in self.name and t in self.name:
                if not self.desc:
                    self.desc = 'the ppl of %s ' % t


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
