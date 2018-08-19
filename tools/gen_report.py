#!/usr/bin/env python
#coding: utf-8
################################################################################
#
# Copyright (c) 2017 Baidu.com, Inc. All Rights Reserved
#
################################################################################
"""
This class is used to run remote command

Authors: guochaorong(guochaorong@baidu.com)
Date: 2018/07/11
"""

import sys
sys.path.append('pypage')
sys.path.append('..')
import config
import json
import time
from db import MongoDB
from datetime import datetime, timedelta
from kpi import Kpi

db = MongoDB(config.db_name)
from web.api import CommitRecord
from html import Html
from datetime import datetime
period = 7

def gettimestamp(dd_str):
    timeArray = time.strptime(dd_str+" 00:00:00", "%Y-%m-%d %H:%M:%S")
    timeStamp = int(time.mktime(timeArray))
    return timeStamp

def get_target_commits(records):
    need_commit = []
    for record in records:
        print (record.date)
        begin = datetime.now() - timedelta(days=period)
        print (begin)
        if record.date > begin:
            need_commit.append(record)
    return need_commit


def get_all_tasks(need_commit):
    print (need_commit)
    all_tasks = {}
    for commit in need_commit:
        tasks = CommitRecord.get_tasks(commit.commit)
        if not all_tasks:
            for task in tasks:
                all_tasks[task]={}
        for task, values in tasks.items():
            res = ''
            for k, v in values['kpis'].items():
                if k not in all_tasks[task].keys():
                    all_tasks[task][k] = 0
                if v[3] == 'pass':
                    res += "%s\t%s\t<br>" %(k, v[3])
                    #print (res)
                else:
                    res += "%s\tfailed\t<br>" %(k)
                    print ("%%%%%%")
                    print (res)
                    all_tasks[task][k] += 1
        return all_tasks

def gen_html(all_tasks):
    hh = Html()
    hh.html_create(period)
    for task, values in all_tasks.items():
        print ("*********")
        print (task)
        res = ''
        for k, v in values.items():
            print ("%s\t%s" %(k, v))
            if v == 0:
                res += "%s&emsp;\tpass\t<br>" %(k)
            else:
                res += '''%s&emsp;\tfailed times: <font color="blue">%s</font>\t<br>''' %(k, v)
        hh.html_add_param(task, res, task)

if __name__ == '__main__':
    records = CommitRecord.get_all()
    #today = datetime.now().strftime("%Y-%m-%d")

    need_commits = get_target_commits(records)
    all_tasks = get_all_tasks(need_commits)
    gen_html(all_tasks)
