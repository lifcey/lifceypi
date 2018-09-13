import sqlite3

class RepoUsers(object):
    """DB connection for users"""
    def __init__(self):
        self.conn = "users.db"

    def validate_user(self, username, password):
        conn = sqlite3.connect(self.conn, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE login=:login", {'login': username})
        fetched_user = c.fetchone()
        conn.close()

        if fetched_user is not None:
            if fetched_user[1] == password:
                return True
        return False

    def is_admin(self, username):
        conn = sqlite3.connect(self.conn, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE login=:login", {'login': username})
        fetched_user = c.fetchone()
        conn.close()

        if fetched_user is not None:
            if fetched_user[2] == 1:
                return True
        return False
