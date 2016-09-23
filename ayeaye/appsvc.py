from ayeaye.error import InternalError, UnavailableError, NotFoundError, MissingAttributeError
import json
from logging import getLogger
from ayeaye.mtemail import EmailNotificationService
import sqlite3
from base64 import b64decode
import os
from time import time


LOGGER = getLogger('appsvc')


def rowToDict(row):
    aDict = {}
    for k in row.keys():
        aDict.update({k : row[k]})
    return aDict


class GlobalSettingsService(object):

    def __init__(self, db):
        self.db = db


    def getEmailSettings(self):
        try:
            cur = self.db.cursor()
            cur.execute('''
            SELECT settings FROM global_setting JOIN handler_type
                ON global_setting.handler_type = (SELECT id FROM handler_type
                                                    WHERE name = 'email')
            ''')
            settings = cur.fetchone()
        except sqlite3.Error as e:
            LOGGER.error(e)
            raise InternalError(str(e))
        finally:
            cur.close()

        if settings is None:
            return {}
        else:
            return json.loads(settings[0])


    def updateEmailSettings(self, settings):
        try:
            cur = self.db.cursor()
            cur.execute('''
                INSERT OR REPLACE INTO global_setting (handler_type, settings)
                    VALUES ((SELECT id FROM handler_type WHERE name = 'email'),
                            ?)
                ''',
                (json.dumps(settings), ))
            self.db.commit()
        except sqlite3.Error as e:
            LOGGER.error(e)
            raise InternalError(str(e))
        finally:
            cur.close()

        return settings


class NotificationHandlerService(object):

    def __init__(self, db):
        self.db = db


    def getEmailHandlers(self):
        try:
           cur = self.db.cursor()
           cur.execute('''
            SELECT topic, settings FROM handler
                WHERE handler_type = (SELECT id FROM handler_type WHERE name = 'email')
            ''')
           handlers = cur.fetchall()
        except sqlite3.Error as e:
            LOGGER.error(e)
            raise InternalError(str(e))
        finally:
            cur.close()

        if handlers is None:
            return []
        else:
            handlers = [rowToDict(row) for row in handlers]
            for h in handlers:
                if 'settings' in h and h['settings'] is not None:
                    h.update(dict(settings=json.loads(h['settings'])))
            return handlers


    def addEmailHandler(self, handler):
        try:
            cur = self.db.cursor()
            cur.execute('''
                INSERT OR REPLACE INTO handler (topic, handler_type, settings)
                VALUES (?, (SELECT id FROM handler_type WHERE name = 'email'),
                        ?)
                ''',
                (handler['topic'].lower(), json.dumps(handler['settings']), ))
            self.db.commit()
        except sqlite3.Error as e:
            LOGGER.error(e)
            raise InternalError(str(e))
        finally:
            cur.close()

        return handler


    def aEmailHandler(self, topic):
        try:
            cur = self.db.cursor()
            cur.execute(
                    'SELECT topic, settings FROM handler WHERE topic = ?',
                    (topic, ))
            handler = cur.fetchone()
        except sqlite3.Error as e:
            LOGGER.error(e)
            raise InternalError('Failed to get email handler')
        finally:
            cur.close()

        if handler is None:
            return {}
        else:
            handler = rowToDict(handler)
            handler.update(dict(settings=json.loads(handler['settings'])))
            return handler


class NotificationService(object):

    def __init__(self, topic='', database=None, attachmentsDir=None):
        self.db = database
        self.attachmentsDir = attachmentsDir
        self.topic = topic
        # TODO: Would make sense to have a fallback/default notification handler
        if len(topic) > 0:
            self.notificationHandler = self.__getNotificationHandler(topic)
        else:
            self.notificationHandler = None


    def aNotificationHistory(self):
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT time, topic, title, content FROM notification_archive
                    WHERE topic = ?
                ''', (self.topic, ))
            notifications = cur.fetchall()
        except sqlite3.Error as e:
            LOGGER.error(str(e))
            raise InternalError('Failed to get notifications')
        finally:
            cur.close()

        if notifications is None:
            return []
        else:
            return [rowToDict(row) for row in notifications]


    def aNotificationHistoryByTopicAndTime(self, topic, fromTime=None, toTime=None):
        try:
            cur = self.db.cursor()

            if toTime is not None and fromTime is None:
                qry = '''SELECT time, topic, title, content, send_failed
                    FROM notification_archive
                    WHERE topic = ? and time <= ?'''
                cur.execute(qry, (topic, toTime, ))
            elif toTime is not None and fromTime is not None:
                qry = '''SELECT time, topic, title, content, send_failed
                    FROM notification_archive
                    WHERE topic = ? and time >= ? and time <= ?'''
                cur.execute(qry, (topic, fromTime, toTime, ))
            elif toTime is None and fromTime is not None:
                qry = '''SELECT time, topic, title, content, send_failed
                    FROM notification_archive
                    WHERE topic = ? and time >= ?'''
                cur.execute(qry, (topic, fromTime, ))
            else:
                raise MissingAttributeError('Missing fromTime/toTime')

            notifications = cur.fetchall()
        except sqlite3.Error as e:
            LOGGER.error(str(e))
            raise InternalError('Failed to get notifications')
        finally:
            cur.close()

        if notifications is None:
            return []
        else:
            return [rowToDict(row) for row in notifications]


    def aNotificationHistoryByTime(self, fromTime=None, toTime=None, offset=0, limit=-1):
        try:
            cur = self.db.cursor()

            if toTime is not None and fromTime is None:
                qry = '''SELECT id, time, topic, title, content, send_failed
                    FROM notification_archive
                    WHERE time <= ? LIMIT ? OFFSET ?'''
                cur.execute(qry, (toTime, limit, offset))
            elif toTime is not None and fromTime is not None:
                qry = '''SELECT id, time, topic, title, content, send_failed
                    FROM notification_archive
                    WHERE time >= ? and time <= ? ORDER BY time DESC LIMIT ? OFFSET ?'''
                cur.execute(qry, (fromTime, toTime, limit, offset))
            elif toTime is None and fromTime is not None:
                qry = '''SELECT id, time, topic, title, content, send_failed
                    FROM notification_archive
                    WHERE time >= ? ORDER BY time DESC LIMIT ? OFFSET ?'''
                cur.execute(qry, (fromTime, limit, offset))
            else:
                qry = '''SELECT id, time, topic, title, content, send_failed
                    FROM notification_archive ORDER BY time DESC LIMIT ? OFFSET ?'''
                cur.execute(qry, (limit, offset))

            notifications = cur.fetchall()
        except sqlite3.Error as e:
            LOGGER.error(str(e))
            raise InternalError('Failed to get notifications')
        finally:
            cur.close()

        if notifications is None:
            return []
        else:
            return [rowToDict(row) for row in notifications]


    def sendNotification(self, notification):
        if any(list(map(lambda k: k not in notification.keys(), ['title', 'content']))):
            raise MissingAttributeError('Required attributes: title and content')

        try:
            result = self.notificationHandler.sendNotification(notification)
        except Exception as e:
            LOGGER.error(str(e))
            self._archiveNotification(notification, failed=True)
            raise InternalError('Failed to send notification')
        else:
            self._archiveNotification(notification)
        
        if 'attachments' in notification:
            try:
                self._archiveAttachments(notification)
            except Exception as e:
                raise InternalError('Failed to archive attachments: {}'.format(str(e)))


    def _archiveNotification(self, notification, failed=False):
        try:
            cur = self.db.cursor()
            cur.execute('''
                INSERT INTO notification_archive (time, topic, title, content, send_failed)
                    VALUES (?, ?, ?, ?, ?)
                ''', (int(time()), self.topic, notification['title'], notification['content'], failed, ))
            self.db.commit()
        except sqlite3.Error as e:
            LOGGER.error(str(e))
        else:
            return True
        finally:
            cur.close()


    def _archiveAttachments(self, notification):
        dir = os.path.join(self.attachmentsDir, self.topic)
        try:
            os.makedirs(os.path.join(self.attachmentsDir, self.topic), exist_ok=True)
        except Exception as e:
            msg = 'Unable to create directory for storing attachments: {}'.format(str(e))
            LOGGER.error(msg)
            raise InternalError(msg)

        for attachment in notification['attachments']:
            if attachment.get('backup') is True:
                try:
                    fileName = self._incrementNameIfExist(dir, attachment['filename'])
                    fileData = b64decode(attachment['content'])
                    with open(os.path.join(dir, fileName), 'wb') as f:
                        f.write(fileData)
                except Exception as e:
                    msg = 'Unable to store attachment {}: {}'.format(
                            attachment['filename'], str(e))
                    LOGGER.error(msg)
                    raise InternalError(msg)


    def __getNotificationHandler(self, topic):
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT name, settings, handler_type FROM handler JOIN handler_type ON
                    handler.handler_type = handler_type.id
                    WHERE topic = ?
            ''', (topic, ))
            handler = cur.fetchone()
        except sqlite3.Error as e:
            LOGGER.error(str(e))
            raise InternalError(str(e))
        finally:
            cur.close()

        if handler is None:
            raise NotFoundError('No such topic '+topic)

        # If no settings were specified for that handler use the global ones
        if (handler[1] is None) or (len(handler[1]) == 0):
            try:
                cur = self.db.cursor()
                cur.execute('''
                    SELECT settings FROM global_setting WHERE handler_type = ?
                ''', (handler[2], ))
                settings = cur.fetchone()
            except sqlite3.Error as e:
                LOGGER.error(str(e))
                raise InternalError(str(e))
            finally:
                cur.close()

            settings = json.loads(settings[0])
        else:
            settings = json.loads(handler[1])

        if handler[0] == 'email':
            return EmailNotificationService(settings)
        else:
            raise UnavailableError('No notification handler found for topic')


    # Append a number if the file name exists
    # Ex: if 'filename.csv'  exists in path, it will become 'filename_1.csv'
    @staticmethod
    def _incrementNameIfExist(path, fileName):
        if not fileName in os.listdir(path):
            return fileName
        try:
            (name, extension) = fileName.rsplit('.', 1)
            extension = '.' + extension
        except ValueError: # No file extension
            name = fileName
            extension = ''

        duplicatedNumber = 0;
        while True:
            duplicatedNumber += 1;
            fileName = name + '_{}'.format(duplicatedNumber) + extension
            if not fileName in os.listdir(path):
                return fileName
