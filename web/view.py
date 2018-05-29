import sys
sys.path.append('pypage')
sys.path.append('..')
import config
import json
from db import MongoDB
from pypage import *
from pypage import layout as lyt
from datetime import datetime, timedelta
from kpi import Kpi
from api import *

status_page = Page(
    "Evaluation Status", filename="pypage-status.html").enable_bootstrap()
# defail for a commit
commit_detail_page = Page(
    "Evaluation Details", filename="pypage-detail.html").enable_bootstrap()
compare_page = Page(
    "Continuous Evaluation", filename="pypage-search.html").enable_bootstrap()

db = MongoDB(config.db_name)


def build_index_page():
    page = Page('Continous Evaluation', debug=True).enable_bootstrap()

    commit_snip = CommitStatusSnip()
    commit_detail_snip = CommitDetailSnip()

    with page.body:
        # add navbar
        NavSnip().html

        main_container = create_middle_align_box()
        with main_container:
            with lyt.row():
                with lyt.col(size=4):
                    Tag('h3', 'Evaluated Commits')
                    Tag('p', 'green means successful, grey means fail.')
                    commit_snip.html
                with lyt.col():
                    Tag('h3', 'Latest Evaluation')
                    commit_detail_snip.html

    return page.compile_str(), (commit_snip, commit_detail_snip)


def build_commit_detail_page():
    page = Page('Commit Evaluation Details').enable_bootstrap()

    commit_detail_snip = CommitDetailSnip()

    with page.body:
        NavSnip().html

        main_container = create_middle_align_box()
        with main_container:
            Tag('h2', 'Commit details')
            commit_detail_snip.html

    return page.compile_str(), (commit_detail_snip, )


def build_compare_page():
    page = Page('Commit Compare').enable_bootstrap()

    commit_compare_select_snip = CommitCompareSelectSnip()
    commit_compare_result_snip = CommitCompareResultSnip()

    with page.body:
        NavSnip().html
        main_container = create_middle_align_box()
        with main_container:
            with lyt.row():
                with lyt.fluid_container():
                    commit_compare_select_snip.html
            with lyt.row():
                with lyt.fluid_container():
                    commit_compare_result_snip.html

    return page.compile_str(), (
        commit_compare_select_snip,
        commit_compare_result_snip, )


def create_middle_align_box():
    with lyt.fluid_container():
        with lyt.row():
            lyt.col()
            with lyt.col(size=10):
                res = lyt.fluid_container()
            lyt.col()
    return res


class NavSnip(Snippet):
    ''' Navegation '''

    @property
    def html(self):
        navbar(
            'CE',
            links=[
                '/',
                '/commit/compare',
            ],
            link_txts=['index', 'compare'],
            theme='dark',
            color='dark')

    def logic(self):
        return {}


class CommitDetailSnip(Snippet):
    ''' Display commit details. '''

    @property
    def html(self):
        '''
        variables:
          - version
        '''
        with Tag('p').as_row():
            with IF('version.passed') as f:
                badge(VAL('version.commit')).set_success()
                f.add(STMT('else'), -1)
                badge(VAL('version.commit')).set_danger()
            RawHtml('<hr/>')

        with lyt.fluid_container():
            Tag('h2', 'Tasks').as_row()
            with FOR('name,task in version.kpis.items()'):
                Tag('h4', VAL('name')).as_row()
                with lyt.row():
                    with table().set_striped():
                        RawHtml('<thead class="thead-dark"><tr>')
                        RawHtml(
                            '<th>KPI</th><th>KPI values</th><th>error</th>')
                        RawHtml('</tr></thead>')

                        with FOR('kpiname, kpi in task.kpis.items()'):
                            with table.row():
                                table.col(VAL('kpiname'))
                                with table.col():
                                    RawHtml(
                                        '<pre><code>{{ kpi[2] }}</code></pre>')
                                with table.col():
                                    with IF('kpi[3] != "pass"'):
                                        alert(c=VAL('kpi[3]')).set_danger()

    def logic(self, commitid):
        task_kpis = query_commit_from_details(commitid)
        res = objdict(version=dict(
            commit=commitid,
            passed=tasks_success(task_kpis),
            kpis=task_kpis, ))
        return res


class CommitCompareSelectSnip(Snippet):
    ''' Comparasion select form. '''

    @property
    def html(self):
        Tag('h2', 'Compare').as_row()
        with Tag('form',
                 class_='container-fluid',
                 method='GET',
                 action='/commit/compare').as_row():
            with Tag('select', name='cur', class_='form-control').as_col(5):
                with FOR('rcd in %s' % self.KEY('records')):
                    Tag('option',
                        c=VAL('rcd.shortcommit') + "  " + VAL('rcd.date'),
                        value=VAL('rcd.commit'),
                        style="color:green")

            with Tag('select', name='base', class_='form-control').as_col(5):
                with FOR('rcd in %s' % self.KEY('records')):
                    Tag('option',
                        c=VAL('rcd.shortcommit') + "  " + VAL('rcd.date'),
                        value=VAL('rcd.commit'))

            with lyt.col():
                Tag('button',
                    class_='btn btn-primary',
                    c='Submit',
                    type='submit').as_col()
        RawHtml('<hr/>')

    def logic(self):
        records_ = query_all_commits_from_details()
        return {self.KEY('records'): records_}


class CommitStatusSnip(Snippet):
    ''' A list of commits. '''

    @property
    def html(self):
        ''' Commit list with links to details. '''

        with Tag('ul', class_='list-group'):
            href_val = '/commit/details?commit=%s' % VAL('commit.commit')
            with FOR('commit in %s' % self.KEY('commits')):
                with IF('commit.passed') as f:
                    with Tag(
                            'a',
                            class_='list-group-item list-group-item-action list-group-item-success',
                            href=href_val):
                        Tag('b', VAL('commit.shortcommit'))
                        Tag('span', VAL('commit.date'))

                    f.add(STMT('else'), -1)

                    with Tag(
                            'a',
                            class_='list-group-item list-group-item-action list-group-item-secondary',
                            href=href_val):
                        Tag('b', VAL('commit.shortcommit'))
                        Tag('span', VAL('commit.date'))

    def logic(self):
        commits = query_all_commits_from_details()
        return {self.KEY('commits'): [v for v in reversed(commits)], }


class CommitCompareResultSnip(Snippet):
    ''' Comparasion result. '''

    @property
    def html(self):
        with lyt.row():
            with Tag('p'):
                Tag('span', 'Comparation between')
                Tag('b', self.VAL('cur_commit'))
                Tag('span', 'and history')
                Tag('b', self.VAL('base_commit'))
            RawHtml('<hr/>')

        with lyt.row():
            Tag('h2', c='Tasks KPI diff')
        with lyt.row():
            with lyt.fluid_container():
                with FOR('task in %s' % self.KEY('tasks')):
                    with lyt.row():
                        Tag('h3', VAL('task.name'))
                        with table().set_striped():
                            RawHtml('<thead class="thead-dark"><tr>')
                            RawHtml(
                                '<th>KPI %s </th><th>improvement proportion(red better)</th>'
                                % (VAL('task.kpis[5]')))
                            RawHtml('</tr></thead>')

                            with FOR('kpi in task.kpis'):
                                with table.row():
                                    table.col(VAL('kpi.name'))
                                    with IF('kpi.ratio > 0.01 or kpi.ratio < -0.01'
                                            ) as f1:
                                        with IF('kpi.ratio > 0') as f2:
                                            table.col(VAL(
                                                "'%.2f' % kpi.ratio | float") +
                                                      '%',
                                                      style='color: red;')
                                            f2.add(STMT('else'), -1)
                                            table.col(VAL(
                                                "'%.2f' % kpi.ratio | float") +
                                                      '%',
                                                      style='color: green;')
                                        f1.add(STMT('else'), -1)
                                        table.col(
                                            VAL("'%.2f' % kpi.ratio | float") +
                                            '%')

    def logic(self, cur_commit, base_commit):
        print('cur', cur_commit)
        print('base', base_commit)

        cur_rcds = query_commit_from_details(cur_commit)
        base_rcds = query_commit_from_details(base_commit)

        res = []
        for name in cur_rcds.keys():
            cur_task = cur_rcds.get(name, None)
            base_task = base_rcds.get(name, None)
            # if eithor do not have some task, skip it.
            if not (cur_task or base_task): continue

            record = objdict()
            res.append(record)
            record.name = name
            record.kpis = []
            for kpi in cur_task.kpis.keys():
                cur_kpi = cur_task.kpis.get(kpi, None)
                base_kpi = base_task.kpis.get(kpi, None)
                if not (cur_kpi or base_kpi): continue
                kpi_ = objdict()
                kpi_type = Kpi.dic.get(cur_kpi[1])

                kpi_.name = kpi
                kpi_.ratio = kpi_type.compare_with(
                    cur_kpi[0], base_kpi[0]) * 100.  # get a percentage
                record.kpis.append(kpi_)
        return {
            self.KEY('tasks'): res,
            self.KEY('cur_commit'): cur_commit[:7],
            self.KEY('base_commit'): base_commit[:7],
        }


def passed_commits():
    pass


class objdict(dict):
    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, item):
        return self[item]
