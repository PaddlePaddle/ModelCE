import os
import unittest
import sys

from plumbum import local

from ce.environ import Environ


class EnvironTester(unittest.TestCase):
    def setUp(self):
        Environ.set_config('../default.conf')

    def test_set_get_env(self):
        Environ.set_commit('commit000')
        self.assertEqual(Environ.commit(), 'commit000')

    def test_child_process(self):
        Environ.set_config('1')
        self.assertEqual(Environ.config(), '1')
        out = local['python']('environ_tester.py', '1')
        print('out', out)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        print(os.environ['ce_config'])
    else:
        unittest.main()
