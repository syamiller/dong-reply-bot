import tweepy
import config
import pymysql

conn = pymysql.connect(
        host= config.host, 
        port = config.port,
        user = config.user, 
        password = config.password,
        db = config.db,
        )
cur = conn.cursor()

cur.execute('UPDATE HRTracker SET count = 18 WHERE name = %s',('Pete Alonso',))
