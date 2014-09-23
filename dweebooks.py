#!/usr/bin/python
"""
A simple twitter bot that tweets at regular intervals and responds to mentions.

Tweets are generated using markov chains based on previous tweets.
"""
import datetime
import glob
import json
import sys
import time
from random import choice

import tweepy


class Dweebooks:
    """Twitter bot that tweets at regular intervals & responds to mentions."""
    def __init__(self):
        self.EOS = [u'.', u'?', u'!']
        self.most_recent_response_id = None

        # Load settings from config.json
        try:
            config = json.load(open('config.json'))
            CONSUMER_KEY = config['CONSUMER_KEY']
            CONSUMER_SECRET = config['CONSUMER_SECRET']
            ACCESS_TOKEN = config['ACCESS_TOKEN']
            ACCESS_TOKEN_SECRET = config['ACCESS_TOKEN_SECRET']
            self.ARCHIVE_PATH = config['ARCHIVE_PATH']
            self.DEBUG = config['DEBUG']
            self.DELAY = 60 * config['DELAY']
            self.URL_TOKENS = config['URL_TOKENS']
            self.USERNAME_TOKENS = config['USERNAME_TOKENS']
            self.REPLY_TO_RETWEETS = config['REPLY_TO_RETWEETS']
        except:
            # TODO: handle file issues and missing settings
            pass

        # Initalize variables used to generate and store markov data
        self.archived_tweets = {}
        self.markov = {}

        # Generate markov dictionary from archived tweets
        self._init_load_archive(self.ARCHIVE_PATH)
        self._init_build_markov_dict()

        # Twitter API Authentication
        self.auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        self.auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        self.username = self.auth.get_username()
        self.api = tweepy.API(self.auth)
        self.listener = None
        self.stream = None

        self._log('Available keys: %s' % len(self.markov.keys()))

    def _init_load_archive(self, files):
        """Load JSON data from tweet archives."""
        tweets = []
        files = glob.glob(files)
        for file in files:
            with open(file) as f:
                d = f.readlines()[1:]  # Twitter's JSON first line is bogus
                d = "".join(d)
                j = json.loads(d)
            for tweet in j:
                tweets.append(tweet)
        self.archived_tweets = sorted(tweets, key=lambda k: k['id'])
        self._log('Found tweets: %s' % len(self.archived_tweets))

    def _init_build_markov_dict(self):
        """Build a Markov chain based on a list of tokens."""
        def _helper_list_tokens_by_tweet(self):
            """Return a nested list of tokens making up each tweet."""
            tokens = []
            for tweet in self.archived_tweets:
                # if len(tweet[u'entities'][u'user_mentions']) == 0:
                temp_tokens = []
                for token in tweet[u'text'].split(' '):
                    if _helper_is_valid_token(self, token):
                        temp_tokens.append(_helper_strip_token(self, token))
                tokens.append(temp_tokens)
            self._log('Usable tweets: %s' % len(tokens))
            return tokens

        def _helper_is_valid_token(self, token):
            """Determine whether a token should be placed in the dictionary."""
            # Filter urls
            if not self.URL_TOKENS and token.lower().startswith(u'http'):
                return False

            # Filter mentions
            if not self.USERNAME_TOKENS and u'@' in token:
                return False

            return True

        def _helper_strip_token(self, token):
            """Remove unwanted characters from an individual token."""
            if any([token.startswith(x) for x in [u'"', u"'", u'(', u' ']]):
                token = token[1:]

            if any([token.startswith(x) for x in [u'"', u"'", u')', u' ']]):
                token = token[:-1]

            return token

        tweet_tokens = _helper_list_tokens_by_tweet(self)
        for tweet in tweet_tokens:
            for i, token in enumerate(tweet):
                try:
                    first, second, third = tweet[i], tweet[i+1], tweet[i+2]
                except IndexError:
                    break

                key = (first, second)
                if key not in self.markov:
                    self.markov[key] = []

                self.markov[key].append(third)

    def _generate_tweet(self, max_length=140):
        """Generate pseudorandom tweets with a maximum length."""
        def _generate_markov_string(self):
            """Generate a string based on the markov dictionary."""
            # Choose a random key to start the chain
            li = [key for key in self.markov.keys()]
            key = choice(li)

            # Add the chosen key and its successor to the string
            first, second = key
            li = []
            li.append(first)
            li.append(second)

            while True:
                # lookup current key in dictionary
                try:
                    third = choice(self.markov[key])
                except KeyError:
                    # no successor found
                    # we've reached the end of this markov chain
                    break

                # successor found, append and check for End-of-String symbols
                li.append(third)
                if len(third) < 1 or third[-1] in self.EOS:
                    break

                # advance key to the next pair of tokens for the next loop
                key = (second, third)
                first, second = key

            return ' '.join(li)

        new_tweet = ''
        while True:
            if len(new_tweet) < 25:            # tweet too short; extend it
                if len(new_tweet) > 0:
                    new_tweet += ' '  # add space prefix for next substring
                new_tweet += _generate_markov_string(self)
            elif len(new_tweet) > max_length:  # tweet too long; start over

                new_tweet = _generate_markov_string(self)
            else:                              # acceptable-length tweet found
                break
        return new_tweet

    def _process_mention(self, status):
        """Reply to a mention status."""
        # don't respond to tweets made by our own account
        if status.user.screen_name == self.username:
            return True

        # TODO: Check for retweets

        self._log('Stream detected mention: ' + status.text)

        # prefix response with mention's username
        new_tweet = '@%s ' % status.user.screen_name

        # add any additional usernames mentioned in the tweet
        for user in status.entities['user_mentions']:
            # don't include ourselves or duplicates of the original author
            if user['screen_name'] != self.username and \
               user['screen_name'] != status.user.screen_name:
                new_tweet += '@%s ' % user['screen_name']

        # generate the response text
        new_tweet += self._generate_tweet(max_length=(140 - len(new_tweet)))

        # make it happen, cap'n
        if not self.DEBUG:
            self.api.update_status(new_tweet, status.id)  # publish reply tweet
        self._log('Tweeting: %s' % new_tweet)             # update log

    def start(self):
        """Start dweebooks bot."""
        self._log('Starting dweebooks...')

        # Setup async StreamListener to monitor mentions
        self.listener = MentionListener(self)
        self.stream = tweepy.Stream(self.auth, self.listener)
        self.stream.userstream(_with='user', replies='all', async=True)

        while True:
            new_tweet = self._generate_tweet()      # generate tweet text
            if not self.DEBUG:
                self.api.update_status(new_tweet)   # publish scheduled tweet
            self._log('Tweeting: %s' % new_tweet)   # update log

            time.sleep(self.DELAY)                 # sleep until next tweet

    def _log(self, msg):
        """Write a message to the dweebooks log."""
        timestamp = datetime.datetime.fromtimestamp(
            time.time()).strftime('%Y-%m-%d %H:%M:%S')

        try:
            print u'[%s] %s' % (timestamp, msg)
        except UnicodeEncodeError:
            print u'Prevented crash from error printing unicode msg!'
        sys.stdout.flush()


class MentionListener(tweepy.StreamListener):
    """ Handle data received from the stream. """
    def __init__(self, bot, *args, **kwargs):
        super(MentionListener, self).__init__(*args, **kwargs)
        self.bot = bot

    def on_status(self, status):
        self.bot.process_mention(status)
        return True  # To continue listening

    def on_error(self, status_code):
        self.bot.log('Got an error with status code: ' + str(status_code))
        return True  # To continue listening

    def on_timeout(self):
        self.bot.log('Timeout...')
        return True  # To continue listening

    def on_friends(self, friends):
        self.bot.log('Received friends list.')
        self.bot.friends = friends
        return True  # To continue listening


def main():
    bot = Dweebooks()
    bot.start()


if __name__ == "__main__":
    main()
