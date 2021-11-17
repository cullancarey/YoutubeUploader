# YoutubeUploader
This repo holds the code to my Python script that uploads videos to Youtube programatically.
I was inspired by https://sudcha.com/i-made-youtube-videos-using-python/ so I wanted to see if I could create my own version of this idea.

This program first scrapes Reddit r/quotes for the newest SFW post on the page. It then writes that quote to a text file and using tts, creates an audio file of the quote. Next, it will do a google image search based on the text file to retrieve relevant images for the video. After that it will create the video file using ffmpeg. Finally it will call the upload_video.py file (provided from Youtube at https://developers.google.com/youtube/v3/guides/uploading_a_video. The video will then appear on my Youtube channel! 

Visit the channel! : https://www.youtube.com/channel/UCGU6cW0iBDA0N3D6iHcc5zg
