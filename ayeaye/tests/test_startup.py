import unittest

import sys
from os import path
from os import remove
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from ayeaye import initializeDatabase


TEST_DB = '/tmp/ayeaye-test.db'


class TestStartup(unittest.TestCase):

    def _fileExists(self, filePath):
        return path.isfile(filePath)


    def setUp(self):
        if self._fileExists(TEST_DB):
            remove(TEST_DB)


    def tearDown(self):
        if self._fileExists(TEST_DB):
            remove(TEST_DB)


    def testInitializeDatabase(self):
        self.assertTrue(initializeDatabase(TEST_DB))
        self.assertTrue(self._fileExists(TEST_DB))


if __name__ == '__main__':
    import xmlrunner
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
