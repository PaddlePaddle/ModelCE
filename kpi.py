from __future__ import division
import json
import numpy as np
import logging
from config import pjoin


class TestError(Exception):
    pass


class Kpi(object):
    dic = {}

    def __init__(self,
                 name,
                 desc='',
                 out_file=None,
                 his_file=None,
                 actived=True,
                 unit_repr=None,
                 desc=None):
        ''' Interface for Kpi tracker.  
        actived: whether this test is turn on
            The test will yield error if failed only if it is actived.
        unit_repr: the unit of the KPI, for train_duration, ms for example.
        desc: the description of this task. '''
        self.name = name
        self.desc = desc
        self.out_file = out_file
        self.his_file = "latest_kpis/" + out_file if his_file is None else his_file
        self.actived = actived
        self.unit_repr = unit_repr
        self.desc = desc
        self.records = []

    def add_record(self, rcd):
        self.records.append(rcd)

    def evaluate(self):
        ''' Run the evaluation based on the records collected and history records. '''
        raise NotImplementedError

    def persist(self):
        ''' Persist the evalution result in some way. '''
        raise NotImplementedError

    @staticmethod
    def compare_with(cur, other):
        ''' compare `cur` with `other` and return a float ratio to indicate how much
        changes cur based on other.
        The `other` is the denominator, the result is like +/- (other-cur)/other, the
        `+/-` will make the result a positive ratio if `cur` is better, negative other-
        wise.
        '''
        raise NotImplementedError

    @staticmethod
    def cal_kpi(data):
        ''' calculate the KPI(a scalar) based on `self.cur_data`.
        This is just a default implementation, free to customize.  '''
        return np.average(data)

    @property
    def cur_data(self):
        raise NotImplementedError

    @property
    def baseline_data(self):
        raise NotImplementedError

    @staticmethod
    def __register__(factor):
        '''
        factor shoud a subclass inherients Kpi
        '''
        assert issubclass(factor, Kpi)
        key = factor.__name__
        assert Kpi.dic.setdefault(key, factor) is factor, \
              "duplicate register %s with a different class" % key
        Kpi.dic[key] = factor


class GreaterWorseKpi(Kpi):
    ''' Evaluator for any factors that large value is bad, trainning cost for example. '''

    def __init__(self,
                 name,
                 diff_thre,
                 skip_head=2,
                 actived=True,
                 unit_repr=None,
                 desc=None):
        '''
        diff_thre: difference threshold.
        '''
        super(GreaterWorseKpi, self).__init__(
            name,
            out_file='%s_factor.txt' % name,
            actived=actived,
            unit_repr=unit_repr,
            desc=desc)
        self.skip_head = skip_head
        self.diff_thre = diff_thre

    def evaluate(self, root):
        '''
        It seems that compare every batch is too sensitive. So we just compare KPI.
        '''
        self.root = root
        cur_data = load_records_from(pjoin(root, self.out_file))[
            self.skip_head:]
        his_data = load_records_from(pjoin(root, self.his_file))[
            self.skip_head:]

        self.ratio = self.compare_with(cur_data, his_data)
        return (-self.ratio) < self.diff_thre

    @staticmethod
    def compare_with(cur, other):
        cur_kpi = GreaterWorseKpi.cal_kpi(cur)
        other_kpi = GreaterWorseKpi.cal_kpi(other)
        return (other_kpi - cur_kpi) / other_kpi

    @property
    def cur_data(self):
        return load_records_from(pjoin(self.root, self.out_file))

    @property
    def baseline_data(self):
        return load_records_from(pjoin(self.root, self.his_file))

    def persist(self):
        lines = []
        is_iterable = False
        if self.records:
            try:
                is_iterable = iter(self.records[0]) is not None
            except Exception as e:
                pass
        for rcd in self.records:
            if not is_iterable: rcd = [rcd]
            rcd = np.array(rcd)
            rcd = rcd.tolist()
            lines.append(json.dumps(rcd))

        # empty records still needs to create an empty file.
        with open(self.out_file, 'w') as f:
            f.write('\n'.join(lines))

    @property
    def fail_info(self):
        info = "[{name}] failed, diff ratio: {ratio} larger than {thre}.".format(
            name=self.name, ratio=-self.ratio, thre=self.diff_thre)
        if not self.actived:
            info = "Task is disabled, " + info
        return info

    @property
    def success_info(self):
        info = "[{name}] pass".format(name=self.name)
        if not self.actived:
            info = "Task is disabled, " + info
        return info


class LessWorseKpi(GreaterWorseKpi):
    ''' Evaluator for any factors that less value is bad, trainning acc for example. '''

    def __init__(self,
                 name,
                 diff_thre,
                 skip_head=2,
                 actived=True,
                 unit_repr=None,
                 desc=None):
        '''
        diff_thre: difference threshold.
        '''
        super(LessWorseKpi, self).__init__(
            name,
            diff_thre,
            skip_head,
            actived=actived,
            unit_repr=unit_repr,
            desc=desc)
        self.skip_head = skip_head
        self.diff_thre = diff_thre

    def evaluate(self, root):
        self.root = root
        cur_data = load_records_from(pjoin(root, self.out_file))[
            self.skip_head:]
        his_data = load_records_from(pjoin(root, self.his_file))[
            self.skip_head:]
        self.ratio = self.compare_with(cur_data, his_data)
        return (-self.ratio) < self.diff_thre

    @staticmethod
    def compare_with(cur, other):
        cur_kpi = LessWorseKpi.cal_kpi(cur)
        other_kpi = LessWorseKpi.cal_kpi(other)
        return (cur_kpi - other_kpi) / other_kpi

    @property
    def cur_data(self):
        return load_records_from(pjoin(self.root, self.out_file))

    @property
    def baseline_data(self):
        return load_records_from(pjoin(self.root, self.his_file))

    @property
    def fail_info(self):
        info = "[{name}] failed, diff ratio: {ratio} larger than {thre}.".format(
            name=self.name, ratio=-self.ratio, thre=self.diff_thre)
        if not self.actived:
            info = "Task is disabled, " + info
        return info

    @property
    def success_info(self):
        info = "[{name}] pass".format(name=self.name)
        if not self.actived:
            info = "Task is disabled, " + info
        return info


CostKpi = GreaterWorseKpi

DurationKpi = GreaterWorseKpi

AccKpi = LessWorseKpi


def load_records_from(file):
    '''
    each line of the data format is
        <json of record>
    for example, a real record might be:
        [[0.1, 0.3], [0.4, 0.2]]
    '''
    datas = []
    with open(file) as f:
        for line in f.readlines():
            data = json.loads(line.strip())
            datas.append(np.array(data))
    return np.array(datas)


Kpi.__register__(GreaterWorseKpi)
Kpi.__register__(LessWorseKpi)
