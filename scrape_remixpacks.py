from requests import get, post
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from bs4 import NavigableString
from selenium import webdriver
from contextlib import closing
from datetime import datetime

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
    raw_html = raw_get_content(given_url)
    soup = BeautifulSoup(raw_html, 'html.parser')
    title_stems = soup.find_all(class_="titlestems")
    for stem in title_stems:
        title_links.append(str(stem.find("a")['href']))
    current_link = soup.find(class_="nextpostslink")
    if current_link is not None:
        current_link = str(current_link['href'])
    break

# Collect Yandex Links
for link in title_links:
    raw_html = raw_get_content(link)
    soup = BeautifulSoup(raw_html, 'html.parser')
    yandex_download_links.append(str(soup.find("form", target="_blank")['action']))
    break
    
# Download Files

driver = webdriver.PhantomJS('phantomjs.exe')
driver.set_window_size(1000, 1000)
for link in yandex_download_links:
    driver.get(link)
    driver.find_element_by_class_name("download-button").click()