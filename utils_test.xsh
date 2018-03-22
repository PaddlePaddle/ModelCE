#!/usr/bin/env xonsh
import os
import unittest
import sys; sys.path.insert(0, '')
import config
import utils
import json
from gstate import gstate

mkdir -p @(config.test_root)

class TestMain(unittest.TestCase):
    def setUp(self):
        config.switch_to_test_mode()
        os.environ['modelci_root'] = config.workspace

    def test_log(self):
        utils.log.logger().info("hello")

    def test_PathRecover(self):
        cur = $(pwd).strip()
        with utils.PathRecover():
            cd ../
            print("switched", $(pwd))
            self.assertNotEqual($(pwd).strip(), cur)
        self.assertEqual($(pwd).strip(), cur)

    def test_download(self):
        with utils.PathRecover():
            cd @(config.test_root)
            utils.log.warn('downloading html')
            utils.download('http://www.baidu.com', '1.html')
            self.assertTrue(os.path.isfile('1.html'))
            rm -f 1.html

    def test_evaluation_succeed(self):
        with utils.PathRecover():
            # prepare data
            content = '\n'.join([
                    'model0\tpass',
                    'model1\tpass',])
            utils.gstate.set(config._evaluation_result_, content)
            self.assertTrue(utils.evaluation_succeed())

    def test_evaluation_succeed_fail(self):
        with utils.PathRecover():
            # prepare data

            content = '\n'.join([
                    'model0\tpass',
                    'model1\tfail',])
            utils.gstate.set(config._evaluation_result_, content)
            self.assertFalse(utils.evaluation_succeed())

    def test_global_state_set(self):
        with utils.PathRecover():
            utils.gstate.set("name", "jomn")
            self.assertEqual(utils.gstate.get("name"), "jomn")

    def test_write_init_models_factors_to_gstate(self):
        import baseline
        with utils.PathRecover():
            baseline.strategy.refresh_workspace()
            utils.write_init_models_factors_to_gstate()

    def test_update_model_factors_status_fail(self):
        import baseline
        with utils.PathRecover():
            baseline.strategy.refresh_workspace()
            utils.write_init_models_factors_to_gstate()
            error_info = "error xxxx"
            utils.update_model_factors_status("resnet30", "train_cost", error_info)
            # check
            status = json.loads(gstate.get(config._model_factors_))
            for model in status:
                if model[0] == 'resnet30':
                    for factor in model[1]:
                        if factor[0] == 'train_cost':
                            self.assertEqual(factor[1], -1)
                    break
    def test_update_model_factors_status_success(self):
        import baseline
        with utils.PathRecover():
            baseline.strategy.refresh_workspace()
            utils.write_init_models_factors_to_gstate()
            error_info = "pass"
            utils.update_model_factors_status("resnet30", "train_cost", error_info)
            # check
            status = json.loads(gstate.get(config._model_factors_))
            for model in status:
                if model[0] == 'resnet30':
                    for factor in model[1]:
                        if factor[0] == 'train_cost':
                            self.assertEqual(factor[1], 1)
                    break

    def test_write_init_progress_to_gstate(self):
        import baseline
        with utils.PathRecover():
            baseline.strategy.refresh_workspace()
            utils.write_init_models_factors_to_gstate()
            utils.write_init_progress_to_gstate()

            progress = json.loads(gstate.get_progress_list())
            self.assertTrue(progress)

    def test_write_history_to_gstate(self):
        import baseline
        with utils.PathRecover():
            baseline.strategy.refresh_workspace()
            utils.write_history_to_gstate()


unittest.main(module='utils_test')
