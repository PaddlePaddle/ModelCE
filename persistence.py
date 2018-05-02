'''
Use a mongodb to persist the status of this framework.
'''
from db import MongoDB
import config
import json

db = MongoDB(config.db_name)


def add_evaluation_record(commitid, date, task, passed, infos, kpis, kpi_types, actived):
    '''
    commitid: str
    date: UNIX timestamp
    task: str
    passed: bool
    infos: list of string
    '''
    # delete old task record for this commit
    db.remove(config.table_name,
              {'commitid': commitid,
               'type': 'kpi',
               'task': task,})

    # insert new record
    record = {
        'commitid': commitid,
        'date': date,
        'task': task,
        'type': 'kpi',
        'passed': passed,
        'infos': infos,
        'kpis-keys': list(kpis.keys()),
        'kpis-values': json.dumps(list(kpis[key].tolist() for key in kpis.keys())),
        'kpi-types': [kpi_types[key] for key in kpis.keys()],
        'actived': actived,
    }
    db.insert_one(config.table_name, record)
