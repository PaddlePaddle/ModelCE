import os
import unittest
import ce.data_view as dv
from ce.kpi import GreaterWorseKpi, LessWorseKpi
from ce.environ import Environ


class GreaterWorseKpiTester(unittest.TestCase):
    def setUp(self):
        dv.init_shared_db(test=True)
        dv.shared_db.client.drop_database('test')
        self.name = 'kpi0'

        self.kpi = GreaterWorseKpi(
            name=self.name,
            actived=True,
            threshold=0.01,
            unit_repr='cm',
            short_description='some desc', )

        Environ.set_commit('commit0')
        Environ.set_task('task0')

        self.assertFalse(dv.KpiBaseline.get('task0', self.name))

        dv.KpiBaseline.update('task0', self.name, 1.)

    def test_evaluate(self):
        cur = 1.3
        self.kpi.add_record(cur)
        self.assertFalse(self.kpi.evaluate())

        self.kpi.records.clear()
        cur = 1.001
        self.kpi.add_record(cur)
        self.assertTrue(self.kpi.evaluate())

    def test_compare_with(self):
        cur = 1.3
        other = 1.
        ratio = (cur - other) / other
        self.assertEqual(self.kpi.compare_with(cur, other), ratio)

    def tearDown(self):
        dv.shared_db.client.drop_database('test')


class LessWorseKpiTester(unittest.TestCase):
    def setUp(self):
        dv.init_shared_db(test=True)
        dv.shared_db.client.drop_database('test')

        self.kpi = LessWorseKpi(
            name='kpi0',
            actived=True,
            threshold=0.01,
            unit_repr='cm',
            short_description='some desc', )
        os.environ['commit'] = 'commit0'
        os.environ['task'] = 'task0'
        self.name = 'kpi0'

        self.assertFalse(dv.KpiBaseline.get('task0', self.name))
        dv.KpiBaseline.update('task0', self.name, 1.)

    def test_evaluate(self):
        cur = 1.3
        self.kpi.add_record(cur)
        self.assertTrue(self.kpi.evaluate())

    def test_compare_with(self):
        cur = 1.3
        other = 1.
        ratio = (cur - other) / other
        self.assertEqual(self.kpi.compare_with(cur, other), ratio)

    def tearDown(self):
        dv.shared_db.client.drop_database('test')


if __name__ == '__main__':
    unittest.main()
