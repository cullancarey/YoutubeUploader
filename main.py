import praw
import os
from gtts import gTTS
from upload_video import *
import requests
from mutagen.mp3 import MP3
import subprocess
import shlex
import shutil
from dotenv import load_dotenv
import random
from datetime import datetime
import boto3

load_dotenv()

shutil.copy(f"{os.getcwd()}/main.py-oauth2.json", "/tmp/main.py-oauth2.json")
shutil.copy(f"{os.getcwd()}/story.txt", "/tmp/story.txt")
shutil.copy(f"{os.getcwd()}/story.mp3", "/tmp/story.mp3")
shutil.copy(f"{os.getcwd()}/output.mp4", "/tmp/output.mp4")
os.mkdir("/tmp/images")

#Retrieves image urls based on text file
def get_image_urls(query):
    url = f'https://www.google.be/search?q={query}&tbm=isch'

    headers = {}
    data = {}

    response = requests.get(url, headers=headers, data=data)

    return response.text

#Downloads the image context for the video file
def download_image(urls):
    url = f'{urls}'

    headers = {}
    data = {}

    response = requests.get(url, headers=headers, data=data)

    return response.content


def get_param(param):
    client = boto3.client('ssm')
    response = client.get_parameter(
        Name=param,
        WithDecryption=True
    )
    return response['Parameter']['Value']


def lambda_handler(event, context):
    #Secrets for Reddit session
    CLIENT_ID = get_param('reddit_client_id')
    CLIENT_SECRET = get_param('reddit_client_secret')
    USER_AGENT = get_param('reddit_user_agent')
    USERNAME = get_param('reddit_username')
    PASSWORD = get_param('reddit_password')

    #Sets Reddit session
    reddit = praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT,
        username=USERNAME,
        password=PASSWORD
    )



    #Grabs newest submission from r/quotes. 
    #Also grabs author and url for credit
    story_file = open(f"/tmp/story.txt", 'w')
    for submission in reddit.subreddit("quotes").new(limit=1):
        if not submission.over_18:
            story_file.write(submission.title)
            story_file.write(submission.selftext)
            author = submission.author
            url = submission.url

    story_file.close()


    #Cretes mp3 file from text file
    story = open(f"/tmp/story.txt", 'r')
    text_file = story.read()
    tts = gTTS(text_file)
    audio_file = tts.save(f'/tmp/story.mp3')
    audio_file_path = f"/tmp/story.mp3"

    #Get length of audio and sets number of images needed
    audio = MP3(f'/tmp/story.mp3')
    audio_length = audio.info.length
    number_of_images = str(audio_length)
    number_of_images = number_of_images.split(".")
    number_of_images = number_of_images[0]

    #Retrieves images urls
    response = get_image_urls(f'{text_file}')
    response = response.split('"')
    urls = []
    for i in response:
        response = i.split(";s")
        if 'https://encrypted-' in i:
            urls.append(response[0])


    if int(number_of_images) > len(urls):
        response = get_image_urls(f'coding with python')
        response = response.split('"')
        for i in response:
            response = i.split(";s")
            if 'https://encrypted-' in i:
                urls.append(response[0])

    #Creates directory for images file
    images_dir = f'/tmp/images'
    if not os.path.isdir(images_dir):
        images_dir = os.mkdir(images_dir)
    images_path = f'{images_dir}/*.jpg'

    #Downloads images based on the lenth of the audio file
    for count, i in enumerate(range(int(number_of_images))):
        image = download_image(urls[count])
        handler = open(f'{images_dir}/image{count}.jpg', 'wb')
        image_file = handler.write(image)
        handler.close()

    #Get frame rate for video
    frame_rate = audio_length / int(number_of_images)

    video_file_path = f"/tmp/output.mp4"


    # Create Video File!
    command_line = f"{os.getcwd()}/ffmpeg -y -hide_banner -framerate 1/{str(frame_rate)} -pix_fmt yuvj420p  -pattern_type glob -i {str(images_path)} -i {str(audio_file_path)} -c:v libx264 -vf scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2 -c:a aac -shortest {str(video_file_path)}"

    args = shlex.split(command_line)
    subprocess.call(args)

    titles = [f"Daily Quote {datetime.today().strftime('%Y-%m-%d')}", "Quotes Daily", f"{datetime.today().strftime('%Y-%m-%d')} Quote", "Quotes", "Daily Quote", "Quote"]

    description = f'''Please enjoy this daily quote from u/{author}!
    These quotes are from r/quotes on Reddit.
    Link to post: {url}. \n
    This video was created and uploaded via Python!'''
    keywords = "quote", "quotes", "daily quote, python, reddit"

    #Instanciate upload video class
    upload = UploadVideo()

    #Calls method to upload video
    # print(video_file_path, random.choice(titles), description, 22, keywords, 'private')
    upload_video = upload.execute(video_file_path, random.choice(titles), description, 22, keywords, 'private')

    #Clean up files
    shutil.rmtree(f"/tmp/images/")
    os.mkdir(images_dir)
    os.remove(f"/tmp/story.txt")
    os.remove(f"/tmp/story.mp3")
    os.remove(f"/tmp/output.mp4")    
    print("Done deleting files")