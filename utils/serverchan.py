# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import requests
import logging


class ServerChan(object):
    def __init__(self, key):
        self.key_url = "http://sc.ftqq.com/" + key + ".send"

    def send(self, text, desp):
        """
        推送主方法
        :param text: 必填，最长265字节 
        :param desp: 信息内容，最长64K，选填，支持Markdown
        :return: 
        """
        r = requests.post(url=self.key_url, data={'text': text, 'desp': desp})
        logging.info(r.text)
        return r.text

    def send_torrent_post_ok(self, dl_torrent):
        text = "已成功发布种子"
        desp = """种子名称：{torrent_name}""".format(torrent_name=dl_torrent.name)
        self.send(text=text, desp=desp)
