'''
Defines all the data structures in Python, it will make the database data operation easier.
'''

import json
import numpy as np
import pymongo
from ce.utils import dictobj, log, __check_type__
from ce.config_util import Config
from ce.db import MongoDB
from ce.environ import Environ


class DB(MongoDB):
    def __init__(self, test=False):
        config = Config.Global(Environ.config())
        super().__init__(
            host=config.get('database', 'host'),
            port=config.get_int('database', 'port'),
            db=config.get('database', 'id'),
            test=Environ.test_mode() if test is not None else test)


shared_db = DB()

log.info = print
log.warn = print


def init_shared_db(test=None):
    global shared_db
    if not shared_db:
        config = Config.Global()
        shared_db = MongoDB(
            host=config.get('database', 'host'),
            port=config.get_int('database', 'port'),
            db=config.get('database', 'id'),
            test=Environ.test_mode() if test is not None else test)


def parse_mongo_record(record):
    '''
    Combine MongoDB record infomation with the JSON serialized dict.
    :param record: dict, which is a MongoDB record with a 'json' field.
    :return: dictobj
    '''
    assert 'json' in record
    assert 'date' in record
    info = json.loads(record['json'])
    info.update({'date': record['date']})
    return dictobj(info)


class DataStruct:
    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return str(self.data)


class Commit(DataStruct):
    def __init__(self, commitid, tasks=[], state='running', data=None):
        '''
        :param commitid: str
            long commit id.
        :param date: None
        :param tasks: list of str
            names of tasks.
        :param state: running/fail/success
        '''
        if data:
            self.data = dictobj(data)
        else:
            self.data = dictobj()
            self.data.commitid = commitid
            self.data.tasks = tasks
            self.data.state = state

        self.record_id = self.gen_record_id(commitid)

    def persist(self, update=False):
        init_shared_db()
        message = json.dumps(self.data)
        if not update:
            log.info('persist', self.record_id, message)
            assert shared_db.set(self.record_id, message, table='commit')
        else:
            log.info('update', self.record_id, message)
            shared_db.update(self.record_id, message, table='commit')
        return self.record_id

    def fetch_info(self):
        '''
        Fetch the commit infomation.
        :return: self
        '''
        init_shared_db()

        message = shared_db.get(self.record_id, table='commit')
        assert message, 'no record called %s' % self.record_id
        self.data = parse_mongo_record(message)

    def fetch_tasks(self):
        '''
        :return: list of Task
        '''
        assert self.data.tasks, 'fetch_info first'
        tasks = []
        for task in self.data.tasks:
            info = shared_db.get(Task.gen_record_id(self.data.commitid, task),
                                 table='task')
            if info:
                info = parse_mongo_record(info)
                task = Task()
                task.data = info
                tasks.append(task)
        return tasks

    @staticmethod
    def gen_record_id(commitid):
        __check_type__.match_str(commitid)
        assert commitid
        return '<commit>/%s' % commitid

    @staticmethod
    def fetch_all():
        init_shared_db()
        infos = shared_db.gets({}, table='commit')
        return [Commit(json.loads(info['value']))
                for info in infos] if infos else []


class Task(DataStruct):
    def __init__(self, commitid='', name='', kpis=[], env_desc='', data=None):
        __check_type__.match_str(commitid, name, env_desc)
        __check_type__.match_list(kpis)
        if data:
            self.data = dictobj(data)
        else:
            self.data = dictobj()
            self.data.name = name
            self.data.commitid = commitid
            # Execution environment.
            self.data.env_desc = env_desc
            # list of Kpi
            self.data.kpis = kpis

    @property
    def record_id(self):
        assert self.data.commitid
        assert self.data.name
        return Task.gen_record_id(self.data.commitid, self.data.name)

    def persist(self):
        init_shared_db()
        message = json.dumps(self.data)
        log.info('persist', self.record_id, message)
        shared_db.set(self.record_id, message, table='task')
        return self.record_id

    def fetch_info(self):
        init_shared_db()
        info = shared_db.get(self.record_id, table='task')
        log.info('task info', info)
        assert info
        self.data = parse_mongo_record(info)
        return self.data

    def fetch_kpis(self):
        '''
        :return: list of KPI.
        '''
        init_shared_db()

        assert self.data.kpis, "fetch_info first"
        kpi_ids = [
            Kpi.gen_record_id(self.data.commitid, self.data.name, kpi)
            for kpi in self.data.kpis
        ]
        # TODO(Superjomn) search multiple records in one time.
        res = []
        for kpi_id in kpi_ids:
            record = shared_db.get(kpi_id, table='kpi')
            if record:
                kpi = Kpi(data=dictobj(json.loads(record['json'])))
                res.append(kpi)
        return res

    @staticmethod
    def fetch_all():
        init_shared_db()
        infos = shared_db.gets({}, table="task")
        return [Task(data=json.loads(info['json']))
                for info in infos] if infos else []

    @staticmethod
    def gen_record_id(commitid, task):
        '''
        :param commitid: str
        :param task: str
        :return: str
        '''
        __check_type__.match_str(commitid, task)
        return "<task>/%s/%s" % (commitid, task)


class Kpi(DataStruct):
    '''
    KPI data view.
    '''

    def __init__(self,
                 commitid='',
                 task='',
                 name='',
                 unit='',
                 short_description='',
                 description='',
                 kpi_type='',
                 value=None,
                 actived=False,
                 passed=None,
                 logs='',
                 data=None):
        '''
        :param commitid: str
        :param task: str
        :param name: str
        :param unit: str
        :param short_description: str
        :param description: str
        :param kpi_type: str
        :param value: any type
        :param actived: bool
        :param passed: bool
        :param logs: str
        :param data: str
        '''
        __check_type__.match_str(commitid, task, name, unit, short_description,
                                 description, kpi_type, logs)
        __check_type__.match_bool(actived)
        __check_type__.match_bool_or_none(bool(passed))

        if data:
            self.data = dictobj(data)
        else:
            self.data = dictobj()
            self.data.commitid = commitid
            self.data.task = task
            # str
            self.data.name = name
            self.data.kpi_type = kpi_type
            # int or bool
            self.data.value = value
            self.data.unit = unit
            self.data.short_description = short_description
            self.data.description = description
            self.data.actived = actived
            self.data.passed = passed
            self.data.logs = logs

    def set_value(self, val):
        '''
        Set the value of the kpi
        :param val: any kind
        :return: None
        '''
        self.data.value = val

    def fetch_infos(self):
        data = shared_db.get(self.record_id, table='kpi')
        assert data, 'no KPI record which key is %s' % self.record_id

        self.data = dictobj(json.loads(data['json']))
        # restore bool
        for key in ["actived", "passed"]:
            self.data[key] = True if self.data[key] == 1 else False
        return self.data

    @staticmethod
    def fetch_all():
        infos = shared_db.gets({}, table="kpi")
        return [Kpi(info['json']) for info in infos] if infos else []

    @property
    def record_id(self):
        return self.gen_record_id(self.data.commitid, self.data.task,
                                  self.data.name)

    def persist(self):
        for key, item in self.data.items():
            if isinstance(
                    type(item),
                    bool) or type(item) is np.bool or type(item) is np.bool_:
                self.data[key] = 1 if item else 0
        message = json.dumps(self.data)
        log.info('persist', self.record_id, message)
        shared_db.set(self.record_id, message, table='kpi')
        return self.record_id

    @staticmethod
    def gen_record_id(commitid, task, kpi):
        __check_type__.match_str(commitid, task, kpi)
        assert commitid
        assert task
        assert kpi
        return "<kpi>/%s/%s/%s" % (commitid, task, kpi)


class KpiBaseline:
    @staticmethod
    def update(task, kpi, value, comment=''):
        '''
        Update the KPI.
        :param task: str
        :param kpi: str
        :param value: any type
        :param comment: str
        :return: any type
        '''
        __check_type__.match_str(task, kpi)
        key = '%s/%s' % (task, kpi)
        value = json.dumps({'kpi': value})
        return shared_db.set(key, value, table='baseline')

    @staticmethod
    def get(task, kpi):
        '''
        Get latest record.
        :param task: str
        :param kpi: str
        :return: kpi.
        '''
        __check_type__.match_str(task, kpi)
        key = '%s/%s' % (task, kpi)
        res = shared_db.get(key,
                            table='baseline',
                            sort=[('_id', pymongo.DESCENDING)])
        return parse_mongo_record(res)['kpi'] if res else None
