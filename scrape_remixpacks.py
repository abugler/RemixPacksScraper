from requests import get, post
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from bs4 import NavigableString
# from selenium import webdriver
from contextlib import closing
from time import sleep
import pandas as pd
import re

given_url = "https://remixpacks.ru"
title_links = []
yandex_download_links = []
download_root = "https://downloader-default20h.disk-yandex.net/rzip/"

def raw_get_content(link):
    def is_good_response(resp):
        """
        Returns True if the response seems to be HTML, False otherwise.
        """
        content_type = resp.headers['Content-Type'].lower()
        return (resp.status_code == 200
                and content_type is not None
                and content_type.find('html') > -1)

    try:
        with closing(get(link, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                print("Nothing was returned")
                return None

    except RequestException as e:
        print('Error during requests to {0} : {1}'.format(link, str(e)))
        return None

# Collect Title Links
current_link = given_url
while current_link:
    sleep(1)
    print("Scraping: %s" % current_link)
    raw_html = raw_get_content(current_link)
    soup = BeautifulSoup(raw_html, 'html.parser')
    title_stems = soup.find_all(class_="titlestems")
    for stem in title_stems:
        title_links.append(str(stem.find("a")['href']))
    current_link = soup.find(class_="nextpostslink")
    if current_link is not None:
        current_link = str(current_link['href'])



"""
Values in the pd.DataFrame
# String/Float Values
"Remixpacks ID", "Yandex ID/Download", "Song Name", "Artist", "Size(MB)",  "Stem Type", 
# Boolean Values
"Bass", "Drums", "Vocal/Acapella",  
# List Values
"Genres", "Other Instruments", "Related Songs"])  
"""
yandex_disk = "https://yadi.sk"
rows = []
# Scraping Stem webpage
for link in title_links:
    sleep(.5)
    new_row = {}
    # We don't want to send to many requests to the site, otherwise, we get an error.
    sleep(1)
    print("Scraping: %s" % (link))
    raw_html = raw_get_content(link)
    soup = BeautifulSoup(raw_html, 'html.parser')
    # The Remixpacks ID is the last part of the url, directly after the second to last backslash
    link = link[:-1]
    new_row["Remixpacks ID"] = link[link.rfind("/") + 1:]

    # Similarly, the Yandex ID is the last part of the url, directly after the last backslash
    download_link = str(soup.find("form", target="_blank")['action'])
    if yandex_disk in download_link:
        new_row["Yandex ID/Download"] = download_link[download_link.rfind("/") + 1:]
    else:
        new_row["Yandex ID/Download"] = download_link

    # Collect stem type, artist, and song name
    title = str(soup.find("h1").get_text())
    first_paren = title.rfind("(")
    new_row["Stem Type"] = title[first_paren:].strip("() ")
    title = title[:first_paren]
    # Remixpacks.ru uses this very strange unicode character instead of a hyphen.
    # It probably has something to do with Russian keyboards
    artist, song_name = tuple(title.split("–"))
    new_row["Song Name"] = song_name.strip()
    new_row["Artist"] = artist.strip()

    # Find the instruments in the song
    # The reason for the formatting is because nussl organizes tracks into Bass, Drums, Vocals, and Other.
    new_row["Bass"] = False
    new_row["Drums"] = False
    new_row["Vocal/Acapella"] = False
    tags = soup.find("div", class_="tagslist").children
    new_row["Misc. Tags"] = []
    for tag in tags:
        if isinstance(tag, NavigableString):
            continue
        text = str(tag.get_text())
        if text == "bass":
            new_row["Bass"] = True
        elif text == "drums":
            new_row["Drums"] = True
        elif text == "acapella":
            new_row["Vocal/Acapella"] = True
        else:
            new_row["Misc. Tags"].append(text)

    # Find Genres
    genres = soup.find("div", class_="genres1").children
    new_row["Genres"] = []
    for genre in genres:
        if isinstance(genre, NavigableString):
            continue
        new_row["Genres"].append(str(genre.contents[0])[:-6])

    # Find Related Songs
    # Might be useful for making a graphical representation in a later iteration?
    new_row["Related Songs"] = []
    similar = soup.find("div", class_="similar-posts").children
    for sim in similar:
        if isinstance(sim, NavigableString):
            continue
        remixpacks_link = str(sim.contents[0]["href"])[:-1]
        new_row["Related Songs"].append(remixpacks_link[remixpacks_link.rfind("/")+1:])
    rows.append(new_row)
dataframe = pd.DataFrame(rows)
dataframe.to_csv("song_data.csv")

# yandex_download_links = [l + "\n" for l in yandex_download_links]
# yandex_saved_list = "yandex_list.txt"
# with open(yandex_saved_list, "w") as file:
#     file.writelines(yandex_download_links)


