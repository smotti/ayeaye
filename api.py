from error import Error, InternalError, TeapotError, UnavailableError
from flask import Flask, request, Response, g
from functools import wraps
import json
from mtemail import EmailNotificationService
import sqlite3


APP = Flask("notify-svc")


def runApi(args):
    APP.config['DATABASE'] = args.database
    APP.run(host=args.listen, port=args.port)


def responseMiddleware(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return Response(json.dumps(result), content_type='application/json')
        except Error as e:
            APP.logger.error(e)
            return Response(json.dumps(e.toDict()), status=e.code,
                    content_type='application/json')
        except Exception as e:
            APP.logger.error(e)
            error = InternalError(str(e))
            return Response(json.dumps(error.toDict()), status=error.code,
                    content_type='application/json')
    return wrapper


# We can't rely on the fact that sqlite3 is always compiled for threadsafe
# operations. Thus we either use a queue or use the strange app context,
# which the doc recommends for db connection even though it gets created &
# destroyed for each individual request Oo.
# Go with app context first because it's easier and can also be changed
# easily in the future if we encounter any performance issues.
def getDatabase():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(APP.config['DATABASE'])
    return db


@APP.teardown_appcontext
def teardownDatabase(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


from werkzeug.local import LocalProxy
DATABASE = LocalProxy(getDatabase)


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

        
@APP.route('/settings/email', methods=['GET', 'PUT'])
@responseMiddleware
def settingsEmail():
    if request.method == 'GET':
        gs = GlobalSettingsService(DATABASE)
        return gs.getEmailSettings()
    elif request.method == 'PUT':
        gs = GlobalSettingsService(DATABASE)
        return gs.updateEmailSettings(request.get_json())
    else:
        raise TeapotError('I\'m a teapot')


@APP.route('/handlers/email', methods=['GET', 'POST'])
@responseMiddleware
def handlersEmail():
    if request.method == 'GET':
        nhs = NotificationHandlerService(DATABASE)
        return nhs.getEmailHandlers()
    elif request.method == 'POST':
        nhs = NotificationHandlerService(DATABASE)
        return nhs.addEmailHandler(request.get_json())
    else:
        raise TeapotError('I\'m a teapot')


# TODO: Get a list of all notifications send under the given topic.
@APP.route('/notifications/<topic>', methods=['POST'])
@responseMiddleware
def notificationByTopic(topic=''):
    if request.method == 'POST':
        ns = NotificationService(topic, DATABASE)
        return ns.sendNotification(request.get_json()) 
    else:
        raise TeapotError('I\'m a teapot')
