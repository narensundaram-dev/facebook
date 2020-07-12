import re
import sys
import time
import json
import argparse
import traceback
from datetime import datetime as dt
from concurrent.futures import as_completed, ThreadPoolExecutor

import pandas as pd
from bs4 import BeautifulSoup, NavigableString

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

data = []


with open("settings.json", "r") as f:
    settings = json.load(f)


def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-gid', "--group_id", type=str, required=True)
    return arg_parser.parse_args()

args = get_args()


url = "https://www.facebook.com/groups/" + args.group_id
chrome = webdriver.Chrome(settings["driver_path"]["value"])
chrome.get(url)
WebDriverWait(chrome, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[role=feed]")))
html = chrome.page_source

# f = open("fb_live.html", "r")
# html = f.read()

soup = BeautifulSoup(html, "html.parser")
# with open("fb_live.html", "w+") as fb_live:
#     fb_live.write(soup.prettify())

posts = soup.find("div", role="feed").find_all("div", role="article", attrs={"id": re.compile("mall_post_.*")})
print("{} posts found!".format(len(posts)))

for post in posts:
    # view_more_comments = post.find('span', text=re.compile('View \d+ more comments'))
    # if view_more_comments:
    #     print(view_more_comments.parent.parent.click())
    # <span aria-hidden="true" class="_39_n _5pb8 o_c3pynyi2g _8o _8s lfloat _ohe" data-ft='{"tn":"m"}' tabindex="-1" title="Sridhar Thirumalaiswamy">

    username = post.select("span._39_n._5pb8.o_c3pynyi2g._8o._8s.lfloat._ohe")[0].attrs["title"]
    post_date = post.find("abbr").attrs["title"]
    try:
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
    for comment in comments:
        comment_by = comment.find(re.compile("(span|a)"), class_="_6qw4").get_text().strip()
        try:
            comment_content = comment.find("span", class_="_3l3x").get_text().strip()
            comment_content = re.sub('\s+', ' ', comment_content)
        except:
            comment_content = "NA"
        # replies = comment.find_all("div", attrs={"aria-label" : re.compile('Reply by .* ago')})
        replies = []

        data.append({
            "post_by": username,
            "post_date": post_date,
            "post_description": description,
            "comment": comment_content,
            "comment_by": comment_by,
            "reply": "",
            "reply_by": ""
        })

        print(f"\tContent: {comment_content} by {comment_by}")
        print(f"\t\tReplies: {len(replies)}")
        for reply in replies:
            reply_dom = reply.find_all("span", attrs={"dir": "auto"})
            reply_by = reply_dom[0].get_text().strip()
            try:
                reply_content = reply_dom[1].get_text().strip()
                reply_content = re.sub('\s+', ' ', reply_content)
            except:
                reply_content = "NA"
            print(f"\t\t\tReply: {reply_content} by {reply_by}")
    print("\n")
# f.close()
chrome.close()

df = pd.DataFrame(data)
df.to_excel('facebook_data.xlsx', index=False, engine='xlsxwriter', encoding="UTF-8")
