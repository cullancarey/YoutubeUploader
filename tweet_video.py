# -*- coding: utf-8 -*-

# Sample Python code for youtube.videos.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/guides/code_samples#python

import os
import sys
import json
import googleapiclient.discovery
import googleapiclient.errors
from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow
import http.client
import httplib2
import tweepy
from datetime import datetime
from dotenv import load_dotenv
import boto3
import shutil
from dateutil.tz import gettz
load_dotenv()

shutil.copy(f"{os.getcwd()}/tmp/tweet_video.py-oauth2.json", "/tmp/tweet_video.py-oauth2.json")

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
                        http.client.IncompleteRead, http.client.ImproperConnectionState,
                        http.client.CannotSendRequest, http.client.CannotSendHeader,
                        http.client.ResponseNotReady, http.client.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

CLIENT_SECRETS_FILE = f"{os.getcwd()}/client_secrets.json"

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of
# access.
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

 %s

with information from the API Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))


def get_authenticated_service():
    httplib2.RETRIES = 1
    CLIENT_SECRETS_FILE = f"{os.getcwd()}/client_secrets.json"
    YOUTUBE_UPLOAD_SCOPE = f"https://www.googleapis.com/auth/youtube.readonly"
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"
    MISSING_CLIENT_SECRETS_MESSAGE = """
    WARNING: Please configure OAuth 2.0

    To make this sample run you will need to populate the client_secrets.json file
    found at:

       %s

    with information from the API Console
    https://console.developers.google.com/

    For more information about the client_secrets.json file format, please visit:
    https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
    """ % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       CLIENT_SECRETS_FILE))
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
                                   scope=YOUTUBE_UPLOAD_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage(f"/tmp/tweet_video.py-oauth2.json")
    credentials = storage.get()
    print(credentials)

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, argparser.parse_args(args=['--noauth_local_webserver']))

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))


scopes = ["https://www.googleapis.com/auth/youtube.readonly"]


def get_param(param):
    client = boto3.client('ssm')
    response = client.get_parameter(
        Name=param,
        WithDecryption=True
    )
    return response['Parameter']['Value']


def lambda_handler(event, context):
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = f"{os.getcwd()}/client_secrets.json"

    youtube = get_authenticated_service()

    CLIENT_ID = get_param('twitter_api_key')
    ACCESS_TOKEN = get_param('twitter_access_token')
    ACCESS_TOKEN_SECRET = get_param('twitter_access_token_secret')
    CLIENT_SECRET = get_param('twitter_api_key_secret')

    # Authenticate to Twitter
    auth = tweepy.OAuthHandler(CLIENT_ID, CLIENT_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    print(auth)

    # Create API object
    twitter_client = tweepy.API(auth)
    print(twitter_client)

    request = youtube.search().list(
        forMine=True,
        type="video",
        part="snippet",
        maxResults=1
    )
    response = request.execute()
    # print(json.dumps(response))
    video_id = response["items"][0]["id"]["videoId"]
    channel_id = response["items"][0]["snippet"]["channelId"]
    video_title = response["items"][0]["snippet"]["title"]

    now = datetime.now(gettz('US/Central'))

    print(f'Today\'s video is live! Title: "{video_title}" \nWatch here -> https://www.youtube.com/watch?v={video_id} \nPlease support the channel and subscribe! -> https://www.youtube.com/channel/{channel_id} \nDatetime: {now} \n#youtube #python #dailyquote')
    twitter_client.update_status(f'Today\'s video is live! Title: "{video_title}" \nWatch here -> https://www.youtube.com/watch?v={video_id} \nPlease support the channel and subscribe! -> https://www.youtube.com/channel/{channel_id} \nDatetime: {now} \n#youtube #python #dailyquote')
    


