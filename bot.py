import collections
import json
import random
import requests
import toml

import praw

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
    payload = {"page": 1, "per_page": 100}
    first_resp = requests.get(FAB_API_URL + "/cards",
                              params=payload, timeout=1).json()

    num_pages = first_resp["meta"]["last_page"]
    card_cache = collections.defaultdict()
    for i in range(1, num_pages+1):
        url = f"{FAB_API_URL}/cards?page={i}&per_page=100"
        resp = requests.get(url, timeout=1).json()
        data = resp["data"]
        cards = {card["identifier"]: card for card in data}
        card_cache.update(cards)

    with open(CACHE_FILE, 'w') as f:
        json.dump(card_cache, f)

    return card_cache


def get_cards():
    # Refresh cache if expired.
    payload = {"page": 1, "per_page": 100}
    resp = requests.get(FAB_API_URL + "/cards",
                        params=payload, timeout=1).json()
    current_num_cards = resp["meta"]["total"]

    with open(CACHE_FILE, 'r') as f:
        card_cache = json.load(f)

    cards_changed = current_num_cards != len(card_cache)
    if cards_changed:
        return update_cache()

    return card_cache


all_cards = get_cards()
cotd = random.choice(list(all_cards.values()))

# TODO build post content using card info
# TODO make post
