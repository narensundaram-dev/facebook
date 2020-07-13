import re
import sys
import time
import json
import argparse
import traceback
from datetime import datetime as dt, timedelta as td
from concurrent.futures import as_completed, ThreadPoolExecutor

import pandas as pd
from bs4 import BeautifulSoup, NavigableString

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

# All neccessary data stored here
data = []

# Load settings
with open("settings.json", "r") as f:
    settings = json.load(f)

# Script args from user as input
def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-gid', "--group_id", type=str, required=True)
    arg_parser.add_argument("-pc", "--post_contains", type=str, help="Post description contains ...", required=False)
    arg_parser.add_argument("-d", "--date", type=str, help="MM/DD/YYYY ['12/31/2019']")
    arg_parser.add_argument("-dt", "--datetime", type=str, help="MM/DD/YYYY HH:MM AM/PM ['12/31/2019 1:05 PM']")
    return arg_parser.parse_args()
args = get_args()


# Open chrome browser and load the group page
url = "https://www.facebook.com/groups/" + args.group_id
chrome = webdriver.Chrome(settings["driver_path"]["value"])
chrome.get(url)
WebDriverWait(chrome, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[role=feed]")))

# Expanding links of "See More" and "View \d+ comments"
for element in chrome.find_elements_by_class_name("see_more_link_inner"):
    webdriver.ActionChains(chrome).move_to_element(element).click(element).perform()
for element in chrome.find_elements_by_css_selector("._5v47.fss"):
    webdriver.ActionChains(chrome).move_to_element(element).click(element).perform()
for element in chrome.find_elements_by_css_selector("._3eol.ellipsis"):
    webdriver.ActionChains(chrome).move_to_element(element).click(element).perform()

# Getting source code of the web page
html = chrome.page_source
soup = BeautifulSoup(html, "html.parser")

# Loading all the posts
posts = soup.find("div", role="feed").find_all("div", role="article", attrs={"id": re.compile("mall_post_.*")})
print("{} posts found!".format(len(posts)))


for idx, post in enumerate(posts):
    username = post.select("span._39_n._5pb8.o_c3pynyi2g._8o._8s.lfloat._ohe")[0].attrs["title"]
    post_date = post.find("abbr").attrs["title"]
    post_date = dt.strptime(post_date, "%A, %d %B %Y at %H:%M")
    post_date_str = post_date.strftime("%m-%d-%Y %I:%M %p")
    try:
        # Inside try-except, since the post may not contain description
        description = post.find("div", attrs={"data-testid": "post_message"}).get_text().strip()
        description = re.sub('\s+', ' ', description)
    except:
        description = "NA"
    comments = post.find_all("div", attrs={"aria-label" : "Comment"})

    print("\n")
    print(f"Username: {username}")
    print(f"Post Date: {post_date}")
    print(f"Description: {description}")
    print(f"Comments: {len(comments)}")

    data.append({
        # "#": idx+1,
        "post_by": username,
        "date": post_date,
        "post_date": post_date_str,
        "post_description": description,
        "comment": "",
        "comment_by": "",
        "reply": "",
        "reply_by": ""
    })
    for comment in comments:
        comment_by = comment.find(re.compile("(span|a)"), class_="_6qw4").get_text().strip()
        try:
            # Inside try-except, since the comment may not contain description
            comment_content = comment.find("span", class_="_3l3x").get_text().strip()
            comment_content = re.sub('\s+', ' ', comment_content)
        except:
            comment_content = "NA"
        replies = post.find_all("div", attrs={"aria-label" : "Comment reply"})

        data.append({
            # "#": idx+1,
            "post_by": username,
            "date": post_date,
            "post_date": post_date_str,
            "post_description": description,
            "comment": comment_content,
            "comment_by": comment_by,
            "reply": "",
            "reply_by": ""
        })

        print(f"\tContent: {comment_content} [by {comment_by}]")
        print(f"\t\tReplies: {len(replies)}")

        for reply in replies:
            reply_by = reply.find(re.compile("(span|a)"), class_="_6qw4").get_text().strip()
            try:
                # Inside try-except, since the reply may not contain description
                reply_content = reply.find("span", class_="_3l3x").get_text().strip()
                reply_content = re.sub('\s+', ' ', reply_content)
            except:
                reply_content = "NA"

            data.append({
                # "#": idx+1,
                "post_by": username,
                "date": post_date,
                "post_date": post_date_str,
                "post_description": description,
                "comment": comment_content,
                "comment_by": comment_by,
                "reply": reply_content,
                "reply_by": reply_by
            })

            print(f"\t\t\tReply: {reply_content} [by {reply_by}]")

    print("\n")

# Close chrome browser once the job is done
chrome.close()


# Filter data and save it to xlsx file
df = pd.DataFrame(data)

df['date'] = pd.to_datetime(df['date'])
if args.date:
    date_ = dt.strptime(args.date, "%m/%d/%Y")
    start = date_.strftime("%Y-%m-%d")
    end = (date_ + td(days=1)).strftime("%Y-%m-%d")
    df = df[(df['date'] >= start) & (df['date'] < end)]

if args.datetime:
    datetime_ = dt.strptime(args.datetime, "%m/%d/%Y %I:%M %p")
    df = df[df["date"] == datetime_]

if args.post_contains:
    df = df[df["post_description"].str.contains(args.post_contains, case=False)]

print(f"{len(df)} no of data has been stored in facebook_data.xlsx file")
columns = ["post_by", "post_date", "post_description", "comment", "comment_by", "reply", "reply_by"]
df.to_excel('facebook_data.xlsx', columns=columns, index=False, engine='xlsxwriter', encoding="UTF-8")
