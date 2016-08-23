import sqlite3
from os.path import realpath


def initializeDatabase(databasePath):
    schemaPath = realpath(__file__).rsplit('/', 1)[0] + '/' + 'schema.sql'
    with open(schemaPath, 'r', encoding='utf-8') as f:
        schema = f.read()

    try:
        db = sqlite3.connect(databasePath)
        db.executescript(schema)
    except:
        raise
    finally:
        db.close()

    return True
