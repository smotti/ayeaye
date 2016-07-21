from os import path, listdir, remove
import sys
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from mtemail import EmailNotificationService
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


class EmailNotificationServiceTestCase(unittest.TestCase):

    def tearDown(self):
        notifications = getListOfNotifications(TEST_NOTIFICATION_DIR)
        list(map(lambda n: remove(TEST_NOTIFICATION_DIR + n), notifications))


    def testSendNotificationNoAuth(self):
        settings = dict(
                server='127.0.0.1', port=2525, toAddr=['test@medicustek.com'],
                fromAddr='norbert@medicustek.com', auth=False, ssl=False)
        ens = EmailNotificationService(settings)

        notification = dict(content='Hello World', title='TEST')
        result = ens.sendNotification(notification)

        self.assertTrue(result)
        self.assertTrue(notificationReceived(notification['title']))


if __name__ == '__main__':
    unittest.main()
