#!/usr/bin/env xonsh
'''
some utils for clone repo, commit.
'''
import sys; sys.path.insert(0, '')
from utils import PathRecover
import config


def clone(url, dst):
    '''
    url: url of a git repo.
    dst: a abstract path in local file system.
    '''
    git clone @(url) @(dst)

def get_commit(local_repo_path, short=False):
    with PathRecover():
        cd @(local_repo_path)
        flags = '%h' if short else '%H'
        if short:
            commit = $(git log -1 --pretty=format:%h).strip()
        else:
            commit = $(git log -1 --pretty=format:%H).strip()
        return commit

def get_commit_date(local_repo_path):
    ''' get UNIX timestamp '''
    with PathRecover():
        cd @(local_repo_path)
        date = $(git log -1 --pretty=format:%ct)
        return date
