from os import path, listdir, remove
import sys
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from mtemail import EmailNotificationService
from time import sleep
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


class EmailNotificationServiceTestCase(unittest.TestCase):

    def tearDown(self):
        remove(TEST_NOTIFICATION_FILE)


    def testSendNotificationNoAuth(self):
        settings = dict(
                server='127.0.0.1', port=2525, toAddr=['test@medicustek.com'],
                fromAddr='norbert@medicustek.com', auth=False, ssl=False, starttls=False)
        ens = EmailNotificationService(settings)

        notification = dict(content='Hello World', title='TEST')
        result = ens.sendNotification(notification)

        sleep(1)
        self.assertTrue(result)
        self.assertTrue(notificationReceived(notification['title']))

    def testSendNotificationWithFileNoAuth(self):
        settings = dict(
                server='127.0.0.1', port=2525, toAddr=['test@medicustek.com'],
                fromAddr='norbert@medicustek.com', auth=False, ssl=False, starttls=False)
        ens = EmailNotificationService(settings)

        notification = dict(content='Hello World', title='TEST', files=["/tmp/tmp1", "/tmp/tmp2"])
        f = open("/tmp/tmp1", "w")
        f.write("This is tmp file #1")
        f.close()

        f = open("/tmp/tmp2", "w")
        f.write("This is Mambo #5")
        f.close()

        result = ens.sendNotification(notification)

        sleep(1)
        self.assertTrue(result)
        self.assertTrue(notificationReceived(notification['title']))


    def testSendNotificationUsingAUTH(self):
        settings = dict(
                server='127.0.0.1', port=2525, toAddr=['test@medicustek.com'],
                fromAddr='norbert@medicustek.com', auth=True, ssl=False,
                starttls=False, user=MAIL_USER, password=MAIL_PASSWORD)
        ens = EmailNotificationService(settings)

        notification = dict(content='Hello World', title='TEST')
        result = ens.sendNotification(notification)

        sleep(1)
        self.assertTrue(result)
        self.assertTrue(notificationReceived(notification['title']))


    def testSendNotificationUsingStartTLS(self):
        settings = dict(
                server='127.0.0.1', port=2525, toAddr=['test@medicustek.com'],
                fromAddr='norbert@medicustek.com', auth=False, ssl=False, starttls=True)
        ens = EmailNotificationService(settings)

        notification = dict(content='Hello World', title='TEST')
        result = ens.sendNotification(notification)

        sleep(1)
        self.assertTrue(result)
        self.assertTrue(notificationReceived(notification['title']))


    def testSendNotificationUsingSMTPS(self):
        settings = dict(
                server='127.0.0.1', port=4650, toAddr=['test@medicustek.com'],
                fromAddr='norbert@medicustek.com', auth=False, ssl=True, starttls=False)
        ens = EmailNotificationService(settings)

        notification = dict(content='Hello World', title='TEST')
        result = ens.sendNotification(notification)

        sleep(1)
        self.assertTrue(result)
        self.assertTrue(notificationReceived(notification['title']))


if __name__ == '__main__':
    import xmlrunner
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
