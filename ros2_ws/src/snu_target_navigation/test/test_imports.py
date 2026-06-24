import importlib
import unittest


class ImportTests(unittest.TestCase):

    def test_target_navigation_modules_import(self):
        for module_name in (
            "snu_target_navigation.semantic_object_projector",
            "snu_target_navigation.semantic_object_registry",
            "snu_target_navigation.target_pose_projector",
        ):
            self.assertIsNotNone(importlib.import_module(module_name))
