import logging
from plumbum import local


class log:
    @staticmethod
    def logger():
        mylogger = logging.getLogger(__name__)
        mylogger.setLevel(logging.INFO)
        if not mylogger.handlers:
            ch = logging.StreamHandler()
            mylogger.addHandler(ch)
        return mylogger

    @staticmethod
    def info(*args):
        log.logger().info(' '.join([str(s) for s in args]))

    @staticmethod
    def warn(*args):
        log.logger().warning(' '.join([str(s) for s in args]))

    def error(*args):
        log.logger().error(' '.join([str(s) for s in args]))

    def debug(*args):
        log.logger().debug(' '.join([str(s) for s in args]))


class dictobj(dict):
    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, item):
        if item in self:
            return self[item]
        else:
            raise AttributeError("No such attribute: %s" % item)


class __check_type__:
    @staticmethod
    def match_str(*x):
        for i in range(len(x)):
            assert isinstance(x[i], str), __check_type__._error_info(x[i], str,
                                                                     i)

    @staticmethod
    def match_float(*x):
        for i in range(len(x)):
            assert isinstance(x[i], float), __check_type__._error_info(
                x[i], float, i)

    @staticmethod
    def match_list(*x):
        for i in range(len(x)):
            assert isinstance(x[i], list), __check_type__._error_info(x[i],
                                                                      list, i)

    @staticmethod
    def match_bool(*x):
        for i in range(len(x)):
            assert isinstance(x[i], bool), __check_type__._error_info(x[i],
                                                                      bool, i)

    @staticmethod
    def match_bool_or_none(*x):
        for i in range(len(x)):
            assert isinstance(
                x[i], bool) or x[i] is None, __check_type__._error_info(
                    x[i], bool, i)

    @staticmethod
    def _error_info(x, t, i=None):
        res = ""
        if i is not None:
            res = "%dth argument type check failed" % i
        return res + ", need %s, get type %s" % (str(t), str(type(x)))


def __(cmd):
    fs = cmd.split()
    cmd = local[fs[0]]
    args = fs[1:]
    return cmd(*args).strip()
