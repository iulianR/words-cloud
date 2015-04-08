#!/usr/bin/python
import tweepy
import json
import time
import sys
import redis

consumer_key = "8adGill0tekm7zRcBlrBWzLaM"
consumer_secret = "2B876ONhUv6yQGbEYNlz8K2RT4MeAV2R03fgJ3mlhIVZgnjcAj"

tweets = []


class MyStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        tweets.append(status.text)


def auth():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError:
        print ("Error! Failed to get authorization url")

    print("Enter the following URL in your browser and authorize the " +
          "application: \n" + redirect_url + "\n")

    verifier = input("Verifier: ")
    try:
        (access_token, access_token_secret) = auth.get_access_token(str (verifier))
    except tweepy.TweepError:
        print ("Error! Failed to get access_token")

    auth.set_access_token (access_token, access_token_secret)
    return tweepy.API(auth)


def get_stopwords ():
    """ Creates the stopwords list by reading the words from the file """
    stopwords = []
    with open('stopwords.txt', 'r') as f:
        for line in f:
            stopwords.append(line.strip('\n'))

    return stopwords


def create_stream(api):
    myStreamListener = MyStreamListener()
    return tweepy.Stream(auth=api.auth, listener=myStreamListener)


def get_json(r, stopwords, length):
    r.flushdb()
    r.hset("cloud", "other", 0)
    for e in tweets:
        words = e.split(' ')
        for word in words:
            word = word.lower()
            if word in stopwords:
                continue

            if r.hlen("cloud") < int (length):
                r.hincrby("cloud", word, 1)
            else:
                r.hincrby("cloud", "other", 1)

    return [{"word": word, "count": int (count)} for word, count in r.hgetall("cloud").items()]


def main(seconds, length):
    api = auth()
    stopwords = get_stopwords ()
    stream = create_stream (api)

    stream.sample(languages=['en'], async=True)
    time.sleep(int(seconds))
    stream.disconnect()

    r = redis.StrictRedis(host='redis', port=6379, db=0)
    json_text = get_json(r, stopwords, length)

    print(json_text)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2])
    else:
        print("Please specify the command line arguments")
