# test/self_test.py

import unittest
import subprocess

class SelfTest(unittest.TestCase):
    def test_nyx_core_execution(self):
        """ Run nyx_core.py and check for errors """
        result = subprocess.run(["python3", "src/nyx_core.py"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "nyx_core.py execution failed!")

if __name__ == "__main__":
    unittest.main()
