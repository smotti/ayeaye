from os import path, close, unlink, remove
import sys
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import json
import ayeaye
from api import APP
import sqlite3
from tempfile import mkstemp, mkdtemp
from shutil import rmtree
from time import sleep
from base64 import b64encode, b64decode
import email
import unittest


TEST_NOTIFICATION_FILE = './test_notifications/vagrant'
MAIL_USER = 'vagrant'
MAIL_PASSWORD = 'vagrant'


''' Compare the received email with the notification. '''
def notificationReceived(notification):
    with open(TEST_NOTIFICATION_FILE, 'r') as f:
        msg = email.message_from_file(f)
        title = msg['Subject']
        content = ''
        fileContents = list()

        for idx, payload in enumerate(msg.get_payload()):
            if idx == 0:
                content = payload.get_payload()
            else:
                fileContents.append(payload.get_payload())

        compareResult = list()
        compareResult.append(title == notification['title'])
        compareResult.append(content == notification['content'])
        if 'attachments' in notification:
            for f1, f2 in zip(notification['attachments'], fileContents):
                compareResult.append(b64decode(f1['content']) == b64decode(f2))

        return all(compareResult)


class ApiTestCase(unittest.TestCase):

    def setUp(self):
        self.databaseFd, APP.config['DATABASE'] = mkstemp(suffix='test.db')
        APP.config['TESTING'] = True
        self.app = APP.test_client()
        with APP.app_context():
            ayeaye.initializeDatabase(APP.config['DATABASE'])
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
                topic='ts',
                settings=dict(
                    server='127.0.0.1',
                    port=2525,
                    toAddr=['TS@medicustek.com'],
                    fromAddr='test@medicustek.com',
                    ssl=0,
                    auth=0,
                    starttls=0))
        irbHandler = dict(
                topic='irb',
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
                (10, 'ts', 'N1', 'C1'), (15, 'ts', 'N2', 'C2'),
                (20, 'irb', 'N3', 'C3'), (25, 'irb', 'N4', 'C4')]
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
            ayeaye.initializeDatabase(APP.config['DATABASE'])
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


    def testDeleteAllNotifications(self):
        rv = self.app.delete('/notifications/')
        self.assertEqual(200, rv.status_code)

        rv = self.app.get('/notifications/')
        data = json.loads(rv.get_data().decode('utf-8'))
        self.assertEqual(0, len(data))


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
                topic='ts',
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
            ayeaye.initializeDatabase(APP.config['DATABASE'])
        self.database = sqlite3.connect(APP.config['DATABASE'])
        self.insertTestData()


    def tearDown(self):
        self.database.close()
        close(self.databaseFd)
        unlink(APP.config['DATABASE'])


    def testGetEmailHandlers(self):
        rv = self.app.get('/handlers/email')
        data = json.loads(rv.get_data().decode('utf-8'))

        self.database.row_factory = sqlite3.Row
        cur = self.database.cursor()
        cur.execute('SELECT * FROM handler')
        handlers = cur.fetchall()
        cur.close()

        self.assertEqual(len(data), len(handlers))
        self.assertEqual(data[0]['topic'], handlers[0]['topic'])


    def testAddEmailHandler(self):
        handler = dict(topic='IRB', settings=dict(server='127.0.0.1'))
        rv = self.app.post(
                '/handlers/email',
                data=json.dumps(handler),
                content_type='application/json')
        responseData = json.loads(rv.get_data().decode('utf-8'))

        cur = self.database.cursor()
        cur.execute('SELECT * FROM handler WHERE topic = \'{}\''.format(handler['topic'].lower()))
        fromDatabase = cur.fetchone()

        self.assertIsNotNone(fromDatabase)
        self.assertEqual(responseData['topic'].lower(), fromDatabase[2])
        self.assertEqual(rv.status_code, 200)


    def testModifyEmailHandler(self):
        topic = 'TS'
        handler = dict(
                settings=dict(
                    server='127.0.0.1',
                    port=2525,
                    toAddr=['TS@medicustek.com'],
                    fromAddr='test@medicustek.com',
                    ssl=0,
                    auth=0,
                    starttls=1))
        rv = self.app.put(
                '/handlers/email/'+topic,
                data=json.dumps(handler),
                content_type='application/json')

        self.assertEqual(200, rv.status_code)

        cur = self.database.cursor()
        cur.row_factory = sqlite3.Row
        cur.execute('SELECT settings FROM handler WHERE topic = ?', (topic.lower(), ))
        settings = json.loads(cur.fetchone()['settings'])

        self.assertEqual(1, settings['starttls'])


    def testGetSpecificEmailHandler(self):
        topic = 'TS'
        rv = self.app.get('/handlers/email/'+topic)
        data = json.loads(rv.get_data().decode('utf-8'))

        self.assertEqual(200, rv.status_code)
        self.assertEqual(2525, data['settings']['port'])


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
                topic='ts',
                settings=dict(
                    server='127.0.0.1',
                    port=2525,
                    toAddr=['TS@medicustek.com'],
                    fromAddr='test@medicustek.com',
                    ssl=0,
                    auth=0,
                    starttls=0))
        authHandler = dict(
                topic='irb',
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
                topic='cra',
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
        APP.config['ATTACHMENTS_DIR'] = mkdtemp()
        APP.config['TESTING'] = True
        self.app = APP.test_client()
        with APP.app_context():
            ayeaye.initializeDatabase(APP.config['DATABASE'])
        self.database = sqlite3.connect(APP.config['DATABASE'])
        self.insertTestData()


    def tearDown(self):
        self.database.close()
        close(self.databaseFd)
        unlink(APP.config['DATABASE'])
        remove(TEST_NOTIFICATION_FILE)
        rmtree(APP.config['ATTACHMENTS_DIR'])


    def testSendNotificationWithGlobalSettings(self):
        topic = 'test'
        notification = dict(title='GlobalSettings', content='Test 1 2 3')
        rv = self.app.post(
                '/notifications/'+topic,
                data=json.dumps(notification),
                content_type='application/json')

        sleep(1)
        self.assertEqual(200, rv.status_code)
        self.assertTrue(notificationReceived(notification))


    def testSendNotificationWithHandlerSettings(self):
        topic = 'TS'
        notification = dict(title='HandlerSettings', content='Test 1 2 3')
        rv = self.app.post(
                '/notifications/'+topic,
                data=json.dumps(notification),
                content_type='application/json')

        sleep(1)
        self.assertEqual(200, rv.status_code)
        self.assertTrue(notificationReceived(notification))

    def testSendNotificationWithAttachments(self):
        topic = 'TS'
        notification = dict(title='SendLog',
                content='Test 1 2 3',
                attachments=[{"filename": "TestFile1",
                              "content": b64encode(b"This is the content of the file1.").decode('utf-8'),
                              "backup": True},
                             {"filename": "TestFile2",
                              "content": b64encode(b"This is the content of the file2.").decode('utf-8'),
                              "backup": False}])
        rv = self.app.post(
                '/notifications/'+topic,
                data=json.dumps(notification),
                content_type='application/json')

        sleep(1)
        self.assertEqual(200, rv.status_code)
        self.assertTrue(notificationReceived(notification))

    def testSendNotificationUsingSMTPAUTH(self):
        topic = 'IRB'
        notification = dict(title='Authentication', content='Test 1 2 3')
        rv = self.app.post(
                '/notifications/'+topic,
                data=json.dumps(notification),
                content_type='application/json')

        sleep(1)
        self.assertEqual(200, rv.status_code)
        self.assertTrue(notificationReceived(notification))

    def testSendNotificationUsingSMTPS(self):
        topic = 'CRA'
        notification = dict(title='SMTPS', content='Test 1 2 3')
        rv = self.app.post(
                '/notifications/'+topic,
                data=json.dumps(notification),
                content_type='application/json')

        sleep(1)
        self.assertEqual(200, rv.status_code)
        self.assertTrue(notificationReceived(notification))


if __name__ == '__main__':
    import xmlrunner
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
