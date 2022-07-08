from sanic import Sanic
from sanic.response import json
from dotenv import load_dotenv
import os
import re
import praw
import funcs

load_dotenv()

app = Sanic("redsave-api")

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
        postID = re.search('http[s]?://www.reddit.com/r/.*/comments/(.*?)/.*/', url)[0]
    except IndexError:
        return funcs.generate_response(False, "Invalid URL")

    submission = reddit.submission(postID)
    
    try:
        postType = funcs.determine_type(submission)
    except Exception as e:
        return funcs.generate_response(False, "couldnt identify post type")
    
    if postType == "self":
        return funcs.generate_response(False, "Post is a text post")
    elif postType == "gallery":
        return funcs.generate_response(False, "Gallery is not supported")
    elif postType == "link":
        return funcs.generate_response(False, "Post is a link")

    return funcs.generate_response(True, submission.url)

if __name__ == "__main__":
    app.run()