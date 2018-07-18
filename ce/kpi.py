from __future__ import division

import numpy as np

import ce.data_view as dv
from ce.environ import Environ
from ce.utils import log


class Kpi(object):
    dic = {}

    def __init__(self,
                 name,
                 actived=False,
                 unit_repr='',
                 short_description='',
                 description='',
                 threshold=0.02,
                 update_threshold=0.06):
        ''' Interface for Kpi tracker.
        actived: whether this test is turn on
            The test will yield error if failed only if it is actived.
        unit_repr: the unit of the KPI, for train_duration, ms for example.
        desc: the description of this task. '''
        self.name = name
        self.actived = actived
        self.unit_repr = unit_repr
        self.records = []
        self.short_description = short_description
        self.description = description
        self.threshold = threshold
        self.update_threshold = update_threshold

        # calculated kpis
        self._kpi = None

    def add_record(self, rcd):
        self.records.append(rcd)

    def evaluate(self):
        ''' Run the evaluation based on the records collected and history records. '''
        raise NotImplementedError

    def persist(self):
        ''' Persist the evalution result in some way. '''
        # persist data
        commitid = Environ.commit()
        task = Environ.task()
        assert commitid
        assert task
        kpi = dv.Kpi(
            commitid=commitid,
            task=task,
            name=self.name,
            value=self.cur_data,
            unit=self.unit_repr,
            actived=self.actived,
            kpi_type=self.__class__.__name__,
            short_description=self.short_description,
            description=self.description,
            passed=self.evaluate(),
            logs=self.logs, )
        kpi.persist()

        # try to update baseline if needed.
        if self.to_update_baseline():
            dv.KpiBaseline.update(Environ.task(), self.name, self.cur_data)

    @staticmethod
    def compare_with(cur, other):
        ''' compare `cur` with `other` and return a float ratio to indicate how much
        changes cur based on other.
        The `other` is the denominator, the result is like +/- (other-cur)/other, the
        `+/-` will make the result a positive ratio if `cur` is better, negative other-
        wise.
        '''
        return (cur - other) / other

    def to_update_baseline(self):
        raise NotImplementedError

    def cal_kpi(self):
        ''' calculate the KPI(a scalar) based on `self.cur_data`.
        This is just a default implementation, free to customize.  '''
        return np.average(self.records)

    @property
    def cur_data(self):
        self._kpi = self.cal_kpi()
        return self._kpi

    @property
    def baseline_data(self):
        task = Environ.task()
        return dv.KpiBaseline.get(task, self.name)

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

    @property
    def logs(self):
        if self.evaluate():
            return 'passed'
        else:
            return 'current_data: {cur_data}, baseline_data: {baseline_data}, diff exceeds threshold: {threshold}'.format(
                cur_data=self.cur_data,
                baseline_data=self.baseline_data,
                threshold=self.threshold, )


class GreaterWorseKpi(Kpi):
    def __init__(self,
                 name,
                 actived=False,
                 threshold=0.01,
                 unit_repr='',
                 short_description='',
                 description='',
                 update_threshold=0.06):
        super().__init__(
            name=name,
            actived=actived,
            unit_repr=unit_repr,
            short_description=short_description,
            description=description,
            threshold=threshold,
            update_threshold=update_threshold)

    def evaluate(self):
        if self.baseline_data is None:
            return True
        ratio = self.compare_with(self.cur_data, self.baseline_data)
        return ratio < self.threshold

    def to_update_baseline(self):
        if self.evaluate():
            if self.baseline_data is None:
                return True
            ratio = self.compare_with(self.cur_data, self.baseline_data)
            return -ratio > self.update_threshold


class LessWorseKpi(Kpi):
    def __init__(
            self,
            name,
            actived=False,
            threshold=0.01,
            unit_repr='',
            short_description='',
            description='',
            update_threshold=0.06, ):
        super().__init__(
            name=name,
            actived=actived,
            unit_repr=unit_repr,
            short_description=short_description,
            description=description,
            threshold=threshold,
            update_threshold=update_threshold, )
        self.threshold = threshold

    def evaluate(self):
        if self.baseline_data is None:
            return True
        ratio = self.compare_with(self.cur_data, self.baseline_data)
        log.info('ratio', ratio)
        return -ratio < self.threshold

    def to_update_baseline(self):
        if self.evaluate():
            if self.baseline_data is None:
                return True
            ratio = self.compare_with(self.cur_data, self.baseline_data)
            return ratio > self.update_threshold


CostKpi = GreaterWorseKpi
DurationKpi = GreaterWorseKpi
AccKpi = LessWorseKpi

Kpi.__register__(GreaterWorseKpi)
Kpi.__register__(LessWorseKpi)
