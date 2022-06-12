import dongReplyBot
import atexit
from flask import Flask,render_template, request
from apscheduler.schedulers.background import BackgroundScheduler

#create flask application
application = Flask(__name__)


#display on webpage
@application.route("/")
def index():
    return "Follow @SyMill_Baseball!"

#call my function
def job():
    dongReplyBot.respond_to_tweet('id.txt')
    print("Success")

#schedule to run every minute
scheduler = BackgroundScheduler()
scheduler.add_job(func=job, trigger="interval", seconds=60)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())


if __name__ == "__main__":
    application.run(port=5000, debug=True)