#!/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf-8 vi:ts=4:sw=4:expandtab:ft=python

"""
analysis the benchmark model kpi
"""
import numpy as np

class Analysis_kpi_data(object):
    """
    Analysis_kpi_data
    """
    def __init__(self, kpis_list):
        self.kpis_list = kpis_list
        self.analysis_result = {}


    def analysis_data(self):
        """
        analysis the benchmark data
        """
        kpi_names = self.kpis_list[0].keys()
        for name in kpi_names:
            self.analysis_result[name] = {}
        for kpis in self.kpis_list:
            for kpi_name in kpis.keys():
                if 'kpi_data' not in self.analysis_result[kpi_name].keys():
                    self.analysis_result[kpi_name]['kpi_data'] = []
                self.analysis_result[kpi_name]['kpi_data'].append(kpis[kpi_name][-1])
        for name in kpi_names:
            np_data = np.array(self.analysis_result[name]['kpi_data'])
            self.analysis_result[name]['min'] = np_data.min()
            self.analysis_result[name]['max'] = np_data.max()
            self.analysis_result[name]['mean'] = np_data.mean()
            self.analysis_result[name]['median'] = np.median(np_data)
            self.analysis_result[name]['var'] = np_data.var()
            self.analysis_result[name]['std'] = np_data.std()
            self.analysis_result[name]['change_rate'] = np_data.std()/np_data.mean()

    def print_result(self):
        """
        print analysis result
        """
        for kpi_name in self.analysis_result.keys():
            print('kpi:%s' % kpi_name)
            print('min:%s max:%s mean:%s median:%s std:%s change_rate:%s' % (
                    self.analysis_result[kpi_name]['min'],
                    self.analysis_result[kpi_name]['max'],
                    self.analysis_result[kpi_name]['mean'],
                    self.analysis_result[kpi_name]['median'],
                    self.analysis_result[kpi_name]['std'],
                    self.analysis_result[kpi_name]['change_rate']))
