from audioop import avg
import tweepy
import logging
import pymysql
import time
import config

# Authenticate to Twitter
consumer_key = config.api_key
consumer_secret = config.api_secret
access_token= config.access_token
access_secret = config.token_secret

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth)



client = tweepy.Client(access_token=config.access_token, access_token_secret=config.token_secret, consumer_key=config.api_key, consumer_secret=config.api_secret)



logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)

#switch cases for emojis
def get_emoji(play_result):
    if play_result == "Single":
        return "\U000026be"
    elif play_result == "Double":
        return "\U0001f3c3\U0001f4a8"
    elif play_result == "Triple":
        return "\U0001f3c7\U0001f4a8"
    elif play_result == "Lineout":
        return "\U0001f3af"
    elif play_result == "Flyout":
        return "\U0001f4a2"
    elif play_result == "Pop Out":
        return "\U0001f6ab"
    elif play_result == "Double Play":
        return "\U0001f3af\U0001f3af",
    elif play_result == "Sac Fly":
        return "\U0001f64c"
    elif play_result == "Fielders Choice":
        return "\U0001f937"
    elif play_result == "Field Error":
        return "\U000026a0"
    elif play_result == "Sac Fly Double Play":
        return "\U0001f64c\U0001f3af\U0001f3af",
    elif play_result == "Fielders Choice Out":
        return "\U0001f937\U0001f3af"
    else:
        return "\U000026be"


def get_last_tweet(file):
    f = open(file, 'r')
    lastId = int(f.read().strip())
    f.close()
    return lastId

def put_last_tweet(file, Id):
    f = open(file, 'w')
    f.write(str(Id))
    f.close()
    logger.info("Updated the file with the latest tweet Id")
    return

#here we go...
def respond_to_tweet(file="id.txt"):
    conn = pymysql.connect(
        host= config.host, 
        port = config.port,
        user = config.user, 
        password = config.password,
        db = config.db,
        )
    cur = conn.cursor()
    #grab last tweet replied to
    last_id = get_last_tweet(file)
    tweets = api.user_timeline(user_id='1392540526465806338', since_id=last_id, count = 200, tweet_mode='extended', include_rts=False)

    #check if any new tweets
    if len(tweets) == 0:
        return
    

    new_id = 0
    logger.info("time to respond to tweets!")

    #this is long...
    for tweet in reversed(tweets):
        logger.info(str(tweet.id) + '-' + tweet.full_text)

        #set current tweet id
        new_id = tweet.id

        #get name, hashtag, play result, emoji, etc
        name = tweet.full_text.split('vs')[0].strip()
        text = tweet.full_text
        hashtag=text.split('#')[1].split()[0].strip()
        result = text.split("#")[1].split()[1].strip()
        text=text.lower()
        emoji = get_emoji(result)
        velo = float(text.split('exit velo:')[1].split()[0].strip())
        ang = float(text.split('launch angle:')[1].split()[0].strip())
        dist = float(text.split('proj. distance:')[1].split()[0].strip())

        print(name)

        logger.info("Liking tweet...")
        # api.create_favorite(tweet.id)

        #check if HR emoji in tweet
        if '\U0001f4a3' in text:
            avg_hr_inc = 0

            if '\U0001f984' in text:
                avg_hr_inc = 1
                emoji = "\U0001f984"
            elif '\U0001f512' in text:
                avg_hr_inc = 30
                emoji = "\U0001f512"
            else:
                avg_hr_inc = int(text.split('/')[0].split()[-1])
                emoji = "\U0001f4a3"

            try:
                cur.execute('SELECT count, avg_park, avg_velo, avg_angle, avg_dist FROM HRTracker WHERE name = %s', (name,))
                tup=cur.fetchone()

                hr=tup[0]
                hr_avg= (tup[1]*hr+avg_hr_inc)/(hr+1)
                avg_velo=(tup[2]*hr+velo)/(hr+1)
                avg_ang=(tup[3]*hr+ang)/(hr+1)
                avg_dist=(tup[4]*hr+dist)/(hr+1)

                cur.execute('''UPDATE HRTracker 
                            SET count = %s, avg_park = %s, avg_velo=%s,avg_angle=%s,avg_dist=%s 
                            WHERE name = %s''', 
                            (hr, hr_avg, avg_velo, avg_ang, avg_dist, name))
                tweet = '''{} HR on the season for {} #{}

Each Home Run for {} has...
AVG Exit Velo: {} mph
AVG Launch Angle: {} deg
AVG Proj. Distance: {} ft
Would dong in {}/30 MLB ballparks

Automated Reply from @SyMill_Baseball'''.format(str(hr), name, hashtag, name, str(round(avg_velo, 2)), str(round(avg_ang, 2)), str(round(avg_dist, 2)), str(round(hr_avg, 2)))

            except:
                hr=1
                hr_avg= avg_hr_inc
                cur.execute('''INSERT IGNORE INTO HRTracker (name, count, avg_park,avg_velo,avg_angle,avg_dist) 
                            VALUES (%s,%s,%s,%s,%s,%s)''',
                            (name, hr, hr_avg, velo, ang, dist))
                tweet='''That's the FIRST {}Home Run{} of the Season for {} #{}

Automated Reply from @SyMill_Baseball'''.format(emoji, emoji, name, hashtag)

        #otherwise...
        else:
            avg_hr_inc = 0
            if '\U0001f984' in text:
                avg_hr_inc = 29
            elif 'nowhere else' in text:
                avg_hr_inc = 1
            else:
                avg_hr_inc = int(text.split('/')[0].split()[-1])
            
            #if in db
            try:
                #get current stats from db
                cur.execute('SELECT count, avg_park, avg_velo, avg_angle, avg_dist FROM NoHRTracker WHERE name = %s', (name,))
                tup=cur.fetchone()

                #calculate averages
                no_hr=tup[0]
                no_hr_avg= (tup[1] * no_hr + avg_hr_inc) / (no_hr+1) 
                avg_velo=(tup[2]*no_hr+velo)/(no_hr+1)
                avg_ang=(tup[3]*no_hr+ang)/(no_hr+1)
                avg_dist=(tup[4]*no_hr+dist)/(no_hr+1)
                no_hr += 1

                #update table
                cur.execute('''UPDATE NoHRTracker 
                            SET count = %s, avg_park = %s, avg_velo=%s,avg_angle=%s,avg_dist=%s 
                            WHERE name = %s''', 
                            (no_hr, no_hr_avg, avg_velo, avg_ang, avg_dist, name))


            #if not in db
            except:
                no_hr=1
                no_hr_avg = avg_hr_inc
                avg_velo = velo
                avg_ang = ang
                avg_dist = dist

                #insert into tracker
                cur.execute('''INSERT IGNORE INTO NoHRTracker (name, count, avg_park,avg_velo,avg_angle,avg_dist) 
                            VALUES (%s,%s,%s,%s,%s,%s)''',
                            (name, no_hr, no_hr_avg, avg_velo, avg_ang, avg_dist))

            #format tweet!
            tweet = '''{} missed dongs on the season for {} #{}

Each Non HR for {} has...
AVG Exit Velo: {} mph
AVG Launch Angle: {} deg
AVG Proj. Distance: {} ft
Would dong in {}/30 MLB ballparks

Automated Reply from @SyMill_Baseball'''.format(str(no_hr), name, hashtag, name, str(round(avg_velo, 2)), str(round(avg_ang, 2)), str(round(avg_dist, 2)), str(round(no_hr_avg, 2))) 
 
        #finally tweet!
        logger.info("Tweeting!")
        client.create_tweet(text=tweet, user_auth=True, quote_tweet_id=new_id)

        #update last tweet
        put_last_tweet(file, new_id)

        #commit changes and wait to tweet again (<3 rate limits)
        conn.commit()
        time.sleep(12)
        logger.info('Sleeping...')
        
    conn.close()







if __name__=="__main__":
    respond_to_tweet()