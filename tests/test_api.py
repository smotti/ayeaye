from os import path, close, unlink, listdir, remove
import sys
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import json
import notify_svc
from api import APP
import sqlite3
from tempfile import mkstemp
from time import sleep, time
import unittest


TEST_NOTIFICATION_FILE = './test_notifications/vagrant'
MAIL_USER = 'vagrant'
MAIL_PASSWORD = 'vagrant'


def notificationReceived(title):
    with open(TEST_NOTIFICATION_FILE, 'r') as f:
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


class ApiWithTestData(unittest.TestCase):

    def insertTestData(self):
        tsHandler = dict(
                topic='TS',
                settings=dict(
                    server='127.0.0.1',
                    port=2525,
                    toAddr=['TS@medicustek.com'],
                    fromAddr='test@medicustek.com',
                    ssl=0,
                    auth=0,
                    starttls=0))
        irbHandler = dict(
                topic='IRB',
                settings=dict(
                    server='127.0.0.1',
                    port=2525,
                    toAddr=['IRB@medicustek.com'],
                    fromAddr='test@medicustek.com',
                    ssl=0,
                    auth=0,
                    starttls=0))
        handlers = [tsHandler, irbHandler]
        notifications = [
                (10, 'TS', 'N1', 'C1'), (15, 'TS', 'N2', 'C2'),
                (20, 'IRB', 'N3', 'C3'), (25, 'IRB', 'N4', 'C4')]
        cur = self.database.cursor()
        cur.execute('''
            INSERT INTO global_setting (handler_type, settings)
            VALUES (1, '{"smtp_server": "", "smtp_account": "", "smtp_password": "", "use_ssl": 0, "use_auth": 1}')
        ''')
        cur.executemany('''
            INSERT INTO notification_archive (time, topic, title, content)
            VALUES (?, ?, ?, ?)
            ''', notifications)
        for h in handlers:
            cur.execute('''
                INSERT INTO handler (topic, handler_type, settings)
                VALUES (?, (SELECT id FROM handler_type WHERE name = 'email'), ?)
            ''', (h['topic'], json.dumps(h['settings']), ))
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


    def testNotificationHistoryByTopic(self):
        rv = self.app.get('/notifications/TS')
        data = json.loads(rv.get_data().decode('utf-8'))

        self.assertEqual(200, rv.status_code)
        self.assertEqual(2, len(data))


    def testNotificationHistoryByTime(self):
        rv = self.app.get('/notifications/IRB?fromTime=10&toTime=30')
        data = json.loads(rv.get_data().decode('utf-8'))
        self.assertEqual(200, rv.status_code)
        self.assertEqual(2, len(data))

        rv = self.app.get('/notifications/IRB?fromTime=15')
        data = json.loads(rv.get_data().decode('utf-8'))
        self.assertEqual(200, rv.status_code)
        self.assertEqual(2, len(data))

        rv = self.app.get('/notifications/?fromTime=15&toTime=30')
        data = json.loads(rv.get_data().decode('utf-8'))
        self.assertEqual(200, rv.status_code)
        self.assertEqual(3, len(data))

        rv = self.app.get('/notifications/')
        data = json.loads(rv.get_data().decode('utf-8'))
        self.assertEqual(200, rv.status_code)
        self.assertEqual(4, len(data))


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
                auth=0,
                starttls=0)
        handler = dict(
                topic='TS',
                settings=dict(
                    server='127.0.0.1',
                    port=2525,
                    toAddr=['TS@medicustek.com'],
                    fromAddr='test@medicustek.com',
                    ssl=0,
                    auth=0,
                    starttls=0))

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


class ApiSendNotificationTestCase(unittest.TestCase):

    def insertTestData(self):
        settings = dict(
                server='127.0.0.1',
                port=2525,
                account='',
                password='',
                toAddr=['norbert@medicustek.com'],
                fromAddr='test@medicustek.com',
                ssl=0,
                auth=0,
                starttls=0)
        handler = dict(
                topic='TS',
                settings=dict(
                    server='127.0.0.1',
                    port=2525,
                    toAddr=['TS@medicustek.com'],
                    fromAddr='test@medicustek.com',
                    ssl=0,
                    auth=0,
                    starttls=0))
        authHandler = dict(
                topic='IRB',
                settings=dict(
                    server='127.0.0.1',
                    port=2525,
                    toAddr=['IRB@medicustek.com'],
                    fromAddr='test@medicustek.com',
                    ssl=0,
                    auth=1,
                    starttls=0,
                    user=MAIL_USER,
                    password=MAIL_PASSWORD))
        sslHandler = dict(
                topic='CRA',
                settings=dict(
                    server='127.0.0.1',
                    port=4650,
                    toAddr=['CRA@medicustek.com'],
                    fromAddr='test@medicustek.com',
                    ssl=1,
                    auth=0,
                    starttls=0))
        handlers = [handler, authHandler, sslHandler]

        cur = self.database.cursor()
        cur.execute('''
            INSERT INTO global_setting (handler_type, settings)
            VALUES (1, ?)
        ''', (json.dumps(settings), ))
        cur.execute('''
            INSERT INTO handler (topic, handler_type)
            VALUES ('test', (SELECT id FROM handler_type WHERE name = 'email'))
        ''')
        for h in handlers:
            cur.execute('''
                INSERT INTO handler (topic, handler_type, settings)
                VALUES (?, (SELECT id FROM handler_type WHERE name = 'email'), ?)
            ''', (h['topic'], json.dumps(h['settings']), ))
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

        remove(TEST_NOTIFICATION_FILE)


    def testSendNotificationWithGlobalSettings(self):
        topic = 'test'
        notification = dict(title='GlobalSettings', content='Test 1 2 3')
        rv = self.app.post(
                '/notifications/'+topic,
                data=json.dumps(notification),
                content_type='application/json')
        
        sleep(1)
        self.assertEqual(200, rv.status_code)
        self.assertTrue(notificationReceived(notification['title']))


    def testSendNotificationWithHandlerSettings(self):
        topic = 'TS'
        notification = dict(title='HandlerSettings', content='Test 1 2 3')
        rv = self.app.post(
                '/notifications/'+topic,
                data=json.dumps(notification),
                content_type='application/json')
        
        sleep(1)
        self.assertEqual(200, rv.status_code)
        self.assertTrue(notificationReceived(notification['title']))       


    def testSendNotificationUsingSMTPAUTH(self):
        topic = 'IRB'
        notification = dict(title='Authentication', content='Test 1 2 3')
        rv = self.app.post(
                '/notifications/'+topic,
                data=json.dumps(notification),
                content_type='application/json')
        
        sleep(1)
        self.assertEqual(200, rv.status_code)
        self.assertTrue(notificationReceived(notification['title']))

    def testSendNotificationUsingSMTPS(self):
        topic = 'CRA'
        notification = dict(title='SMTPS', content='Test 1 2 3')
        rv = self.app.post(
                '/notifications/'+topic,
                data=json.dumps(notification),
                content_type='application/json')
        
        sleep(1)
        self.assertEqual(200, rv.status_code)
        self.assertTrue(notificationReceived(notification['title']))


if __name__ == '__main__':
    unittest.main()
