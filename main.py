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

load_dotenv()

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

#Secrets for Reddit session
CLIENT_ID=os.getenv('CLIENT_ID')
CLIENT_SECRET=os.getenv('CLIENT_SECRET')
USER_AGENT=os.getenv('USER_AGENT')
USERNAME=os.getenv('USERNAME')
PASSWORD=os.getenv('PASSWORD')

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
story_file = open(r'story.txt', 'w')
for submission in reddit.subreddit("quotes").new(limit=1):
    if not submission.over_18:
        story_file.write(submission.title)
        story_file.write(submission.selftext)
        author = submission.author
        url = submission.url

story_file.close()


#Cretes mp3 file from text file
story = open(r'story.txt', 'r')
text_file = story.read()
tts = gTTS(text_file)
audio_file = tts.save('story.mp3')
audio_file_path = f"{os.getcwd()}/story.mp3"

#Get length of audio and sets number of images needed
audio = MP3('story.mp3')
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

#Creates directory for images file
images_dir = f'{os.getcwd()}/images'
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

video_file_path = "output.mp4"


# Create Video File!
command_line = f"/usr/local/bin/ffmpeg -y -hide_banner -framerate 1/{str(frame_rate)} -pix_fmt yuvj420p  -pattern_type glob -i {str(images_path)} -i {str(audio_file_path)} -c:v libx264 -vf scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2 -c:a aac -shortest {str(video_file_path)}"

args = shlex.split(command_line)
subprocess.call(args)

##clean up images files
shutil.rmtree("images/")
os.mkdir(images_dir)

title = "Python Daily Quote!"

description = f'''Please enjoy this daily quote! \n
Credit u/{author}. See post at {url}. \n
This video was created and uploaded via Python!'''

keywords = "Python, quote, quotes, daily quote, automation, Reddit, Praw"

#Instanciate upload video class
upload = UploadVideo()

#Calls method to upload video
upload_video = upload.execute(video_file_path, title, description, 22, keywords, 'public')
