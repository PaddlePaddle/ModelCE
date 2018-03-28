from __future__ import division
import os
import json
import numpy as np
import logging


class TestError(Exception):
    pass


class Factor(object):
    dic = {}

    def __init__(self, out_file=None, his_file=None):
        '''
        the simplest way to persist records is plain file.
        '''
        self.out_file = out_file
        self.his_file = "history/" + out_file if his_file is None else his_file
        self.records = []

    def add_record(self, rcd):
        self.records.append(rcd)

    def evaluate(self):
        ''' Run the evaluation based on the records collected and history records. '''
        raise NotImplementedError

    def persist(self):
        ''' Persist the evalution result in some way. '''
        raise NotImplementedError

    def error_info(self):
        ''' Error information, will write to a log file. '''
        raise NotImplementedError

    def success_info(self):
        raise NotImplementedError

    # def error_info_in_html(self):
    #     ''' Error infomation, will place in a HTML page or email.'''
    #     raise NotImplementedError

    @staticmethod
    def __register__(factor):
        '''
        factor shoud a subclass inherients Factor
        '''
        assert isinstance(factor, Factor)
        key = factor.__name__
        assert Factor.dic.setdefault(key, factor) is factor, \
            "duplicate register %s with a different class" % key


class GreaterWorseFactor(Factor):
    ''' Evaluator for any factors that large value is bad, trainning cost for example. '''

    def __init__(self, name, diff_thre, skip_head=2):
        '''
        diff_thre: difference threshold.
        '''
        super(GreaterWorseFactor, self).__init__(out_file='%s_factor.txt' %
                                                 name)
        self.skip_head = skip_head
        self.name = name
        self.diff_thre = diff_thre

    def evaluate(self, root):
        cur_data = load_records_from(
            pjoin(root, self.out_file))[self.skip_head:]
        his_data = load_records_from(
            pjoin(root, self.his_file))[self.skip_head:]
        diff = cur_data - his_data
        larger = diff > 0
        self.ratios = diff[larger] / his_data[larger]
        logging.info('evaluation diff ratio: %s' % str(self.ratios))
        return not (self.ratios > self.diff_thre).any()

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
    def error_info(self):
        return "[{name}] failed, diff ratio: {ratio} larger than {thre}.".format(
            name=self.name,
            ratio=str(self.ratios).replace('\n', ' '),
            thre=self.diff_thre)

    @property
    def sucess_info(self):
        return "[{name}] pass".format(self.name)


class LessWorseFactor(GreaterWorseFactor):
    ''' Evaluator for any factors that less value is bad, trainning acc for example. '''

    def __init__(self, name, diff_thre, skip_head=2):
        '''
        diff_thre: difference threshold.
        '''
        super(LessWorseFactor, self).__init__(name, diff_thre, skip_head)
        self.skip_head = skip_head
        self.name = name
        self.diff_thre = diff_thre

    def evaluate(self, root):
        cur_data = load_records_from(
            pjoin(root, self.out_file))[self.skip_head:]
        his_data = load_records_from(
            pjoin(root, self.his_file))[self.skip_head:]
        diff = his_data - cur_data
        logging.info('evaluation diff ratio: %s' % str(diff))
        larger = diff > 0
        self.ratios = diff[larger] / his_data[larger]
        logging.info('evaluation diff ratio: %s' % str(self.ratios))
        return not (self.ratios > self.diff_thre).any()

CostFactor = GreaterWorseFactor
DurationFactor = GreaterWorseFactor
AccFactor = LessWorseFactor


def load_records_from(file):
    # each line of the data format is
    #     <json of record>
    # for example, a real record might be:
    #     [[0.1, 0.3], [0.4, 0.2]]
    datas = []
    with open(file) as f:
        for line in f.readlines():
            data = json.loads(line.strip())
            datas.append(np.array(data))
    return np.array(datas)


pjoin = os.path.join
