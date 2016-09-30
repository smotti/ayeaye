from os import path, listdir, remove
import sys
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from mtemail import EmailNotificationService
from time import sleep
import unittest
import email
from base64 import b64encode, b64decode


TEST_NOTIFICATION_FILE = './test_notifications/vagrant'
MAIL_USER = 'vagrant'
MAIL_PASSWORD = 'vagrant'


''' Compare the received email with the notification '''
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
        self.assertTrue(notificationReceived(notification))

    def testSendNotificationWithFileNoAuth(self):
        settings = dict(
                server='127.0.0.1', port=2525, toAddr=['test@medicustek.com'],
                fromAddr='norbert@medicustek.com', auth=False, ssl=False, starttls=False)
        ens = EmailNotificationService(settings)

        notification = dict(
                content='Hello World',
                title='TEST',
                attachments=[{"filename": "TestFile1",
                              "content": b64encode(b"This is the content of the file1.").decode('utf-8'),
                              "backup": True},
                             {"filename": "TestFile2",
                              "content": b64encode(b"This is the content of the file2.").decode('utf-8'),
                              "backup": False}])

        result = ens.sendNotification(notification)

        sleep(1)
        self.assertTrue(result)
        self.assertTrue(notificationReceived(notification))


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
        self.assertTrue(notificationReceived(notification))


    def testSendNotificationUsingStartTLS(self):
        settings = dict(
                server='127.0.0.1', port=2525, toAddr=['test@medicustek.com'],
                fromAddr='norbert@medicustek.com', auth=False, ssl=False, starttls=True)
        ens = EmailNotificationService(settings)

        notification = dict(content='Hello World', title='TEST')
        result = ens.sendNotification(notification)

        sleep(1)
        self.assertTrue(result)
        self.assertTrue(notificationReceived(notification))


    def testSendNotificationUsingSMTPS(self):
        settings = dict(
                server='127.0.0.1', port=4650, toAddr=['test@medicustek.com'],
                fromAddr='norbert@medicustek.com', auth=False, ssl=True, starttls=False)
        ens = EmailNotificationService(settings)

        notification = dict(content='Hello World', title='TEST')
        result = ens.sendNotification(notification)

        sleep(1)
        self.assertTrue(result)
        self.assertTrue(notificationReceived(notification))


if __name__ == '__main__':
    import xmlrunner
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
