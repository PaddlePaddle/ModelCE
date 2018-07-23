#!/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf-8 vi:ts=4:sw=4:expandtab:ft=python
"""
analysis the benchmark model kpi
"""
import numpy as np
from utils import log

class AnalysisKpiData(object):
    """
    Analysis_kpi_data
    """

    def __init__(self, kpis_status, kpis_list):
        self.kpis_list = kpis_list
        self.kpis_status = kpis_status
        self.analysis_result = {}
        self.diff_thre = 0.05

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
                self.analysis_result[kpi_name]['kpi_data'].append(kpis[
                    kpi_name][-1])
        for name in kpi_names:
            np_data = np.array(self.analysis_result[name]['kpi_data'])
            self.analysis_result[name]['min'] = np_data.min()
            self.analysis_result[name]['max'] = np_data.max()
            self.analysis_result[name]['mean'] = np_data.mean()
            self.analysis_result[name]['median'] = np.median(np_data)
            self.analysis_result[name]['var'] = np_data.var()
            self.analysis_result[name]['std'] = np_data.std()
            self.analysis_result[name]['change_rate'] = np_data.std(
            ) / np_data.mean()

    def print_result(self):
        """
        print analysis result
        """
        suc = True
        for kpi_name in self.analysis_result.keys():
            is_actived = self.kpis_status[kpi_name]
            log.info('kpi: %s, actived: %s' % (kpi_name, is_actived))
            if is_actived:
                if self.analysis_result[kpi_name]['change_rate'] > self.diff_thre:
                    suc = False
                    log.warn("NOTE kpi: %s change_rate too bigger!" % kpi_name)
            log.info('min:%s max:%s mean:%s median:%s std:%s change_rate:%s' %
                  (self.analysis_result[kpi_name]['min'],
                   self.analysis_result[kpi_name]['max'],
                   self.analysis_result[kpi_name]['mean'],
                   self.analysis_result[kpi_name]['median'],
                   self.analysis_result[kpi_name]['std'],
                   self.analysis_result[kpi_name]['change_rate']))
        if not suc:
            raise Exception("some kpi's change_rate has bigger then thre")
