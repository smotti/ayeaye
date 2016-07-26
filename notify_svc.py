#!/usr/bin/env python

from api import runApi
from argparse import ArgumentParser
import logging
from os import _exit
from os.path import realpath
import sqlite3
from sys import exit, stdout


LOG_FMT = '%(levelname)s %(asctime)s %(name)s %(filename)s:%(lineno)d %(message)s'
LOG_DATEFMT = '%Y-%m-%dT%H:%M:%SZ'


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


if __name__ == '__main__':
    # Parse cli arguments
    parser = ArgumentParser()
    parser.add_argument('-l', '--listen', type=str, default='127.0.0.1',
            help='IP address the HTTP REST API should listen on')
    parser.add_argument('-p', '--port', type=int, default=5000,
            help='The port of the HTTP REST API')
    parser.add_argument('-d', '--database', type=str, default='./notify-svc.db',
            help='Path to the sqlite3 database', metavar='PATH')
    parser.add_argument('-v', '--verbose', help='Verbose output',
            action='store_true')
    args = parser.parse_args()

    # Configure the logger. We log to stdout by default to simplefy things.
    # One can pipe stdout to a file and use logrotate with copytruncate option.
    # Note that also errors will be piped to stdout, though it's adviced
    # to pipe stderr also to the same location as stdout (i.e. app > log 2>&1)
    rootLogger = logging.getLogger()
    stdoutLogger = logging.StreamHandler(stdout)
    if args.verbose:
        rootLogger.setLevel(logging.DEBUG)
        stdoutLogger.setLevel(logging.DEBUG)
    else:
        rootLogger.setLevel(logging.INFO)
        stdoutLogger.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt=LOG_FMT,datefmt=LOG_DATEFMT)
    stdoutLogger.setFormatter(formatter)
    rootLogger.addHandler(stdoutLogger)

    # Initialize the database and create it, if it doesn't exist yet.
    try:
        initializeDatabase(args.database)
    except sqlite3.Error as e:
        rootLogger.error(e)
        rootLogger.error('Failed to initialize/create database')
        try:
            exit(1)
        except SystemExit:
            _exit(1)

    # Run the http api.
    try:
        runApi(args)
    except Exception as e:
        rootLogger.error(e)
        rootLogger.error('Failed to start HTTP API')

    exit(0)
