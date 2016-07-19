from flask import Flask


APP = Flask("notify-svc")


@APP.route('/handlers/email')
def emailHandler():
    APP.logger.info('REQUEST')
    return 'Hello world'
