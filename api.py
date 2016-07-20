from error import Error, InternalError
from flask import Flask, request, Response
from functools import wraps
import json
import sqlite3


APP = Flask("notify-svc")

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


# TODO: Right now the database connection is not being closed, but an
# object is created for each individual request.
# See how we can create maybe just one instance (singleton) and if the
# sqlite3 connection is thread-safe.
class GlobalSettingsService(object):

    def __init__(self, db):
        self.db = sqlite3.connect(db)

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


@APP.route('/settings/email', methods=['GET', 'PUT'])
@responseMiddleware
def emailSettings():
    if request.method == 'GET':
        gs = GlobalSettingsService(APP.config['DATABASE'])
        return gs.getEmailSettings()
    elif request.method == 'PUT':
        gs = GlobalSettingsService(APP.config['DATABASE'])
        return gs.updateEmailSettings(request.get_json())
    else:
        return 'no way'
