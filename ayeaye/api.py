from ayeaye.appsvc import GlobalSettingsService, NotificationHandlerService, \
    NotificationService
from ayeaye.error import Error, InternalError, TeapotError, NotFoundError, BadRequestError
from flask import Flask, request, Response, g
from flask_cors import CORS
from functools import wraps
import json
from logging import getLogger
import sqlite3


LOGGER = getLogger('api')
APP = Flask("ayeaye")
CORS(APP)

def runApi(args):
    APP.config['DATABASE'] = args.database
    APP.config['MAX_CONTENT_LENGTH'] = args.maxLen * 1024 * 1024
    APP.config['ATTACHMENTS_DIR'] = args.attachmentsDir
    APP.run(host=args.listen, port=args.port)


def responseMiddleware(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if isinstance(result, (dict, list)):
                return Response(json.dumps(result), content_type='application/json')
            else:
                return Response(content_type='application/json')
        except Error as e:
            LOGGER.error(e)
            return Response(json.dumps(e.toDict()), status=e.code,
                    content_type='application/json')
        except Exception as e:
            LOGGER.error(e)
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
        db.row_factory = sqlite3.Row
    return db


@APP.teardown_appcontext
def teardownDatabase(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


from werkzeug.local import LocalProxy
DATABASE = LocalProxy(getDatabase)


@APP.errorhandler(404)
@responseMiddleware
def pageNotFound(e):
    raise NotFoundError('The endpoint you\'re trying to reach is not found.')


@APP.errorhandler(405)
@responseMiddleware
def methodNotFound(e):
    raise NotFoundError('The endpoint you\'re trying to reach is not found.')


@APP.errorhandler(500)
@responseMiddleware
def internalError(e):
    raise InternalError('Oops...Something went wrong')


@APP.errorhandler(418)
@responseMiddleware
def teapot():
    return TeapotError('''I'm a teapot.''')


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


# TODO: We need to be able to update an individual handler.
# Or we also turn it into PUT only like /settings/email.
@APP.route('/handlers/email', methods=['GET', 'POST'])
@responseMiddleware
def handlersEmail():
    if request.method == 'GET':
        nhs = NotificationHandlerService(DATABASE)
        return nhs.getEmailHandlers()
    elif request.method == 'POST':
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError('Data must be provided in JSON format.')

        nhs = NotificationHandlerService(DATABASE)
        return nhs.addEmailHandler(json_data)
    else:
        raise TeapotError('I\'m a teapot')


@APP.route('/handlers/email/<topic>', methods=['GET', 'PUT'])
@responseMiddleware
def emailHandlerByTopic(topic=''):
    if request.method == 'GET':
        nhs = NotificationHandlerService(DATABASE)
        return nhs.aEmailHandler(topic)
    elif request.method == 'PUT':
        handler = request.get_json()
        if handler is None:
            raise BadRequestError('Data must be provided in JSON format.')

        nhs = NotificationHandlerService(DATABASE)
        handler.update({'topic': topic})
        return nhs.addEmailHandler(handler)


@APP.route('/notifications/', methods=['GET','DELETE'])
@responseMiddleware
def notifications():
    if request.method == 'GET':
        ns = NotificationService(database=DATABASE)
        args = request.args.to_dict()
        timeRange = {}
        list(map(
            lambda t: timeRange.update({t[0] : t[1]}),
            [t for t in args.items() if t[0] in ['fromTime', 'toTime', 'offset',  'limit']]))
        return ns.aNotificationHistoryByTime(**timeRange)
    elif request.method == 'DELETE':
        ns = NotificationService(database=DATABASE)
        ns.deleteAllNotifications()
    else:
        raise TeapotError('I\'m a teapot')


@APP.route('/notifications/<topic>', methods=['POST', 'GET'])
@responseMiddleware
def notificationByTopic(topic=''):
    if request.method == 'POST':
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError('Data must be provided in JSON format.')

        ns = NotificationService(topic, DATABASE, attachmentsDir=APP.config['ATTACHMENTS_DIR'])
        return ns.sendNotification(json_data)
    elif request.method == 'GET':
        ns = NotificationService(topic, DATABASE)
        args = request.args.to_dict()
        if 'fromTime' in args or 'toTime' in args:
            timeRange = {}
            list(map(
                lambda t: timeRange.update({t[0] : t[1]}),
                [t for t in args.items() if t[0] in ['fromTime', 'toTime']]))
                # from time to time teehee
            return ns.aNotificationHistoryByTopicAndTime(topic, **timeRange)
        else:
            return ns.aNotificationHistory()
    else:
        raise TeapotError('I\'m a teapot')
