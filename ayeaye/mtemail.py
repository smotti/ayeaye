from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from ayeaye.error import Error, AuthenticationError, InternalError, MissingAttributeError, \
        UnknownError
from logging import getLogger
from os.path import basename
import smtplib
import ssl


LOGGER = getLogger('mtemail')
COMMASPACE = ', '


class EmailNotificationService(object):

    requiredKeys = ['server', 'port', 'toAddr', 'fromAddr', 'ssl', 'auth',
            'starttls']

    def __init__(self, settings):
        settingsKeys = settings.keys()
        if any(list(map(lambda k: k not in settingsKeys, self.requiredKeys))):
            raise MissingAttributeError(
                    '''Required attributes: server, port, toAddr, fromAddr, ssl, auth, starttls''')

        self.settings = settings
        self.timeout = 10 # In seconds


    def sendNotification(self, notification):
        msg = MIMEMultipart()

        msg['Subject'] = notification['title']
        msg['From'] = self.settings['fromAddr']
        msg['To'] = COMMASPACE.join(self.settings['toAddr'])
        msg.attach(MIMEText(notification['content']))

        if 'attachments' in notification and type(notification['attachments']) is list :
            for file in notification['attachments']:
                with open(file) as f:
                    file_cont = f.read()
                    file_basename = basename(file)
                    part = MIMEApplication(file_cont, name=file_basename)
                    part['Content-Diposition'] = 'attachment; filename="%s"' % file_basename
                    msg.attach(part)

        try:
            s = None

            if self.settings['ssl'] and not self.settings['starttls']:
                s = smtplib.SMTP_SSL(host=self.settings['server'],
                        port=self.settings['port'], timeout=self.timeout)
            else:
                s = smtplib.SMTP(host=self.settings['server'], port=self.settings['port'],
                        timeout=self.timeout)

            if self.settings['starttls']:
                s.starttls()

            if self.settings['auth']:
                if 'user' in self.settings and 'password' in self.settings:
                    s.login(self.settings['user'], self.settings['password'])
                else:
                    raise MissingAttributeError('No user/password supplied')

            s.sendmail(self.settings['fromAddr'], self.settings['toAddr'], msg.as_string())
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
            raise UnknownError('Oops, ... Something went wrong!')
        else:
            return True
        finally:
            if s is not None:
                s.quit()
