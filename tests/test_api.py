from os import path, close, unlink
import sys
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import json
import notify_svc
from api import APP
import sqlite3
from tempfile import mkstemp
import unittest





class ApiTestCase(unittest.TestCase):

    def setUp(self):
        self.databaseFd, APP.config['DATABASE'] = mkstemp(suffix='test.db')
        APP.config['TESTING'] = True
        self.app = APP.test_client()
        with APP.app_context():
            notify_svc.initializeDatabase(APP.config['DATABASE'])
        self.database = sqlite3.connect(APP.config['DATABASE'])

    def tearDown(self):
        self.database.close()
        close(self.databaseFd)
        unlink(APP.config['DATABASE'])

    def testInitializeDatabase(self):
        cur = self.database.cursor()
        cur.execute('select * from handler_type where name = \'email\'')
        typeId, typeName = cur.fetchone()
        self.assertEqual(typeId, 1)
        self.assertEqual(typeName, 'email')

    def testGetEmailSettingsEmpty(self):
        rv = self.app.get('/settings/email')
        expected = json.loads('''{}''')
        self.assertEqual(expected, json.loads(rv.get_data().decode('utf-8')))

    def testPutEmailSettings(self):
        newSettings = dict(
                smtp_server='127.0.0.1',
                smtp_account='',
                smtp_password='',
                use_ssl=0,
                use_auth=1)
        rv = self.app.put(
                '/settings/email',
                data=json.dumps(newSettings),
                content_type='application/json')
        cur = self.database.cursor()
        cur.execute('''
            SELECT settings FROM global_setting
                WHERE handler_type = (SELECT id FROM handler_type
                                        WHERE name = 'email')
        ''')
        settings = cur.fetchone()
        if settings is None:
            settings = {}
        else:
            settings = json.loads(settings[0])
        self.assertEqual(sorted(newSettings), sorted(settings))
        self.assertEqual(200, rv.status_code)
        self.assertEqual('application/json', rv.mimetype)
        self.assertEqual(sorted(newSettings),
                sorted(json.loads(rv.get_data().decode('utf-8'))))


class ApiTestCaseWithTestData(unittest.TestCase):

    def insertTestData(self):
        cur = self.database.cursor()
        cur.execute('''
            INSERT INTO global_setting (handler_type, settings)
            VALUES (1, '{"smtp_server": "", "smtp_account": "", "smtp_password": "", "use_ssl": 0, "use_auth": 1}')
        ''')
        self.database.commit()
        cur.close()

    def setUp(self):
        self.databaseFd, APP.config['DATABASE'] = mkstemp(suffix='test.db')
        APP.config['TESTING'] = True
        self.app = APP.test_client()
        with APP.app_context():
            notify_svc.initializeDatabase(APP.config['DATABASE'])
        self.database = sqlite3.connect(APP.config['DATABASE'])
        self.insertTestData()

    def tearDown(self):
        self.database.close()
        close(self.databaseFd)
        unlink(APP.config['DATABASE'])

    def testGetEmailSettings(self):
        rv = self.app.get('/settings/email')
        expected = json.loads('''
        {"smtp_server": "", "smtp_account": "", "smtp_password": "",
            "use_ssl": 0, "use_auth": 1}
        ''')
        self.assertEqual(sorted(expected),
                sorted(json.loads(rv.get_data().decode('utf-8'))))


if __name__ == '__main__':
    unittest.main()
