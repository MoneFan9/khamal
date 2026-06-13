from django.test import TestCase
from projects.nixpacks import NixpacksPlan
import logging

class NixpacksExtraTests(TestCase):

    def test_nixpacks_plan_from_dict_invalid_types(self):
        data = {
            "phases": {
                "setup": {
                    "nixPkgs": "not-a-list",
                    "nixLibs": None,
                    "aptPkgs": 123
                }
            },
            "variables": "not-a-dict"
        }

        # This should log warnings but not crash, returning empty defaults
        with self.assertLogs('projects.nixpacks', level='WARNING') as cm:
            plan = NixpacksPlan.from_dict(data)

        self.assertEqual(plan.packages, [])
        self.assertEqual(plan.libraries, [])
        self.assertEqual(plan.apt_packages, [])
        self.assertEqual(plan.variables, {})

        # Verify warnings were logged
        self.assertTrue(any("Expected a list but got str" in output for output in cm.output))
        self.assertTrue(any("Expected a list but got int" in output for output in cm.output))
        self.assertTrue(any("Expected a dict but got str" in output for output in cm.output))
