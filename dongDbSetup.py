import os
import collections
import tweepy
import time
import pymysql
import config

#authenticate to twitter
consumer_key = config.api_key
consumer_secret = config.api_secret
access_token= config.access_token
access_secret = config.token_secret

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth)
client = tweepy.Client(bearer_token= config.bearer_token)

#connect to db
conn = pymysql.connect(
        host= config.host, 
        port = config.port,
        user = config.user, 
        password = config.password,
        db = config.db,
        )
cur = conn.cursor()

#create tables
cur.execute("CREATE TABLE IF NOT EXISTS HRTracker (name varchar(200) UNIQUE, count INTEGER, avg_park REAL, avg_velo REAL, avg_angle REAL, avg_dist REAL)")
cur.execute("CREATE TABLE IF NOT EXISTS NoHRTracker (name varchar(200) UNIQUE, count INTEGER, avg_park REAL, avg_velo REAL, avg_angle REAL, avg_dist REAL)")
conn.commit()

#a bunch of dictionaries
d_hr = {}
d_avg_hr = collections.defaultdict(list)
d_avg_no_hr = collections.defaultdict(list)
d_avg_velo = collections.defaultdict(list)
d_avg_no_velo = collections.defaultdict(list)
d_avg_ang = collections.defaultdict(list)
d_avg_no_ang = collections.defaultdict(list)
d_avg_dist = collections.defaultdict(list)
d_avg_no_dist = collections.defaultdict(list)
d_no_hr = {}

#handle all the different tweets

for tweet in tweepy.Paginator(client.get_users_tweets, "1392540526465806338", start_time="2022-04-01T00:00:00.00Z", max_results=100).flatten():
    #get name, text, velo, etc
    name = tweet.text.split('vs')[0].strip()
    text = tweet.text.lower()
    velo = float(text.split('exit velo:')[1].split()[0].strip())
    ang = float(text.split('launch angle:')[1].split()[0].strip())
    dist = float(text.split('proj. distance:')[1].split()[0].strip())

    #check if hr emoji in tweet
    if '\U0001f4a3' in text:

        #check if unicorn
        if '\U0001f984' in text:
            d_avg_hr[name].append(1)

        #check if no doubter
        elif '\U0001f512' in text:
            d_avg_hr[name].append(30)

        #otherwise get amount of parks would dong
        else:
            num = int(text.split('/')[0].split()[-1])
            d_avg_hr[name].append(num)

        #update the dictionaries
        d_hr[name] = d_hr.get(name, 0) + 1
        d_avg_velo[name].append(velo)
        d_avg_ang[name].append(ang)
        d_avg_dist[name].append(dist)


    else:
        #check if unicorn
        if '\U0001f984' in text:
            d_avg_no_hr[name].append(29)

        #check if only 1 ballpark
        elif 'nowhere else' in text:
            d_avg_no_hr[name].append(1)

        #otherwise get amount of parks would dong
        else:
            num = int(text.split('/')[0].split()[-1])
            d_avg_no_hr[name].append(num)

        #update dictionaries
        d_no_hr[name] = d_no_hr.get(name, 0) + 1
        d_avg_no_velo[name].append(velo)
        d_avg_no_ang[name].append(ang)
        d_avg_no_dist[name].append(dist)

#iterate through HR dicts and insert into db
for name in d_hr.keys():
    avg_hr = sum(d_avg_hr[name]) / d_hr[name]
    avg_velo=sum(d_avg_velo[name])/d_hr[name]
    avg_dist=sum(d_avg_dist[name])/d_hr[name]
    avg_ang=sum(d_avg_ang[name])/d_hr[name]
    cur.execute("""INSERT IGNORE INTO HRTracker (name, count, avg_park, avg_velo, avg_angle, avg_dist) 
                VALUES (%s,%s,%s,%s,%s,%s)""", 
                (name, d_hr[name], avg_hr, avg_velo, avg_ang, avg_dist))

#do the same for No HR dicts
for name in d_no_hr.keys():
    avg_no = sum(d_avg_no_hr[name])/d_no_hr[name]
    avg_no_velo=sum(d_avg_no_velo[name])/ d_no_hr[name]
    avg_no_dist=sum(d_avg_no_dist[name])/d_no_hr[name]
    avg_no_ang=sum(d_avg_no_ang[name])/d_no_hr[name]
    cur.execute("""INSERT IGNORE INTO NoHRTracker (name, count, avg_park, avg_velo, avg_angle, avg_dist) 
            VALUES (%s,%s,%s,%s,%s,%s)""", 
            (name, d_no_hr[name], avg_no, avg_no_velo, avg_no_ang, avg_no_dist))

#commit all changes
conn.commit()