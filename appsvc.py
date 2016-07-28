from error import InternalError, UnavailableError, NotFoundError
import json
from logging import getLogger
from mtemail import EmailNotificationService
import sqlite3
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
            SELECT * FROM handler
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
            return handlers


    def addEmailHandler(self, handler):
        try:
            cur = self.db.cursor()
            cur.execute('''
                INSERT INTO handler (topic, handler_type, settings)
                VALUES (?, (SELECT id FROM handler_type WHERE name = 'email'),
                        ?)
                ''',
                (handler['topic'], json.dumps(handler['settings']), ))
            self.db.commit()
        except sqlite3.Error as e:
            LOGGER.error(e)
            raise InternalError(str(e))
        finally:
            cur.close()

        return handler


class NotificationService(object):

    def __init__(self, topic='', database=None):
        self.db = database
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
                qry = '''SELECT time, topic, title, content FROM notification_archive
                    WHERE topic = ? and time <= ?'''
                cur.execute(qry, (topic, toTime, ))
            elif toTime is not None and fromTime is not None:
                qry = '''SELECT time, topic, title, content FROM notification_archive
                    WHERE topic = ? and time >= ? and time <= ?'''
                cur.execute(qry, (topic, fromTime, toTime, ))
            elif toTime is None and fromTime is not None:
                qry = '''SELECT time, topic, title, content FROM notification_archive
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


    def aNotificationHistoryByTime(self, fromTime=None, toTime=None):
        try:
            cur = self.db.cursor()

            if toTime is not None and fromTime is None:
                qry = '''SELECT time, topic, title, content FROM notification_archive
                    WHERE time <= ?'''
                cur.execute(qry, (toTime, ))
            elif toTime is not None and fromTime is not None:
                qry = '''SELECT time, topic, title, content FROM notification_archive
                    WHERE time >= ? and time <= ?'''
                cur.execute(qry, (fromTime, toTime, ))
            elif toTime is None and fromTime is not None:
                qry = '''SELECT time, topic, title, content FROM notification_archive
                    WHERE time >= ?'''
                cur.execute(qry, (fromTime, ))
            else:
                 qry = '''SELECT time, topic, title, content FROM notification_archive'''
                 cur.execute(qry)
            
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
        try:
            self._archiveNotification(notification)
        except Exception as e:
            LOGGER.error(str(e))

        return self.notificationHandler.sendNotification(notification)


    def _archiveNotification(self, notification):
        if any(list(map(lambda k: k not in notification.keys(), ['title', 'content']))):
            raise MissingAttributeError('Required attributes: title and content')

        try:
            cur = self.db.cursor()
            cur.execute('''
                INSERT INTO notification_archive (time, topic, title, content)
                    VALUES (?, ?, ?, ?)
                ''', (int(time()), self.topic, notification['title'], notification['content'], ))
            self.db.commit()
        except sqlite3.Error as e:
            LOGGER.error(str(e))
            raise InternalError(str(e))
        else:
            return True
        finally:
            cur.close()


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
