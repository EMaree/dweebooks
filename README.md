# dweebooks
A simple twitter bot that tweets at regular intervals and responds to mentions. All tweets are pseudorandom text based on Markov chains of archived tweets.

## Requirements

* Python 2.X
* [tweepy](http://www.tweepy.org)

## Configuration
Before dweebot can connect to twitter successfully, some configuration values must be set in `config.json`. A [sample configuration](config.sample.json) is provided for your convenience. 

### config.sample.json

    {
        "CONSUMER_KEY"          : "",
        "CONSUMER_SECRET"       : "",
        "ACCESS_TOKEN"          : "",
        "ACCESS_TOKEN_SECRET"   : "",
        "URL_TOKENS"            : true,
        "USERNAME_TOKENS"       : false
    }

### API Keys

The following API keys are provided by Twitter when creating a [Twitter App](http://apps.twitter.com). ***Reminder:** Secret keys allow access to your twitter account and should be kept secret. Don't publish them!*

##### CONSUMER_SECRET

This should be the string listed as `API key` under Application settings on the API Keys tab of the Twitter Apps website.

##### CONSUMER_KEY

This should be the string listed as `API secret` under Application settings on the API Keys tab of the Twitter Apps website.

##### ACCESS_TOKEN

This should be the string listed as `Access token` under Your access tokens on the API Keys tab of the Twitter Apps website.

##### ACCESS\_TOKEN_SECRET

This should be the string listed as `Access token secret` under Your access tokens on the API Keys tab of the Twitter Apps website.

### Configuration Options

The following configuration options are also specified within the configuration file:

##### URL_TOKENS

This boolean option controls whether or not previously tweeted URLs contained within the scanned archive should be included when generating new tweets.

- *true* : include URLs
- *false* : don't include URLs

##### USERNAME_TOKENS

This boolean option controls whether or not previously tweeted usernames contained within the scanned archive should be included when generating new tweets.

- *true* : include usernames
- *false* : don't include usernames
