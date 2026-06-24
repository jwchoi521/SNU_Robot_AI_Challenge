import importlib
import unittest


class ImportTests(unittest.TestCase):

    def test_mission_manager_modules_import(self):
        self.assertIsNotNone(
            importlib.import_module(
                "snu_mission_manager.pick_place_mission_manager"
            )
        )
