import sys
sys.path.append('pypage')
from pypage import *
from pypage import layout as lyt
from pypage import FOR

search_page = Page(
    "Continuous Evaluation", filename="pypage-search.html").enable_bootstrap()

with search_page.body:
    with lyt.fluid_container(
            style='margin:0px; padding:0px; box-sizing:unset;'):
        with lyt.row():
            with lyt.col():
                navbar(
                    'CE',
                    links=['/'],
                    link_txts=['index'],
                    theme='dark',
                    color='dark')

        with lyt.row():
            # layout middle
            lyt.col()
            with lyt.col(size=9):
                main = lyt.fluid_container()
            lyt.col()

with main:
    Tag('h2', 'Compare').as_row()

    with Tag(
            'form', class_='container-fluid', method='GET',
            action='/kpi/compare').as_row():
        with Tag('select', name='cur', class_='form-control').as_col(5):
            with FOR('rcd in records'):
                Tag('option',
                    c=VAL('rcd.shortcommit') + "  " + VAL('rcd.date'),
                    value=VAL('rcd.commit'))

        with Tag('select', name='base', class_='form-control').as_col(5):
            with FOR('rcd in records'):
                Tag('option',
                    c=VAL('rcd.shortcommit') + "  " + VAL('rcd.date'),
                    value=VAL('rcd.commit'))

        with lyt.col():
            Tag('button', class_='btn btn-primary', c='Submit',
                type='submit').as_col()

    RawHtml('<hr/>')

    Tag('h2', 'Latest evaluation status').as_row()

    with Tag('p').as_row():
        Tag('span', 'commitid: ')
        with IF('latest_kpi.passed') as f:
            badge(VAL('latest_kpi.commit')).set_success()
            f.add(STMT('else'), -1)
            badge(VAL('latest_kpi.commit')).set_danger()

    with lyt.fluid_container():
        with FOR('name,task in latest_kpi.kpis.items()'):
            Tag('h3', VAL('name')).as_row()
            with lyt.row():
                with table().set_striped():
                    RawHtml('<thead class="thead-dark"><tr>')
                    RawHtml('<th>KPI</th><th>KPI values</th><th>error</th>')
                    RawHtml('</tr></thead>')

                    with FOR('kpiname, kpi in task.kpis.items()'):
                        with table.row():
                            table.col(VAL('kpiname'))
                            with table.col():
                                RawHtml('<pre><code>{{ kpi[2] }}</code></pre>')
                            with table.col():
                                with IF('kpi[3] != "pass"'):
                                    alert(c=VAL('kpi[3]')).set_danger()

kpi_page = Page(
    "Continuous Evaluation", filename="pypage-kpi.html").enable_bootstrap()

with kpi_page.body:
    with lyt.fluid_container(style='margin:0px; padding:0px;'):
        with lyt.row():
            with lyt.col():
                navbar(
                    'CE',
                    links=['/'],
                    link_txts=['index'],
                    theme='dark',
                    color='dark')

        with lyt.row():
            # layout middle
            lyt.col()
            with lyt.col(size=9):
                main = lyt.fluid_container()
            lyt.col()

    with main:
        with lyt.row():
            with Tag('p'):
                Tag('span', 'Comparation between')
                Tag('b', VAL('cur_commit'))
                Tag('span', 'and history')
                Tag('b', VAL('base_commit'))

        with lyt.row():
            Tag('h1', c='Tasks KPI diff')
        with lyt.fluid_container():
            with FOR('task in tasks'):
                with lyt.row():
                    Tag('h2', VAL('task.name'))
                    with table().set_striped():
                        RawHtml('<thead class="thead-dark"><tr>')
                        RawHtml(
                            '<th>KPI</th><th>improvement proportion(red better)</th>'
                        )
                        RawHtml('</tr></thead>')

                        with FOR('kpi in task.kpis'):
                            with table.row():
                                table.col(VAL('kpi.name'))
                                with IF('kpi.ratio > 0.01 or kpi.ratio < -0.01'
                                        ) as f1:
                                    with IF('kpi.ratio > 0') as f2:
                                        table.col(
                                            VAL("'%.2f' % kpi.ratio | float") +
                                            '%',
                                            style='color: red;')
                                        f2.add(STMT('else'), -1)
                                        table.col(
                                            VAL("'%.2f' % kpi.ratio | float") +
                                            '%',
                                            style='color: green;')
                                    f1.add(STMT('else'), -1)
                                    table.col(
                                        VAL("'%.2f' % kpi.ratio | float") + '%'
                                    )

if __name__ == '__main__':
    search_page.compile()
    #kpi_page.display(port=8010)
    kpi_page.compile()
    #search_page.display(port=8010)
