import sqlite3
import os



class RepoSettings(object):
    """DB connection for settings"""
    def __init__(self):
        self.conn = "private/settings.db"
        if os.path.exists(self.conn) and os.path.getsize(self.conn) > 0:
            pass
        else:
            self.create_db()


    def create_db(self):
        print ("create_db")
        print(self.conn)
        conn = sqlite3.connect(self.conn, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()


    def get_relays(self):
        conn = sqlite3.connect(self.conn, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS relays (
                    name text,
                    pin integer
                    )""")
        c.execute("SELECT * FROM relays")
        relays = c.fetchall()
        conn.close()
        return relays


    def set_relays(self, relays):
        conn = sqlite3.connect(self.conn, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        with conn:
            c.execute("DELETE from relays")
            print(self.conn)
            for relay in relays:
                c.execute("INSERT INTO relays VALUES (:name, :pin)", {'name': relay[0], 'pin': int(relay[1])})
        conn.close()

    def get_dht22s(self):

        conn = sqlite3.connect(self.conn, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS dht22 (
                    name text,
                    pin integer
                    )""")
        c.execute("SELECT * FROM dht22")
        dht22s = c.fetchall()
        conn.close()
        return dht22s


    def set_dht22s(self, dht22s):
        conn = sqlite3.connect(self.conn, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        with conn:
            c.execute("DELETE from dht22")
            print(self.conn)
            for dht22 in dht22s:
                c.execute("INSERT INTO dht22 VALUES (:name, :pin)", {'name': dht22[0], 'pin': int(dht22[1])})
        conn.close()

    def get_miners(self):
        conn = sqlite3.connect(self.conn, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS miners (
                    name text,
                    address text,
                    type text
                    )""")
        c.execute("SELECT * FROM miners")
        miners = c.fetchall()
        conn.close()
        return miners


    def set_miners(self, miners):
        conn = sqlite3.connect(self.conn, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        with conn:
            c.execute("DELETE from miners")
            print(self.conn)
            for miner in miners:
                c.execute("INSERT INTO miners VALUES (:name, :address, :type)", {'name': miner[0], 'address': miner[1], 'type': miner[2]})
        conn.close()
