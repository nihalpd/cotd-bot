import collections
import json
import random
import requests
import toml
from os import path

import praw

CACHE_FILE = "cache.json"
CACHE_TIMEOUT = 7 * 24 * 60 * 60  # one week
CREDS_FILE_PATH = "credentials.toml"
FAB_API_URL = "https://api.fabdb.net"
FAB_SUBREDDIT = "FleshAndBloodTCG"


def generate_post_and_title(card) -> (str, str):
    post_title = f"Card of The Day - {card['name']}"
    card_link = "https://fabdb.net/cards/" + card['identifier']
    keywords = ", ".join(card['keywords'])

    post_lines = [
            f"# [{card['name']}]({card_link})\n",
            f"{card['text']}\n\n",
            " Attribute | Stat \n",
            "-|-\n",
            f" Rarity | {card['rarity']} \n",
            f" Keywords | {keywords}\n",
            ]

    stats = card['stats']
    if 'attack' not in stats:
        post_lines.append("| Attack |  0 |\n")
    for stat in stats:
        post_lines.append(f" {stat} | {stats[stat]}\n")

    post_lines.append(f"# [Image]({card['image']})")
    return (post_title, ''.join(post_lines))





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
    payload = {"page": 1, "per_page": 100}
    resp = requests.get(FAB_API_URL + "/cards",
                        params=payload).json()
    current_num_cards = resp["meta"]["total"]

    # If the cache file doesnt exist, update the cache
    if not path.exists(CACHE_FILE):
        return update_cache()

    with open(CACHE_FILE, 'r') as file:
        card_cache = json.load(file)

    # Refresh cache if the total number of cards have changed.
    cards_changed = current_num_cards != len(card_cache)
    if cards_changed:
        print("Total number of cards has changed. Refreshing cache.")
        return update_cache()
    else:
        print("Total number of cards has remained unchanged. Using old cache.")
        return card_cache


all_cards = get_cards()
cotd = random.choice(list(all_cards.values()))
title, post = generate_post_and_title(cotd)

reddit = get_handle()
sr = reddit.subreddit('test')
sr.submit(title, selftext=post)
