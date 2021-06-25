import json
import praw
import requests
import time
import toml

CACHE_FILE = "cache.json"
CACHE_TIMEOUT = 7 * 24 * 60 * 60  # one week
CREDS_FILE_PATH = "credentials.toml"
FAB_API_URL = "https://api.fabdb.net"
FAB_SUBREDDIT = "FleshAndBloodTCG"


def get_handle() -> praw.Reddit:
    creds = toml.load(CREDS_FILE_PATH)

    r = praw.Reddit(user_agent="COTDBOT",
                    username=creds["username"],
                    password=creds["password"],
                    client_id=creds["client_id"],
                    client_secret=creds["client_secret"])
    return r


def update_cache():


    return


def get_ids():
    data = None
    with open(CACHE_FILE) as f:
        data = json.load(f)

    cached_timestamp = data["timestamp"]
    current_time = time.time()

    # Refresh cache if expired. 
    if current_time > cached_timestamp + CACHE_TIMEOUT:
        update_cache()

    ids = data["ids"]

    return ids

    


r = get_handle()
subreddit = r.subreddit(FAB_SUBREDDIT)


check if cache is expired
if cache expired, refresh cache
pick a random id
fetch info for card with id
build post content using card info
make post
