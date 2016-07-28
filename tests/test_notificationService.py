from os import path, close, unlink, listdir, remove
import sys
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from appsvc import NotificationService
import json
import sqlite3
from tempfile import mkstemp
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

    def insertTestData(self):
        topic = self.topic
        handler = dict(
                topic=topic,
                settings=dict(
                    server='127.0.0.1',
                    port=2525,
                    toAddr=['TS@medicustek.com'],
                    fromAddr='test@medicustek.com',
                    ssl=0,
                    auth=0,
                    starttls=0))
        notifications = [
                dict(title='test', time=10, topic=topic),
                dict(title='test', time=20, topic=topic),
                dict(title='test', time=25, topic=topic),
                dict(title='test', time=30, topic=topic),
                dict(title='test', time=35, topic=topic),
                dict(title='test', time=40, topic=topic)]

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
        self.topic = 'TS'
        self.insertTestData()


    def tearDown(self):
        self.database.close()
        close(self.databaseFd)
        unlink(self.databasePath)


    def testArchiveNotification(self):
        notification = dict(content='Testing __archiveNotification',
                title='Test')
        topic = 'TS'
        ns = NotificationService(topic, self.database)
        result = ns._archiveNotification(notification)

        cur = self.database.cursor()
        cur.execute('SELECT * FROM notification_archive WHERE title = \'Test\'')
        row = cur.fetchone()

        self.assertIsNotNone(row)
        self.assertEqual('TS', row[2])
        self.assertEqual('Test', row[3])
        self.assertTrue(result)


    def testANotificationHistoryByTime(self):
        fromTime = 20
        toTime = 35
        ns = NotificationService(self.topic, self.database)
        result = ns.aNotificationHistoryByTime(fromTime, toTime)
        self.assertEqual(4, len(result))

        fromTime = 35
        result = ns.aNotificationHistoryByTime(fromTime)
        self.assertEqual(2, len(result))


if __name__ == '__main__':
    unittest.main()
