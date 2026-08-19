import importlib
import unittest


class ImportTests(unittest.TestCase):

    def test_base_control_modules_import(self):
        for module_name in (
            "snu_base_control.cmd_vel_to_four_wheel",
            "snu_base_control.four_wheel_odometry",
            "snu_base_control.startup_lateral_escape",
        ):
            self.assertIsNotNone(importlib.import_module(module_name))
