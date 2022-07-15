from sanic import Sanic, response
from dotenv import load_dotenv
import pathlib
import os
import re
import praw
import funcs
import socket
import subprocess
import hashlib
import logging
import asyncio
import time
from urllib.parse import urlparse

MAX_FILE_STORED_TIME = 60 * 60 * 6 # 6 hours

# bind to ipv6
sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
sock.bind(('::', 8100))

load_dotenv()

app = Sanic("redsave-api")
app.config.REQUEST_MAX_SIZE = 100000
app.config.FORWARDED_SECRET = "204f61787b479971ae58071e032382fc366a977c3b7acb2fde4d8d28de70ddd3"

# load reddit
reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("CLIENT_USERAGENT"),
)


def validate_m3u8_url(url):
    urlParsed = urlparse(url)
    if urlParsed.scheme != "https":
        return False, "Invalid scheme"
    
    if urlParsed.netloc != "v.redd.it":
        return False, "Invalid netloc"
    
    split = urlParsed.path.split("/")[1:]
    if len(split) != 2:
        return False, "Invalid path"

    if re.search('^[a-z0-9]{13}$', split[0]) is None:
        return False, "Invalid id"
    
    if split[1] != "HLSPlaylist.m3u8":
        return False, "Invalid file"
    
    return True, ""


@app.route("/getlink")
async def get_link(req):
    url = req.args.get("url")
    
    # extract post id 
    try:        
        postID = re.search('(?<=comments/)(.*?)(?=\/)', url).group()
    except:
        return funcs.generate_response(False, "Invalid URL")

    print(postID)
    submission = reddit.submission(postID)
    
    postType = await funcs.determine_type(submission)

    if postType == "self":
        return funcs.generate_response(False, "Post is a text post")
    elif postType == "gallery":
        return funcs.generate_response(False, "Gallery is not supported")
    elif postType == "link":
        return funcs.generate_response(False, "Post is a link")

    return funcs.generate_response(True, submission.url)


@app.route("/getmp4")
async def get_mp4(req):
    # Example URL:
    # https://v.redd.it/jeswo38hjtsif/HLSPlaylist.m3u8
    url = req.args.get("url")
    filename = f'conversions/{hashlib.md5(url.encode()).hexdigest()}.mp4'

    # first check if url is safe
    safe, resp = validate_m3u8_url(url)
    if not safe:
        return funcs.generate_response(
            False,
            {
                "error": resp
            }
        )

    if not os.path.exists(filename):
        # convert mu3u8 -> mp4 via ffmpeg.exe
        logging.info(f"Converting {url} to {filename}")
        try:
            result = subprocess.run(
                ['ffmpeg', '-i', url, '-c', 'copy', '-bsf:a', 'aac_adtstoasc', filename],
                shell=True,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            return funcs.generate_response(False, e.output.decode())
        except Exception as e:
            return funcs.generate_response(False, e)

    
    return await response.file(
        filename,
        mime_type='video/mp4',
    )


async def routine_delete_conversions():
    while True:
        try:
            for file in os.listdir("conversions"):
                path = os.path.join("conversions", file)

                # get time since creation
                time_since_creation = (time.time() - os.path.getctime(path))  # in seconds
                
                if path.endswith(".mp4") and time_since_creation >= MAX_FILE_STORED_TIME:
                    os.remove(f"conversions/{path}")
                    logging.info(f"Deleted {path}")
        
        except Exception as e:
            logging.error(e)
        
        await asyncio.sleep(60 * 60) # hourly

if __name__ == "__main__":
    pathlib.Path("./conversions").mkdir(parents=True, exist_ok=True)

    app.add_task(routine_delete_conversions)

    app.run(sock=sock)