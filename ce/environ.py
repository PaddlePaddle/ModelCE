import os
from ce.utils import local


class Environ(object):
    '''
    All the environment variables, setter and getter.
    '''

    @staticmethod
    def workspace():
        return env_setdefault('ce_workspace', os.getcwd())

    @staticmethod
    def test_mode():
        env_setdefault('ce_test_mode', '0')
        return True if os.environ['ce_test_mode'] == '1' else False

    @staticmethod
    def config():
        return env_setdefault('ce_config', 'default.conf')

    @staticmethod
    def task():
        return env_setdefault('ce_task', '')

    @staticmethod
    def commit():
        return env_setdefault('ce_commit', '')

    @staticmethod
    def set_workspace(path):
        if path:
            env_set('ce_workspace', path)
        return Environ.workspace()

    @staticmethod
    def set_test_mode(mode):
        env_set('ce_test_mode', '1' if mode else '0')

    @staticmethod
    def set_config(config):
        env_set('ce_config', config)

    @staticmethod
    def set_task(task):
        env_set('ce_task', task)

    @staticmethod
    def set_commit(x):
        env_set('ce_commit', x)


def env_setdefault(key, default_val):
    if key not in local.env:
        os.environ.setdefault(key, default_val)
        local.env[key] = default_val
    return local.env[key]


def env_get(key):
    return local.env[key]


def env_set(key, value):
    local.env[key] = value
