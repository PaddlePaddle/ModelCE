from ce.db import RedisDB, MongoDB
import unittest


class MongoDBTester(unittest.TestCase):
    def setUp(self):
        self.db = MongoDB(test=True)

    def test_tables(self):
        print('tables', self.db.tables())
        self.assertEqual(len(self.db.tables()), 0)

    def test_set_default_table(self):
        self.db.set('id0', dict(name='xxx0', sex="xxxx"))
        rcd = self.db.get('id0')
        self.assertTrue(rcd)
        print('rcd', rcd)
        self.assertEqual(rcd.sex, "xxxx")

    def test_set_table(self):
        self.db.set('id0', dict(name='xxx0'), table='table0')
        rcd = self.db.get('id0', table='table0')
        self.assertTrue(rcd)
        self.assertEqual(rcd.name, "xxx0")

    def test_update_table(self):
        self.db.set('id0', dict(name='xxx0'), table='table0')
        rcd = self.db.get('id0', table='table0')
        self.assertTrue(rcd)
        self.assertEqual(rcd.name, "xxx0")
        self.db.update('id0', dict(name='xxx1'), table='table0')
        rcd = self.db.get('id0', table='table0')
        self.assertTrue(rcd)
        self.assertEqual(rcd.name, 'xxx1')

    def test_update_fields(self):
        self.db.set('id0', dict(name='xxx0', sex='male'), table='table0')
        rcd = self.db.get('id0', table='table0')
        self.assertTrue(rcd)
        self.assertEqual(rcd.name, "xxx0")

        self.db.update_fields('id0', dict(sex='female'), table='table0')
        rcd = self.db.get('id0', table='table0')
        self.assertEqual(rcd.name, 'xxx0')
        self.assertEqual(rcd.sex, 'female')

    def test_gets(self):
        self.db.set({'type': 'book'}, dict(name='xxx0'), table='table0')
        self.db.set({'type': 'book'}, dict(name='xxx0'), table='table0')
        rcds = self.db.gets({'type': 'book'}, table='table0')
        self.assertEqual(len(rcds), 2)

    def test_delete(self):
        self.db.set('id0', dict(name='xxx0'))
        self.assertTrue(self.db.get('id0'))
        self.assertEqual(len(self.db.gets('id0')), 1)
        self.db.delete('id0')
        self.assertEqual(len(self.db.gets('id0')), 0)

    def tearDown(self):
        self.db.client.drop_database('test')


class RedisDBTester(unittest.TestCase):
    def setUp(self):
        self.db = RedisDB(test=True)

    def test_set_get(self):
        self.db.set('name', 'xxx0')
        rcd = self.db.get('name')
        self.assertEqual(rcd, 'xxx0')

    def test_not_found(self):
        res = self.db.get('no-key')
        self.assertEqual(res, None)

    def test_subscribe_publish(self):
        '''
        Test Redis subscribe and publish.
        '''
        p = self.db.new_subpub()
        p.subscribe('channel0')
        datas = ['hello', 'world']
        for data in datas:
            self.db.publish_message('channel0', data)

        message = p.get_message()
        num_messages = message['data']
        for i in range(num_messages):
            message = p.get_message()
            self.assertEqual(message['type'], 'message')
            self.assertEqual(message['data'], datas[i])


if __name__ == '__main__':
    unittest.main()
