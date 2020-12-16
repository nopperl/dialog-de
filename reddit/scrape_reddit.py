from json import load, dump
from multiprocessing import Queue, Process
from os import makedirs
from re import search, sub as re_sub, IGNORECASE
from typing import List, Dict, Any

from requests import get


def is_ama_submission(submission: Dict[str, Any], sub: Dict[str, Any]) -> bool:
    """
    Checks whether the given submission is an AMA-type submission. Apply `is_proper_submission` first.
    :param submission: A reddit submission
    :param sub: The subreddit specification
    :return:
    """
    amaFlairs = sub.get("amaFlairs")
    if amaFlairs and submission.get("link_flair_text") in amaFlairs:
        return True
    if sub.get("allowAMAInOtherFlairs"):
        title = submission.get("title")
        # Check if submission title starts with [AMA]-like tag, which is usually a proper AMA post
        if (
            search("\\[AmA\\]|\\[Ask me Anything\\]", title, flags=IGNORECASE)
            is not None
        ):
            return True
        # Check if the submission starts or ends with AMA. This check is of dubious quality
        if title.lower().startswith("ama ") or title.lower().endswith(" ama"):
            return True
    return False


def is_proper_submission(
    submission: Dict[str, Any], sub: Dict[str, Any], blacklist_flairs=[]
) -> bool:
    """
    Checks whether the submission should be used for the dataset
    :param submission: A reddit submission
    :param sub: The subreddit specification
    :param blacklist_flairs: Flairs which should be ignored
    :return:
    """
    # Do not use a removed or deleted submissions
    if submission.get("selftext") in ["[removed]", "[deleted]"]:
        return False
    # Meta posts are often moderation related and not really relevant
    if submission.get("is_meta"):
        return False
    # Posts other than self posts do not contain any relevant text from the poster
    if not submission.get("is_self"):
        return False
    # Makes no sense to consider questions/posts which no one answered
    if "num_comments" not in submission or submission["num_comments"] < 2:
        return False
    if submission.get("link_flair_text") in blacklist_flairs:
        return False
    if not has_enough_upvotes(submission):
        return False
    questionFlairs = sub.get("questionFlairs")
    # Check if submission is either of question or AMA type using flair
    if (
        sub.get("ignoreFlairs")
        or (not questionFlairs or submission.get("link_flair_text") in questionFlairs)
        or is_ama_submission(submission, sub)
    ):
        return True
    return False


def is_proper_comment(comment: Dict[str, Any]) -> bool:
    """
    Checks whether the comment should be used for the dataset
    :param comment: A reddit comment
    :return:
    """
    body = comment["data"]["body"]
    # Do not use a removed or deleted comments
    if body in ["[removed]", "[deleted]"]:
        return False
    if not has_enough_upvotes(comment["data"]):
        return False
    # Ignore top-level comments without replies
    if comment["data"]["depth"] == 0 and (
        comment["data"].get("replies")
        and len(comment["data"]["replies"]["data"]["children"]) < 1
    ):
        return False
    # Ignore all comments which include hyperlinks (also reddit-specifics like `r/all`)
    if '&gt;&lt;a href="' in body:
        return False
    # Attempt to ignore comments which include bot commands
    if "remindme!" in body.lower():
        return False
    # Ignore sarcasm
    if "/s" in body or "\s" in body:
        return False
    # Ignore empty text
    if body.isspace():
        return False
    # Ignore upper-case rage
    if search("[A-Z]{5,}", body):
        return False
    return True


def filter_submissions(
    data: List[Dict[str, Any]], sub: Dict[str, Any], blacklist_flairs=[]
) -> List[str]:
    """
    Filters all submissions which should be used for the dataset.
    :param data: The list of submissions
    :param sub: The subreddit specification
    :param blacklist_flairs: Flairs which should be ignored
    :return: The permalinks of all proper submissions
    """
    return [
        s["permalink"] for s in data if is_proper_submission(s, sub, blacklist_flairs)
    ]


def has_enough_upvotes(body: Dict[str, Any]) -> bool:
    """
    Determines if a submission or a comment has more upvotes than downvotes for quality control
    :param body: Either a submission or a comment
    :return:
    """
    return body["score"] > 1


def traverse_dialog(
    comment: Dict[str, Any],
    turns: List[Dict[str, str]],
    request_url: str,
    sys=None,
    user=None,
    text_maxlen=1024,
) -> List[Dict[str, str]]:
    """
    Traverses a comment chain recursively in order to assemble the dialog.
    :param comment: The current comment
    :param turns: The dialog turns up until now
    :param request_url: The URL used for HTTP requests
    :param sys: The author representing the system response
    :param user: The author representing the user response
    :param text_maxlen: The maximum length of a comment text
    :return: The turns of one dialog
    """
    text = comment["data"]["body"]
    if not is_proper_comment(comment):
        return turns
    # Remove texts which are too long (problematic for training and not really representative for chatbot users)
    if len(text) > text_maxlen:
        return turns
    # Current author is always the other role of their correspondent
    if not user:
        user = comment["data"]["author"]
    elif not sys:
        sys = comment["data"]["author"]
    comment_is_user = user == comment["data"]["author"]
    sender = "user" if comment_is_user else "sys"
    # If the text contains a quote, reencode it in a way better suited to learning it
    if "&lt;blockquote&gt;" in comment["data"]["body_html"]:
        re_sub(r"(.*)\&gt\;(.*)\n(.*)", r"\1[QUOTE]\2[QUOTE]\3", text)
    turns.append({"sender": sender, "text": text})
    if not comment["data"].get("replies"):
        return turns
    replies = comment["data"]["replies"]["data"]["children"]
    # At some length, the API response cuts the chain off. Therefore, the replies have to be requested along the chain
    if len(replies) == 1 and replies[0]["kind"] == "more":
        response = get(request_url + comment["data"]["id"] + ".json")
        replies = response.json()[1]["data"]["children"]
    # Only retrieves the next direct response from the correspondent
    # Could potentially traverse all replies to see if sys has responded to someone else as well in AMA mode
    reply = next(
        (
            r
            for r in replies
            if (comment_is_user and r["data"]["author"] == sys)
            or (not comment_is_user and r["data"]["author"] == user)
        ),
        None,
    )
    if not reply:
        return turns
    return traverse_dialog(reply, turns, request_url, sys, user, text_maxlen)


def retrieve_dialogs(
    js: List[Dict[str, Any]], sub: Dict[str, Any], text_maxlen=1024
) -> List[Dict[str, Any]]:
    """
    Retrieves all dialogs of a submission.
    :param js: The submission site JSON dict containing both submission and comments
    :param sub: The subreddit specification
    :param text_maxlen: The maximum length of a comment text
    :return: All dialogs of the submission
    """
    # Abort if the JSON structure is invalid
    if len(js) < 2 and js[0]["kind"] != "Listing" and js[0]["kind"] != "Listing":
        return []
    submission = js[0]["data"]["children"][0]
    ama_mode = is_ama_submission(submission["data"], sub)
    # use flair as (arguably rough) approximation for the initial intent
    intent = submission["data"].get("link_flair_text")
    dialog = {
        "domain": sub["displayName"],
        "initialIntent": intent,
        "title": submission["data"]["title"],
        "id": submission["data"]["id"],
    }
    dialogs = []
    # In AMA-mode, the original poster represents the system, while the top-level commenter represents the user.
    # The inverse is true for question-mode.
    if ama_mode:
        sys = submission["data"]["author"]
        user = None
        dialog["turns"] = []
    else:
        sys = None
        user = submission["data"]["author"]
        # Use either the post body or title as initial turn text in question mode
        text = submission["data"].get("selftext")
        if not text:
            text = submission["data"].get("title")
        dialog["turns"] = [{"sender": "user", "text": text}]
    comments = [c for c in js[1]["data"]["children"] if is_proper_comment(c)]
    for comment in comments:
        turns = traverse_dialog(
            comment, [], submission["data"]["url"], sys, user, text_maxlen
        )
        if len(turns) < 2:
            continue
        dialog_copy = dialog.copy()
        dialog_copy["turns"].extend(turns)
        dialogs.append(dialog_copy)
    return dialogs


def write_output(queue: Queue, top_dir: str):
    """
    Consumes processed dialog turns from a queue and writes them into a directory.
    An individual file will be used for each subreddit.
    :param queue: The queue to wait on for new data. Should output dialog JSON or None if the process is finished
    :param top_dir: The directory used to write the data to
    :return:
    """
    while True:
        item = queue.get()
        print(item)
        if item is None:
            continue
        sub, dialogs = item
        with open(f"{top_dir}/{sub}.json", "a") as file:
            for dialog in dialogs:
                dump(dialog, file)
                file.write("\n")


def process_subreddit(
    sub: Dict[str, Any],
    url_template: str,
    queue: Queue,
    text_maxlen=1024,
    blacklist_flairs=[],
):
    last_time = None
    submissions = []
    while True:
        request_url = (
            url_template + f"&before={last_time}" if last_time else url_template
        )
        response = get(request_url)
        if response.ok:
            data = response.json()["data"]
            if len(data) == 0:
                break
            new_submissions = filter_submissions(data, sub, blacklist_flairs)
            submissions.extend(new_submissions)
            last_time = response.json()["data"][-1]["created_utc"]

    url_template = "https://np.reddit.com"
    for permalink in submissions:
        response = get(url_template + permalink + ".json?limit=1000")
        if not response.ok:
            continue
        new_dialogs = retrieve_dialogs(response.json(), sub, text_maxlen)
        queue.put((sub["displayName"], new_dialogs))


def main():
    url = "https://api.pushshift.io/reddit"
    output_dir = "../data"
    makedirs(output_dir, exist_ok=True)
    blacklist_flairs = ["Meme", "Humor"]
    text_maxlength = 1024
    file_name = "subreddits-de.json"
    with open(file_name, "r") as file:
        subs = load(file)
    output_queue = Queue()
    consumer = Process(target=write_output, args=(output_queue, output_dir))
    consumer.start()
    pool = []
    # Only fields explicitly specified here will be requested to save bandwith
    fields = [
        "created_utc",
        "is_meta",
        "is_self",
        "num_comments",
        "link_flair_text",
        "title",
        "permalink",
        "score",
        "selftext",
    ]
    for sub in subs:
        url_template = (
            url
            + f"/search/submission?subreddit={sub['displayName']}&size=100&fields={','.join(fields)}"
        )
        p = Process(
            target=process_subreddit,
            args=(sub, url_template, output_queue, text_maxlength, blacklist_flairs),
        )
        p.start()
        pool.append(p)
    for p in pool:
        p.join()
    output_queue.put(None)


if __name__ == "__main__":
    main()
