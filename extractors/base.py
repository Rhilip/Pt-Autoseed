# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import logging

import requests
from bs4 import BeautifulSoup

# Disable log messages from the Requests library
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

REQUESTS_TIMEOUT = 5


class Base(object):
    url_host = "http://www.pt_domain.com"  # No '/' at the end.
    db_column = "tracker.pt_domain.com"  # The column in table,should be as same as the first tracker's host
    encode = "bbcode"  # bbcode or html
    status = False
    cookies = None

    online_check_count = 0

    def model_name(self):
        return type(self).__name__

    def online_check(self):
        online = True
        try:
            requests.get(url=self.url_host, stream=True, timeout=REQUESTS_TIMEOUT)
        except requests.exceptions.RequestException:
            online = False
            if self.online_check_count == 0:
                logging.warning("Site: {si} is offline now.".format(si=self.url_host))
            self.online_check_count += 1
        else:
            if self.online_check_count != 0:
                logging.info("The Site: {si} is Now online,after {count} times tries."
                             "Will check the session soon.".format(si=self.url_host, count=self.online_check_count))
                self.session_check()
                self.online_check_count = 0
        return online

    def session_check(self):
        pass

    # -*- Encapsulation requests's method,with format-out as bs or json when use get -*-
    def get_data(self, url, params=None, bs=False, json=False):
        page = requests.get(url=url, params=params, cookies=self.cookies)
        return_info = page.text
        if bs:
            return_info = BeautifulSoup(return_info, "lxml")
        elif json:
            return_info = page.json()
        return return_info

    def post_data(self, url, params=None, data=None, files=None):
        return requests.post(url=url, params=params, data=data, files=files, cookies=self.cookies)
