#!/usr/bin/env python3

from os import environ
import sqlite3
from sys import exit


AYEAYE_DB = environ.get('AYEAYE_DB', '/srv/ayeaye/ayeaye.db')
# See the sqlite docs on what are valid retention periods:
# https://www.sqlite.org/lang_datefunc.html
RETENTION_PERIOD = environ.get('RETENTION_PERIOD', '-30 days')


if __name__ == '__main__':
    try:
        conn = sqlite3.connect(AYEAYE_DB)
    except Exception as e:
        print('[E] Failed connecting to database: {}'.str(e))
        exit(1)
    else:
        try:
            cur = conn.cursor()
            cur.execute("""DELETE FROM notification_archive 
                WHERE datetime(time, 'unixepoch') <= datetime('now', '{}')""".format(
                    RETENTION_PERIOD))
            conn.commit()
        except Exception as e:
            print('[E] Failed deleting notifications: {}'.str(e))
            exit(1)
        else:
            print('[I] Purged notifications older than {}'.format(RETENTION_PERIOD.lstrip('-')))
            exit(0)
    finally:
        cur.close()
        conn.close()
