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


# url = "https://www.facebook.com/groups/odoodevelopers"
# chrome = webdriver.Chrome("/home/narendran/Documents/chromedriver")
# chrome.get(url)
# WebDriverWait(chrome, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[role=feed]")))
# time.sleep(10)
# html = chrome.page_source

f = open("fb.html", "r")
html = f.read()

soup = BeautifulSoup(html, "html.parser")
# with open("fb_live.html", "w+") as fb_live:
#     fb_live.write(soup.prettify())

posts = soup.find("div", role="feed").select('div.du4w35lb.k4urcfbm.l9j0dhe7.sjgh65i0')
print("{} posts found!".format(len(posts)))

for post in posts:
    # view_more_comments = post.find('span', text=re.compile('View \d+ more comments'))
    # if view_more_comments:
    #     print(view_more_comments.parent.parent.click())

    username = post.find("h2", attrs={"id": re.compile("jsc_c_.*")}).select("a.oajrlxb2.g5ia77u1.qu0x051f.esr5mh6w.e9989ue4.r7d6kgcz.rq0escxv.nhd2j8a9.nc684nl6.p7hjln8o.kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.jb3vyjys.rz4wbd8a.qt6c0cv9.a8nywdso.i1ao9s8h.esuyzwwr.f1sip0of.lzcic4wl.oo9gr5id.gpro0wi8.lrazzd5p")[0].get_text().strip()
    post_date = post.find("span", attrs={"id": re.compile("jsc_c_.*")}).select("a.oajrlxb2.g5ia77u1.qu0x051f.esr5mh6w.e9989ue4.r7d6kgcz.rq0escxv.nhd2j8a9.nc684nl6.p7hjln8o.kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.jb3vyjys.rz4wbd8a.qt6c0cv9.a8nywdso.i1ao9s8h.esuyzwwr.f1sip0of.lzcic4wl.gmql0nx0.gpro0wi8.b1v8xokw")[0].get_text().replace("·", "").strip()
    try:
        description = post.find("div", attrs={"data-ad-preview": "message"}).get_text().strip()
        description = re.sub('\s+', ' ', description)
    except:
        description = ""
    comments = post.find_all("div", attrs={"aria-label" : re.compile('Comment by .* ago')})

    print("\n")
    print(f"Username: {username}")
    print(f"Post Date: {post_date}")
    print(f"Description: {description}")
    print(f"Comments: {len(comments)}")
    for comment in comments:
        comment_dom = comment.find_all("span", attrs={"dir": "auto"})
        comment_by = comment_dom[0].get_text().strip()
        try:
            comment_content = comment_dom[1].get_text().strip()
            comment_content = re.sub('\s+', ' ', comment_content)
        except:
            comment_content = ""
        replies = comment.find_all("div", attrs={"aria-label" : re.compile('Reply by .* ago')})

        print(f"\tContent: {comment_content} by {comment_by}")
        print(f"\t\tReplies: {len(replies)}")
        for reply in replies:
            reply_dom = reply.find_all("span", attrs={"dir": "auto"})
            reply_by = reply_dom[0].get_text().strip()
            try:
                reply_content = reply_dom[1].get_text().strip()
                reply_content = re.sub('\s+', ' ', reply_content)
            except:
                reply_content = ""
            print(f"\t\t\tReply: {reply_content} by {reply_by}")
    print("\n")
f.close()
# chrome.close()
