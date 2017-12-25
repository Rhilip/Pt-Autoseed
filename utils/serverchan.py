# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import logging

import requests


class ServerChan(object):
    def __init__(self, status, key):
        self.status = status
        self.key_url = "http://sc.ftqq.com/" + key + ".send"

    def send(self, text, desp):
        """
        推送主方法
        :param text: 必填，最长265字节 
        :param desp: 信息内容，最长64K，选填，支持Markdown
        """
        if self.status:
            r = requests.post(url=self.key_url, data={'text': text, 'desp': desp})
            logging.info("Send ServerChan message, The Server echo: \"{0}\"".format(r.text))

    def send_torrent_post_ok(self, url, dl_torrent):
        # TODO more desp
        text = "已成功发布种子"
        desp = """种子名称：{name}<br>种子发布链接：{url}""".format(name=dl_torrent.name, url=url)
        self.send(text=text, desp=desp)
