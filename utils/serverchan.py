# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import requests
import logging


class ServerChan(object):
    def __init__(self, setting):
        self.status = setting.ServerChan_status
        self.key_url = "http://sc.ftqq.com/" + setting.ServerChan_SCKEY + ".send"

    def send(self, text, desp):
        """
        推送主方法
        :param text: 必填，最长265字节 
        :param desp: 信息内容，最长64K，选填，支持Markdown
        """
        if self.status:
            r = requests.post(url=self.key_url, data={'text': text, 'desp': desp})
            logging.info("Send ServerChan message,The Server echo:\"{0}\"".format(r.text))

    def send_torrent_post_ok(self, dl_torrent):
        # TODO more desp
        text = "已成功发布种子"
        desp = """种子名称：{torrent_name}""".format(torrent_name=dl_torrent.name)
        self.send(text=text, desp=desp)
