import random
from ce.utils import dictobj


class FakeView:
    @staticmethod
    def index():
        res = dictobj()
        res.latest_commit = dictobj(commit="448ca8a", status=random_status())
        res.commits = []
        for i in range(10):
            res.commits.append(
                dictobj(
                    commit='ffxcaaf',
                    status=random_status(), ))

        res.tasks = []
        for task in range(10):
            res.tasks.append(
                dictobj(
                    kpis=[], short_description="task some desc"))
            for i in range(6):
                res.tasks[-1].kpis.append(
                    dictobj(
                        offset=i,
                        name='kpi-%d' % i,
                        value=0.43,
                        unit='ms',
                        info='',
                        status=random_status(),
                        short_description="some desc", ))
        return res


def random_status():
    return random.choice("success secondary".split())
