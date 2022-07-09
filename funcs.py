from sanic.response import json


async def determine_type(submission):
    """Determine the type of post

    Args:
        submission (Submission): Post

    Returns:
        string: Type of post
    """
    if submission.is_self:
        return "self"

    try:
        if submission.is_gallery:
            return "gallery"
    except:
        pass    
    
    domain = submission.domain
    if domain.startswith("v.redd.it"):
        return "video"
    elif domain.startswith("i.redd.it"):
        return "image"
    
    return "link"


def generate_response(success, payload):
    """Generate a JSON response

    Args:
        success (bool): If request was successful
        payload (json): Data

    Returns:
        json: Return data
    """
    if not success:
        data = {
            "error": payload
        }

    return json({
        "success": success,
        "data": payload
    })