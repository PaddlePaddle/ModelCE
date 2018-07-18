import os
from ce import repo
from ce.utils import local, __, log
import unittest


class RepoTester(unittest.TestCase):
    def setUp(self):
        __('rm -rf _test_clone_ce')
        repo.clone('https://github.com/PaddlePaddle/continuous_evaluation.git',
                   './_test_clone_ce')

    def test_clone(self):
        self.assertTrue(os.path.isdir('./_test_clone_ce'))
        self.assertTrue(os.path.isdir('./_test_clone_ce/.git'))

    def test_commit(self):
        commit = repo.get_commit('./_test_clone_ce')
        log.info('commit', commit)
        self.assertTrue(commit)


if __name__ == '__main__':
    unittest.main()
