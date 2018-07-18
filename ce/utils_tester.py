from ce.utils import log, dictobj, __
import unittest
from plumbum import local


class LogTester(unittest.TestCase):
    def test_info(self):
        log.info("haha")

    def test_error(self):
        log.error("haha")

    def test_warn(self):
        log.warn("haha")


class dictobject_tester(unittest.TestCase):
    def test(self):
        a = dictobj()
        a.name = 'xxx0'

        self.assertEqual(a.name, 'xxx0')


class ShellTester(unittest.TestCase):
    def test(self):
        res = __('ls -l')
        log.info('ls -l output:', res)

    def test_multi_shell(self):
        __('mkdir -p _test/__test1')
        with local.cwd('./_test'):
            self.assertTrue(
                __('pwd').endswith('_test'), "cwd is %s" % __('pwd'))
            with local.cwd('./__test1'):
                self.assertTrue(__('pwd').endswith('_test/__test1'))


if __name__ == '__main__':
    unittest.main()
