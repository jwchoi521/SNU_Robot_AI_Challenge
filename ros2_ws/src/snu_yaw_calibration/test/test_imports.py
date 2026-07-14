import importlib
import unittest


class ImportTests(unittest.TestCase):

    def test_yaw_calibration_modules_import(self):
        for module_name in (
            "snu_yaw_calibration.collector_node",
            "snu_yaw_calibration.train_yaw_response_model",
            "snu_yaw_calibration.yaw_cmd_compensator_node",
            "snu_yaw_calibration.yaw_response_model",
        ):
            self.assertIsNotNone(importlib.import_module(module_name))
