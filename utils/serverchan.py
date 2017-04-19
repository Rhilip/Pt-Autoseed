# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import requests


class ServerChan(object):
    def __init__(self, key):
        self.key_url = "http://sc.ftqq.com/" + key + ".send"

    def send(self, text, desp):
        r = requests.post(url=self.key_url, data={'text': text, 'desp': desp})
        r_j = r.json()
        # TODO 回报推送状态
        # r.text '{"errno":0,"errmsg":"success","dataset":"done"}'
        return r.text
