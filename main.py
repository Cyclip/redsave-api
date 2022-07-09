from sanic import Sanic
from dotenv import load_dotenv
import os
import re
import praw
import funcs
import socket

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


@app.route("/")
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

if __name__ == "__main__":
    app.run(sock=sock)