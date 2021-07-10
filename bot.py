import collections
import json
import logging
import random
import os
import requests
import boto3
from botocore.exceptions import ClientError

import praw

FLAIR_ID = os.environ.get("FLAIR")
FAB_API_URL = "https://api.fabdb.net"
FAB_SUBREDDIT = os.environ.get("SUBREDDIT") or "test"
SECRET_NAME = "prod/COTDBot/credentials"
AWS_REGION = "us-east-2"

logger = logging.getLogger("cotd-bot")
logger.setLevel(logging.INFO)


def generate_post(card) -> (str, str):
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


def get_secret(secret_name, region_name) -> str:

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
                SecretId=secret_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise e
    else:
        secret = get_secret_value_response['SecretString']
        return secret


def get_handle() -> praw.Reddit:
    secret = get_secret(SECRET_NAME, AWS_REGION)
    creds = json.loads(secret)

    r = praw.Reddit(user_agent="COTDBOT",
                    username=creds["username"],
                    password=creds["password"],
                    client_id=creds["client_id"],
                    client_secret=creds["client_secret"])
    return r


def fetch_cards():
    payload = {"page": 1}
    first_resp = requests.get(FAB_API_URL + "/cards",
                              params=payload, timeout=30).json()

    num_pages = first_resp["meta"]["last_page"]
    cards = collections.defaultdict()
    if not num_pages:
        logger.error("Error getting number of cards from first API request")
        logger.error(f"Response: {first_resp}")
        return

    # Iterate through the paginated list of cards
    for i in range(1, num_pages+1):
        url = f"{FAB_API_URL}/cards?page={i}&per_page=100"
        resp = requests.get(url, timeout=1)
        if not resp.ok:
            logger.error("Error getting page {i} of {num_pages}")
            logger.error("Response Code: {resp.status_code}")
            continue
        resp = resp.json()
        data = resp["data"]
        cards_page = {card["identifier"]: card for card in data}
        cards.update(cards_page)
    return cards


def lambda_handler(self, event):
    all_cards = fetch_cards()
    if not all_cards:
        logger.error("No cards returned from FaBDB.net")
        return
    logger.info("Picking a random card out of %i", len(all_cards))
    cotd = random.choice(list(all_cards.values()))
    title, post = generate_post(cotd)

    try:
        reddit = get_handle()
        subreddit = reddit.subreddit(FAB_SUBREDDIT)
        submission = subreddit.submit(title, selftext=post, flair_id=FLAIR_ID)
        return {
                "saved": submission.saved,
                "title": submission.title,
                "content": submission.selftext,
                "url": submission.permalink,
                "subreddit": FAB_SUBREDDIT
               }
    except Exception as e:
        logger.error("Exception thrown while getting reddit handle: %s", e)
