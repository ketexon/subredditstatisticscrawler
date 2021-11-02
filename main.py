import praw
import pickle
from datetime import datetime
from dateutil import tz
import numpy as np
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os
import re

# first post fullname to be used to check if it is the last post
# (should, in theory, prevent an extra query in some cases)
# (optional, put None if unused)
FIRST_POST_NAME = "hv5kbi"
# subreddit to crawl
SUBREDDIT = "bruindating"
# cache file
CACHE_FILE = "posts_ser.p"

# ENVIRONMENT VARIABLES
# PRAW_CLIENT_ID = reddit client ID to use for praw
# PRAW_CLIENT_SECRET = reddit client secret to use for praw
# PRAW_USER_AGENT = user agent for praw (script:subredditcrawler:1.0.0 (by u/ketexon))


def submission_hsm(submission):
    cali_tz = tz.gettz("PST")
    dt = datetime.fromtimestamp(submission.created_utc, tz=cali_tz)
    return dt.hour + dt.minute / 60 + dt.second / 3600


SUBMISSION_M = 0
SUBMISSION_F = 1
SUBMISSION_NB = 2
SUBMISSION_UNKNOWN = -1
def submission_gender(submission):
    filtered_selftext = re.sub(r"#|\*|-", "", submission.selftext)
    match = re.search(
        "(?:\n|^| |,)+gender *(?::|=)? *(?:(?:cis|trans)(?:gender)?)? *(\w+)(?: |$|\n|,|/)",
        filtered_selftext, re.M | re.I
    )
    if match is None:
        # use weaker match
        match = re.search(
            "(?:\n|^| |,|/)+(m(?:ale|an)?|boy|ftm|f(?:emale)?|girl|mtf)(?: |$|\n|,|/)",
            filtered_selftext, re.M | re.I
        )
    
    if match is not None:
        gender = match.groups()[0]
        if re.match("(m(ale|an)?|boy|ftm)", gender, re.I) is not None:
            return SUBMISSION_M
        elif re.match("(f(emale)?|girl|mtf)", gender, re.I) is not None:
            return SUBMISSION_F
        else:
            print("Nonbinary gender found: %s" % gender)
            return SUBMISSION_NB
    else:
        print(submission.selftext)
        return SUBMISSION_UNKNOWN
            


def main():
    # reddit api client
    reddit = praw.Reddit(
        client_id = os.getenv("PRAW_CLIENT_ID"),
        client_secret = os.getenv("PRAW_CLIENT_SECRET"),
        user_agent = os.getenv("PRAW_USER_AGENT")
    )
    
    # list of cached posts
    previous_posts = []
    # list of new posts
    posts = []
    try:
        with open(CACHE_FILE, "rb") as serialized:
            previous_posts = pickle.load(serialized)
    except:
        pass
    
    # last submission in query (to pass to "after" query in reddit api)
    last_submission = None
    
    
    should_break = False
    i = 1
    print("Crawling...")
    while not should_break:
        print(f"Iteration {i}")
        i += 1
        n_submissions = 0
        # query new for bruindating, adding the "after" param if we have queried before
        for submission in reddit.subreddit(SUBREDDIT).new(
            **({"params": {"after": f"t3_{last_submission}"}} if last_submission else {})
            ):
            n_submissions += 1
            if submission in previous_posts:
                print("Found cached submission. Breaking...")
                should_break = True
                break
            posts.append(submission)
            last_submission = submission
            if FIRST_POST_NAME is not None:
                if submission.name == FIRST_POST_NAME:
                    print("Found first submission. Breaking...")
                    should_break = True
                    break
        
        if n_submissions == 0:
            print("Query produced no submissions. Breaking...")
            should_break = True
    
    posts = posts + previous_posts
    
    # update cache if found new postss
    if posts != previous_posts:
        with open(CACHE_FILE, "wb") as serialized:
            pickle.dump(posts, serialized)
    
    
    # map the submissions to hours since midnight -> np array
    post_hsm = map(submission_hsm, posts)
    post_hsm_np = np.fromiter(post_hsm, dtype=np.double)
    
    # statistics
    avg = np.average(post_hsm_np)
    std = np.std(post_hsm_np)
    
    print(f"Hours Since Midnight\nAVG: {avg}\nSTD: {std}")
    
    # histogram
    hist = np.histogram(post_hsm_np, range(25))
    plt.bar(list(hist[1][:-1]), list(hist[0]), width=0.8)
    plt.xticks(list(range(24)))
    plt.show()
    
    # map the submissions to gender
    post_gender = map(submission_gender, posts)
    post_gender_np = np.fromiter(post_gender, dtype=np.int_)
    post_gender_np_filtered = post_gender_np[post_gender_np != SUBMISSION_UNKNOWN]
    
    n_m = np.count_nonzero(post_gender_np == SUBMISSION_M)
    n_f = np.count_nonzero(post_gender_np == SUBMISSION_F)
    n_nb = np.count_nonzero(post_gender_np == SUBMISSION_NB)
    n_unknown = np.count_nonzero(post_gender_np == SUBMISSION_UNKNOWN)
    print(f"Counts:\n\tM: {n_m}\n\tF: {n_f}\n\tNB/Unknown: {n_nb}\n\tUnknown: {n_unknown}")
    
    # histogram
    plt.hist(post_gender_np_filtered, bins=np.arange(0, 4), align="left")
    plt.xticks(np.arange(0, 3))
    plt.show()
    
    
if __name__ == "__main__":
    load_dotenv()
    main()