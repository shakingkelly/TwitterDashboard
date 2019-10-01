from flask import Flask, session, redirect, request, render_template
import tweepy
import logging
from collections import defaultdict
from utils import StreamListener

app = Flask(__name__)
app.secret_key = 'tsdhisiusdfdsfaSecsdfsdfrfghdetkey'
# app.config['SESSION_TYPE'] = 'redis'
# app.config['SECRET_KEY'] = 'redsfsfsfsfis'
# sess = Session()
# sess.init_app(app)

# april's tokens
# access_token = '1106277569752633351-z9XGTbAL7ZxEqT7aToonp8NvO4XuQJ'
# access_token_secret = 'EEKofWc9VV0a4V16wtdAoPSvZHbhZtriyZgKZTf20M7Bq'
# consumer_key = '8lkEPXD9VBXwNxES21RR8k0vZ'
# consumer_secret = 'hkLL9WWMnhbz7trMlfIOgzyctXayT1ZzUYilmdWi16xEhJs4FM'

# kelly's tokens
access_token = '364156861-cSyt6v8Rjg4n8aVxRqI7stklhtvv69raNR7X3Tp9'
access_token_secret = 'q9AppxYixPtI7HAi4Fxxd2i6Nl6ESGDqzCVqVOOFjr0FB'
consumer_key = '0IvIaXCm8CUHeuayBiFS3Blwd' 
consumer_secret = 'WlgHUfC7waVlRrktuyySBRQHwVSBPFpxEud2hGY08i83NFXpNk'

callback_uri = 'https://twitterdashboard.appspot.com/callback'
request_token_url = 'https://api.twitter.com/oauth/request_token'
authorization_url = 'https://api.twitter.com/oauth/authorize'
access_token_url = 'https://api.twitter.com/oauth/access_token'


@app.route('/', methods=['POST', 'GET'])
def index():
    title = 'TwitterDashboardHomePage'
    return render_template('index.html', title=title)


@app.route("/login", methods=['POST', 'GET'])
def login():
    # should redirect to app if it's not user's first visit
    # get stored username and password from datastore
    error = None
    return redirect('/app', error=error)


@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        # get username and password from request.form
        session['username'] = request.form.get('username')
        session['password'] = request.form.get('password')

        print('username:', session['username'])
        print('password:', session['password'])

        # save to our database, it's the login info for our service

        return redirect('/auth')
    return render_template('register.html', error=None)


@app.route("/auth", methods=['POST', 'GET'])
def auth():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_uri)
    redirect_url = auth.get_authorization_url()

    logging.info(redirect_url)
    logging.info(auth.request_token)

    # print(redirect_url)
    # print(auth.request_token)

    session['request_token'] = auth.request_token
    return redirect(redirect_url)


@app.route("/callback", methods=['POST', 'GET'])
def callback():
    request_token = session['request_token']
    del session['request_token']
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_uri)
    auth.request_token = request_token
    verifier = request.args.get('oauth_verifier')
    logging.info(verifier)
    auth.get_access_token(verifier)
    session['token'] = (auth.access_token, auth.access_token_secret)
    print(auth.access_token, auth.access_token_secret)

    # save access_token, access_token_secret to datastore for reuse

    return redirect('/app')


@app.route('/app') # rate limit, might use stream api
def get_tweets():
    # user's first visit to our service
    # redirected from auth
    # get tokens directly from session 
    print(request.referrer)
    # if request.referrer == 'auth':
    if session['token']:
        token, token_secret = session['token']
    else:
        # query tokens from datastore with session username and password

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
    auth.set_access_token(token, token_secret)
    api = tweepy.API(auth)

    # set up streaming api
    # using username as screen_name, have to ensure they are the same!!
    if not session['token']:
        print('start streaming')
        stream = tweepy.Stream(auth=api.auth, listener=StreamListener())
        user = api.get_user(screen_name=screen_name)
        stream.filter(follow=[user.id_str], is_async=True)

        # save to datastore
        # change in StreamListener class

    # search api
    # get initial tweets for labeling
    if session['token']:
    tweets = api.user_timeline(screen_name=session['username'], count=200) # max count
    tweet_replies = []
    
    for tweet in tweets:
        tmp = {}
        tmp['tid'] = tweet.id
        tmp['context'] = tweet.text
        tmp['hashtag'] = tweet.entities['hashtags']
        tmp['reply'] = []
        for reply in tweepy.Cursor(api.search, q=session['username'], since_id=tweet.id_str, result_type="mixed", count=10).items(10):
            tmp['reply'].append({'uid': reply.user.id, 'uname': reply.user.name, 'reply': reply.text})
            tweet_replies.append(tmp)

    # save to db and display for labeling

    return render_template('app.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
