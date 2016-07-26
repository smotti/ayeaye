from os import path, close, unlink, listdir, remove
import sys
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import json
import notify_svc
from api import APP
import sqlite3
from tempfile import mkstemp
import unittest


TEST_NOTIFICATION_DIR = './test_notifications/'


def getListOfNotifications(path):
    return list(filter(lambda n: n != 'README.md', listdir(path)))


def notificationReceived(title):
    notifications = getListOfNotifications(TEST_NOTIFICATION_DIR)
    for n in notifications:
        with open(TEST_NOTIFICATION_DIR + n, 'r') as f:
            for l in f:
                if l.startswith('Subject: ' + title):
                    return True
    return False


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


class ApiHandlersEmailTestCase(unittest.TestCase):

    def insertTestData(self):
        settings = dict(
                server='127.0.0.1',
                port=2525,
                account='',
                password='',
                toAddr=['norbert@medicustek.com'],
                fromAddr='test@medicustek.com',
                ssl=0,
                auth=0)
        handler = dict(
                topic='TS',
                settings=dict(
                    smtp_server='127.0.0.1',
                    smtp_port=2525,
                    toAddr=['TS@medicustek.com'],
                    fromAddr='test@medicustek.com',
                    use_ssl=0,
                    use_auth=0))

        cur = self.database.cursor()
        cur.execute('''
            INSERT INTO global_setting (handler_type, settings)
            VALUES (1, ?)
        ''', (json.dumps(settings), ))
        cur.execute('''
            INSERT INTO handler (topic, handler_type)
            VALUES ('test', (SELECT id FROM handler_type WHERE name = 'email'))
        ''')
        cur.execute('''
            INSERT INTO handler (topic, handler_type, settings)
            VALUES (?, (SELECT id FROM handler_type WHERE name = 'email'), ?)
        ''', (handler['topic'], json.dumps(handler['settings']), ))
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

        notifications = getListOfNotifications(TEST_NOTIFICATION_DIR)
        list(map(lambda n: remove(TEST_NOTIFICATION_DIR + n), notifications))


    def testGetEmailHandlers(self):
        rv = self.app.get('/handlers/email')
        data = json.loads(rv.get_data().decode('utf-8'))

        cur = self.database.cursor()
        cur.execute('SELECT * FROM handler')
        handlers = cur.fetchall()
        cur.close()

        self.assertEqual(len(data), len(handlers))
        self.assertEqual(data[0][1], handlers[0][1])


    def testAddEmailHandler(self):
        handler = dict(topic='IRB', settings=dict(smtp_server='127.0.0.1'))
        rv = self.app.post(
                '/handlers/email',
                data=json.dumps(handler),
                content_type='application/json')
        responseData = json.loads(rv.get_data().decode('utf-8'))

        cur = self.database.cursor()
        cur.execute('SELECT * FROM handler WHERE topic = \'IRB\'')
        fromDatabase = cur.fetchone()

        self.assertIsNotNone(fromDatabase)
        self.assertEqual(responseData['topic'], fromDatabase[1])
        self.assertEqual(rv.status_code, 200)


    def testSendNotificationWithGlobalSettings(self):
        topic = 'test'
        notification = dict(title='GlobalSettings', content='Test 1 2 3')
        rv = self.app.post(
                '/notifications/'+topic,
                data=json.dumps(notification),
                content_type='application/json')

        self.assertEqual(200, rv.status_code)
        self.assertTrue(notificationReceived(notification['title']))


    def testSendNotificationWithHandlerSettings(self):
        pass
        

if __name__ == '__main__':
    unittest.main()