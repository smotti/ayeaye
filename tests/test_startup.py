import unittest

import sys
from os import path
from os import remove
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import notify_svc


TEST_DB = '/tmp/notify-svc-test.db'


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
        self.assertTrue(notify_svc.initializeDatabase(TEST_DB))
        self.assertTrue(self._fileExists(TEST_DB))


if __name__ == '__main__':
    unittest.main()
