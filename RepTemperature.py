import sqlite3

class RepTemperature(object):
    """DB connection for temerature log"""
    def __init__(self, dbname):
        self.conn = dbname

    def get_current_temperatures():
