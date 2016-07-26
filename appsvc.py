from error import InternalError, UnavailableError, NotFoundError
import json
from mtemail import EmailNotificationService
import sqlite3


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
            APP.logger.error(e)
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
            APP.logger.error(e)
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
            APP.logger.error(e)
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
            APP.logger.error(e)
            raise InternalError(str(e))
        finally:
            cur.close()

        return handler


class NotificationService(object):

    def __init__(self, topic, database):
        self.db = database
        self.topic = topic
        self.notificationHandler = self.__getNotificationHandler(topic)


    def sendNotification(self, notification):
        return self.notificationHandler.sendNotification(notification)


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
            APP.logger.error(str(e))
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
                APP.logger.error(str(e))
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
