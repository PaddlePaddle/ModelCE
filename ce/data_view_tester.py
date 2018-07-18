import unittest
import ce.data_view as dv
from ce.utils import log


class KpiTester(unittest.TestCase):
    def setUp(self):
        self.commitid = 'dfafa'
        self.task = 'task0'
        self.name = 'kpi0'

        dv.shared_db = None
        dv.init_shared_db(test=True)
        self.kpi = dv.Kpi(commitid=self.commitid,
                          task=self.task,
                          name=self.name)

    def test_persist(self):
        self.kpi.set_value(1.)
        self.kpi.persist()

    def test_query(self):
        self.kpi.set_value(1.)
        self.kpi.persist()

        another_kpi = dv.Kpi(commitid=self.commitid,
                             task=self.task,
                             name=self.name)
        info = another_kpi.fetch_infos()
        self.assertTrue(info)
        self.assertAlmostEqual(info['value'], 1.)

    def test_query_not_exist(self):
        another_kpi = dv.Kpi(commitid='not-exitsts',
                             task=self.task,
                             name=self.name)
        exists = True
        try:
            another_kpi.fetch_infos()
        except:
            exists = False
        self.assertFalse(exists)

    def tearDown(self):
        record_id = dv.Kpi.gen_record_id(self.commitid, self.task, self.name)
        dv.shared_db.delete(record_id)


class TaskTester(unittest.TestCase):
    def setUp(self):
        self.commitid = 'dfadfx'
        self.name = 'task0'
        self.kpi_ids = set()

        dv.shared_db = None
        dv.init_shared_db(test=True)
        self.kpi = []
        self.task = dv.Task(
            commitid=self.commitid, name=self.name, kpis=self.kpi)
        self.kpi_ids.add(self.task.record_id)
        for i in range(3):
            kpi_name = 'kpi' + str(i)
            self.kpi.append(kpi_name)
            kpi = dv.Kpi(commitid=self.commitid, task=self.name, name=kpi_name)
            kpi.set_value(i)
            kpi.persist()
            self.kpi_ids.add(kpi.record_id)

    def test_persist(self):
        self.task.persist()

    def test_query(self):
        self.task.persist()
        another_task = dv.Task(commitid=self.commitid, name=self.name)
        another_task.fetch_info()
        self.assertEqual(len(another_task.data.kpis), 3)

        kpis = another_task.fetch_kpis()
        log.info('kpis', kpis)
        self.assertEqual(len(kpis), 3)

    def test_query_all(self):
        for i in range(10):
            t = dv.Task(commitid="xx0%d" % i, name="suome", kpis=[])
            t.persist()

        records = dv.Task.fetch_all()
        log.info('fetch all records', records)
        self.assertEqual(len(records), 10)

    def tearDown(self):
        log.warn('delete test database')
        dv.shared_db.client.drop_database('test')


class CommitTester(unittest.TestCase):
    def setUp(self):
        self.commitid = "xxsdfas0"
        dv.shared_db = None
        dv.init_shared_db(test=True)

        self.commit = dv.Commit(
            commitid=self.commitid, tasks=['task0', 'task1'])

    def test_persist(self):
        self.commit.persist()

    def tearDown(self):
        dv.shared_db.client.drop_database('test')


class KpiBaselineTester(unittest.TestCase):
    def test_update(self):
        dv.init_shared_db(True)
        dv.KpiBaseline.update('task0', 'kpi0', 1., 'first update')

    def test_get(self):
        dv.init_shared_db(True)
        dv.KpiBaseline.update('task0', 'kpi0', 1., 'first update')
        dv.KpiBaseline.update('task0', 'kpi0', 2., 'first update')
        dv.KpiBaseline.update('task0', 'kpi0', 3., 'first update')
        dv.KpiBaseline.update('task0', 'kpi1', True, 'first update')

        rcd = dv.KpiBaseline.get('task0', 'kpi0')
        log.info('baseline record', rcd)
        self.assertEqual(rcd, 3.)
        self.assertEqual(dv.KpiBaseline.get('task0', 'kpi1'), True)

    def tearDown(self):
        dv.shared_db.client.drop_database('test')


if __name__ == '__main__':
    unittest.main()
