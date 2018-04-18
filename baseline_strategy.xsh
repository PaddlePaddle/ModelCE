#!/usr/bin/env xonsh
$RAISE_SUBPROC_ERROR = True
$XONSH_SHOW_TRACEBACK = True
'''
Some stragegies define how to update the baseline.
'''
import sys; sys.path.insert(0, '')
import config
import repo
from utils import *

class Strategy(object):
    ''' The bese class for all strategies. '''

    def __call__(self):
        log.warn('running baseline strategy')
        if self.evaluation_passed():
            self.update_baseline()
        else:
            self.store_failed_kpis()

    def refresh_workspace(self):
        ''' git checkout -b develop origin/master. '''
        raise NotImplementedError

    def evaluation_passed(self):
        ''' Whether the current version pass the evaluation. '''
        raise NotImplementedError

    def update_baseline(self):
        ''' Update the baseline to the last evaluation records. '''
        raise NotImplementedError

    def store_failed_kpis(self):
        raise NotImplementedError


class GitStrategy(Strategy):
    '''
    Use a git repo to maintain baseline.

    If the current KPI is better than baseline, update the baseline:
       - overwrite baseline files with the current KPI.
       - git add all the diff
       - git commit and push to github

    pros:
       - use plain text file and easy to debug and analysis
       - git based version controling is easy to maintain
       - the baseline can be manully managed by changing the baseline repo
    cons:
       - git can not maintain a big history


    details:
       - several branches
          - **master** for the stable baseline
          - **failure** for the latest failed KPI
          - **develop** a temporary branch for the working space
    '''
    def __init__(self, repo_url, local_dst):
        '''
        repo_url: the url to the repo.
        local_dst: the local destination.
        '''
        log.info('GitStrategy.repo_url', repo_url)
        log.info('GitStrategy.local_dst', local_dst)
        self.repo_url = repo_url
        self.local_dst = local_dst

    def refresh_workspace(self):
        log.warn('baseline refresh workspace')
        with PathRecover():
            if $mode != "baseline_test":
                self._init_repo()
                cd @(self.local_dst)
                # git checkout -b master origin/master
                git checkout -b develop origin/master

    def update_baseline(self):
        log.warn('baseline update baseline')
        with PathRecover():
            cd @(self.local_dst)
            assert self.cur_branch == "develop", \
                "branch %s is should be develop" % self.cur_branch
            for model in models():
                with PathRecover():
                    cd @(model)
                    cp *_factor.txt history/  # update baseline
            self._commit_current_kpis()
            git checkout master
            git merge develop
            # only update git repo on production mode
            if config.mode == "production":
                git push origin master

    def evaluation_passed(self):
        ''' here just use a file as success flag. '''
        return evaluation_succeed()

    def store_failed_kpis(self):
        ''' store the failed kpis to failure branch. '''
        log.info("store the failed kpis")
        with PathRecover():
            cd @(self.local_dst)
            assert self.cur_branch == 'develop'
            # store the failed record
            with PathRecover():
                for model in models():
                    cd @(model)
                    git add *_factor.txt
            self._commit_current_kpis()
            git push origin develop -f

    def _commit_current_kpis(self):
        with PathRecover():
            assert self.cur_branch == 'develop'
            title = "evaluate {commit} {status}".format(
                commit = repo.get_paddle_commit(short=True),
                status = 'passed' if self.evaluation_passed() else 'failed',)
            details = [
                "paddle commit: %s" % repo.get_paddle_commit(),
                "evaluation status:\n %s" % gstate.get_evaluation_result()
            ]
            cd @(self.local_dst)
            log.info('commit current kpi to branch[%s]' % self.cur_branch)
            comment = "{title}\n\n{details}".format(
                        title = title,
                        details = '\n'.join(details))
            git commit -a -m @(comment)


    def _init_repo(self):
        with PathRecover():
            if os.path.isdir(config.baseline_local_repo_path()):
                log.info('remove the old baseline: %s' % config.baseline_local_repo_path())
                rm -rf @(config.baseline_local_repo_path())
            log.warn('git clone baseline from {} to {}'.format(
                config.baseline_repo_url(),
                config.baseline_local_repo_path()))
            git clone @(config.baseline_repo_url()) @(config.baseline_local_repo_path())

    @property
    def cur_branch(self):
        with PathRecover():
            cd @(self.local_dst)
            return $(git branch | grep -e "^*").strip()[2:]
