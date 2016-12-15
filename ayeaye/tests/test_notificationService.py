from os import path, close, unlink, listdir, remove
from shutil import rmtree
import sys
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from appsvc import NotificationService
import json
import sqlite3
from tempfile import mkstemp, mkdtemp
from base64 import b64decode, b64encode
import unittest


def initializeDatabase(databasePath):
    schemaPath = path.realpath(__file__).rsplit('/', 1)[0] + '/' + '../schema.sql'
    with open(schemaPath, 'r', encoding='utf-8') as f:
        schema = f.read()

    try:
        db = sqlite3.connect(databasePath)
        db.executescript(schema)
    except:
        raise
    finally:
        db.close()

    return True


class NotificationServiceTestCase(unittest.TestCase):

    def insertTestData(self, handler, notifications):
        topic = self.topic
        cur = self.database.cursor()
        cur.execute('''
            INSERT INTO handler (topic, handler_type, settings)
            VALUES (?, (SELECT id FROM handler_type WHERE name = 'email'), ?)
        ''', (handler['topic'], json.dumps(handler['settings']), ))
        for n in notifications:
            cur.execute('''
                INSERT INTO notification_archive (title, time, topic)
                VALUES (?, ?, ?)
                ''', (n['title'], n['time'], n['topic'], ))
        self.database.commit()
        cur.close()


    def setUp(self):

        self.databaseFd, self.databasePath = mkstemp(suffix='.test.db')
        initializeDatabase(self.databasePath)
        self.database = sqlite3.connect(self.databasePath)
        self.database.row_factory = sqlite3.Row

        self.topic = 'ts'
        self.fileArchivePath = mkdtemp()
        self.handler = dict(
                topic=self.topic,
                settings=dict(
                    server='127.0.0.1',
                    port=2525,
                    toAddr=['TS@medicustek.com'],
                    fromAddr='test@medicustek.com',
                    ssl=0,
                    auth=0,
                    starttls=0))
        self.notifications = [
                dict(title='test', time=10, topic=self.topic),
                dict(title='test', time=20, topic=self.topic),
                dict(title='test', time=25, topic=self.topic),
                dict(title='test', time=30, topic=self.topic),
                dict(title='test', time=35, topic=self.topic),
                dict(title='test', time=40, topic=self.topic)]

        self.insertTestData(self.handler, self.notifications)


    def tearDown(self):
        self.database.close()
        close(self.databaseFd)
        unlink(self.databasePath)
        rmtree(self.fileArchivePath)


    def testArchiveNotification(self):
        topic = 'TS'
        title = 'Test'
        notification = dict(
                content='Testing __archiveNotification',
                title=title)
        ns = NotificationService(topic, self.database)
        result = ns._archiveNotification(notification)

        cur = self.database.cursor()
        cur.execute('SELECT * FROM notification_archive WHERE title = \'Test\'')
        row = cur.fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(topic.lower(), row['topic'])
        self.assertEqual(title, row['title'])
        self.assertTrue(result)


    def testArchiveAttachments(self):
        notification = dict(content='Testing _archiveAttachments',
                title='Test',
                attachments=[{'filename': 'TestFile.csv',
                              'content': b64encode(b'This is the content of TestFile.csv').decode('utf-8'),
                              'backup': True},
                             {'filename': 'TestFile2.csv',
                              'content': b64encode(b'This is the content of TestFile2.csv').decode('utf-8'),
                              'backup': True},
                             {'filename': 'TestFile3.csv',
                              'content': b64encode(b'This is the content of TestFile3.csv').decode('utf-8'),
                              'backup': True}])
        topic = 'TS'
        ns = NotificationService(topic, self.database, self.fileArchivePath)
        result = ns._archiveAttachments(notification)

        self.assertTrue(topic.lower() in listdir(self.fileArchivePath))
        for attachment in notification['attachments']:
            self.assertTrue(attachment['filename'] in listdir(path.join(self.fileArchivePath, topic.lower())))
            with open(path.join(self.fileArchivePath, topic.lower(), attachment['filename']), 'rb') as f:
                data = f.read()
                self.assertEqual(attachment['content'],
                                 b64encode(data).decode('utf-8'))


    def testArchiveAttachmentsNoBackup(self):
        notification = dict(content='Testing _archiveAttachments',
                title='Test',
                attachments=[{'filename': 'TestFile.csv',
                              'content': b64encode(b'This is the content of TestFile.csv').decode('utf-8'),
                              'backup': False},
                             {'filename': 'TestFile2.csv',
                              'content': b64encode(b'This is the content of TestFile2.csv').decode('utf-8'),
                              'backup': False},
                             {'filename': 'TestFile3.csv',
                              'content': b64encode(b'This is the content of TestFile3.csv').decode('utf-8'),
                              'backup': True}])
        topic = 'TS'
        ns = NotificationService(topic, self.database, self.fileArchivePath)
        result = ns._archiveAttachments(notification)
    
        self.assertTrue(topic.lower() in listdir(self.fileArchivePath))
        self.assertFalse('TestFile.csv' in listdir(path.join(self.fileArchivePath, topic.lower())))
        self.assertFalse('TestFile2.csv' in listdir(path.join(self.fileArchivePath, topic.lower())))
        self.assertTrue('TestFile3.csv' in listdir(path.join(self.fileArchivePath, topic.lower())))

        with open(path.join(self.fileArchivePath, topic.lower(), 'TestFile3.csv'), 'rb') as f:
            data = f.read()
            self.assertEqual(notification['attachments'][2]['content'],
                             b64encode(data).decode('utf-8'))


    def testArchiveDuplicatedNamedAttachments(self):
        notification = dict(content='Testing _archiveAttachments',
                title='Test',
                attachments=[{'filename': 'TestFile.csv',
                              'content': b64encode(b'This is the content of TestFile.csv').decode('utf-8'),
                              'backup': True},
                             {'filename': 'TestFile.csv',
                              'content': b64encode(b'This is the content of TestFile2.csv').decode('utf-8'),
                              'backup': True},
                             {'filename': 'TestFile.csv',
                              'content': b64encode(b'This is the content of TestFile3.csv').decode('utf-8'),
                              'backup': True}])
        topic = 'TS'
        ns = NotificationService(topic, self.database, self.fileArchivePath)
        result = ns._archiveAttachments(notification)

        self.assertTrue(topic.lower() in listdir(self.fileArchivePath))
        self.assertTrue('TestFile.csv' in listdir(path.join(self.fileArchivePath, topic.lower())))
        self.assertTrue('TestFile_1.csv' in listdir(path.join(self.fileArchivePath, topic.lower())))
        self.assertTrue('TestFile_2.csv' in listdir(path.join(self.fileArchivePath, topic.lower())))

        with open(path.join(self.fileArchivePath, topic.lower(), 'TestFile.csv'), 'rb') as f:
            data = f.read()
            self.assertEqual(notification['attachments'][0]['content'],
                             b64encode(data).decode('utf-8'))

        with open(path.join(self.fileArchivePath, topic.lower(), 'TestFile_1.csv'), 'rb') as f:
            data = f.read()
            self.assertEqual(notification['attachments'][1]['content'],
                             b64encode(data).decode('utf-8'))

        with open(path.join(self.fileArchivePath, topic.lower(), 'TestFile_2.csv'), 'rb') as f:
            data = f.read()
            self.assertEqual(notification['attachments'][2]['content'],
                             b64encode(data).decode('utf-8'))


    def testANotificationHistoryByTime(self):
        fromTime = 20
        toTime = 35
        ns = NotificationService(self.topic, self.database)
        result = ns.aNotificationHistoryByTime(fromTime=fromTime, toTime=toTime)
        self.assertEqual(4, len(result))

        offset = 2
        result = ns.aNotificationHistoryByTime(fromTime=fromTime, toTime=toTime, offset=offset)
        self.assertEqual(2, len(result))

        offset = 2
        limit = 1
        result = ns.aNotificationHistoryByTime(fromTime=fromTime, toTime=toTime, offset=offset, limit=limit)
        self.assertEqual(1, len(result))

        fromTime = 35
        result = ns.aNotificationHistoryByTime(fromTime)
        self.assertEqual(2, len(result))

    def testDeleteAllNotificationsWithSomeNotificationsExpectingEmptyList(self):
        ns = NotificationService(self.topic, self.database)
        self.assertEqual(len(self.notifications), len(ns.aNotificationHistory()))

        ns.deleteAllNotifications()
        self.assertEqual(0, len(ns.aNotificationHistory()))


if __name__ == '__main__':
    import xmlrunner
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
