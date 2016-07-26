from email.mime.text import MIMEText
from error import Error, AuthenticationError, InternalError, MissingAttributeError, \
        UnknownError
from logging import getLogger
import smtplib


LOGGER = getLogger('mtemail')
COMMASPACE = ', '


class EmailNotificationService(object):

    requiredKeys = ['server', 'port', 'toAddr', 'fromAddr', 'ssl', 'auth']

    def __init__(self, settings):
        settingsKeys = settings.keys()
        if any(list(map(lambda k: k not in settingsKeys, self.requiredKeys))):
            raise MissingAttributeError(
                    '''Required attributes: server, port, toAddr, fromAddr, ssl, auth''')

        self.settings = settings
        self.timeout = 10 # In seconds


    def sendNotification(self, notification):
        msg = MIMEText(notification['content'])

        if 'settings' in notification:
            settings = notification['settings']
        else:
            settings = self.settings

        msg['Subject'] = notification['title']
        msg['From'] = settings['fromAddr']
        msg['To'] = COMMASPACE.join(settings['toAddr'])

        # The following code is quite ugly :/. Reminds me of Go :D.
        try:
            if settings['ssl']:
                s = smtplib.SMTP_SSL(host=settings['server'], port=settings['port'],
                        timeout=self.timeout)
            else:
                s = smtplib.SMTP(host=settings['server'], port=settings['port'],
                        timeout=self.timeout)

            if settings['auth'] and ('user' in settings and 'password' in settings):
                s.login(settings['user'], settings['password'])
                raise MissingAttributeError('No user/password supplied')


            s.sendmail(settings['fromAddr'], settings['toAddr'], msg.as_string())
        except smtplib.SMTPConnectError as e:
            LOGGER.error(str(e))
            raise InternalError('Failed to connect to SMTP server')
        except smtplib.SMTPAuthenticationError as e:
            LOGGER.warning(str(e))
            raise AuthenticationError('Failed to authenticate with SMTP server')
        except smtplib.SMTPException as e:
            LOGGER.error(str(e))
            raise InternalError('Something went wrong with sending the email')
        except Error as e:
            LOGGER.warning(str(e))
            raise e
        except Exception as e:
            LOGGER.error(str(e))
            raise UnkownError('Woops, don\'t know what happened :/.')
        else:
            return True
        finally:
            s.quit()
