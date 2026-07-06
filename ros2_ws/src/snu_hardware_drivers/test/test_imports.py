import importlib
import unittest


class ImportTests(unittest.TestCase):

    def test_hardware_driver_modules_import(self):
        for module_name in (
            "snu_hardware_drivers.esp32_serial_bridge",
            "snu_hardware_drivers.gpio_encoder_joint_state",
            "snu_hardware_drivers.gpio_four_wheel_driver",
            "snu_hardware_drivers.wheel_jog_test",
        ):
            self.assertIsNotNone(importlib.import_module(module_name))
