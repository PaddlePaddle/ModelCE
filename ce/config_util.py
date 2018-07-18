from ce.utils import log
import os
from ce.environ import Environ
import configparser


class Config(object):
    g_config = None

    def __init__(self, path):
        log.warn('Loading config from %s' % path)
        abs_path = os.path.join(os.getcwd(), path)
        path = abs_path if os.path.isfile(abs_path) else path
        assert os.path.isfile(path), "file not exists: %s" % path
        self.config = configparser.ConfigParser()
        self.config.read(path)

    def get(self, session, key):
        return self.config.get(session, key)

    def get_int(self, session, key):
        return self.config.getint(session, key)

    def get_float(self, session, key):
        return self.config.getfloat(session, key)

    def get_bool(self, session, key):
        return self.config.getboolean(session, key)

    @staticmethod
    def Global(path=None):
        if not Config.g_config:
            path = path if path else Environ.config()
            Config.g_config = Config(path)
        return Config.g_config
