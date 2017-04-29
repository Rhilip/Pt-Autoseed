# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import logging
import requests
from utils.cookie import cookies_raw2jar
from utils.extend_descr import ExtendDescr
from utils.serverchan import ServerChan
from bs4 import BeautifulSoup


class NexusPHP(object):
    url_torrent_download = "http://www.pt_domain.com/download.php?id={tid}&passkey={pk}"
    url_torrent_upload = "http://www.pt_domain.com/takeupload.php"
    url_torrent_detail = "http://www.pt_domain.com/details.php?id={tid}&hit=1"
    url_thank = "http://www.pt_domain.com/thanks.php"
    url_search = "http://www.pt_domain.com/torrents.php?search={k}&search_mode={md}"

    uplver = "no"
    auto_thank = False

    reseed_column = "pt_domain.com"  # The column in table seed_list

    def __init__(self, setting: set, site_setting: dict):
        self._setting = setting
        self.cookies = cookies_raw2jar(site_setting["cookies"])
        self.passkey = site_setting["passkey"]
        self.clone_mode = site_setting["clone_mode"]
        if site_setting["anonymous_release"]:
            self.uplver = "yes"
        if site_setting["auto_thank"]:
            self.auto_thank = True
        self.descr = ExtendDescr(setting=self._setting)
        self.server_chan = ServerChan(setting=setting)

    def torrent_download(self, tr_client, tid, thanks=auto_thank):
        """
        直接使用transmissionrpc.Client.add_torrent方法向tr添加url直链种子
        https://pythonhosted.org/transmissionrpc/reference/transmissionrpc.html#transmissionrpc.Client.add_torrent
        :param tr_client: class transmissionrpc.Client
        :param tid: 种子发布号
        :param thanks: 自动感谢
        :return: 种子号
        """
        added_torrent = tr_client.add_torrent(torrent=self.url_torrent_download.format(tid=tid, pk=self.passkey))
        logging.info("Download Torrent OK,which id: {id}.".format(id=tid))
        if thanks:
            self.torrent_thank(tid)
        return added_torrent.id

    def torrent_upload(self, tr_client, multipart_data: tuple):
        """
        使用已经构造好的表单发布种子
        :param tr_client: class transmissionrpc.Client
        :param multipart_data: 发布表单
        :return: 
        """
        post = requests.post(url=self.url_torrent_upload, cookies=self.cookies, files=multipart_data)
        if post.url != self.url_torrent_upload:  # 发布成功检查
            seed_torrent_download_id = re.search("id=(\d+)", post.url).group(1)  # 获取种子编号
            flag = self.torrent_download(tr_client=tr_client, tid=seed_torrent_download_id)
            self.server_chan.send_torrent_post_ok(url=post.url, dl_torrent=tr_client.get_torrent(flag))
            logging.info("Reseed post OK,The torrent's in transmission: {fl}".format(fl=flag))
        else:  # 未发布成功打log
            outer_bs = BeautifulSoup(post.text, "lxml").find("td", id="outer")
            if outer_bs.find_all("table"):  # Remove unnecessary table info(include SMS,Report)
                for table in outer_bs.find_all("table"):
                    table.extract()
            outer_message = outer_bs.get_text().replace("\n", "")
            flag = -1
            logging.error("Upload this torrent Error,The Server echo:\"{0}\",Stop Posting".format(outer_message))
        return flag

    def torrent_thank(self, tid):
        """
        自动感谢
        :param tid: 种子号
        :return: None
        """
        requests.post(url=self.url_thank, cookies=self.cookies, data={"id": str(tid)})  # 自动感谢

    def page_torrent_detail_text(self, tid):
        """
        
        :param tid: 种子号
        :return: tid对应的种子页面
        """
        details_url = self.url_torrent_detail.format(tid=tid)
        details_page = requests.get(cookies=self.cookies, url=details_url)
        return details_page.text

    def page_search_text(self, search_key: str, search_mode: int):
        """
        
        :param search_key: 搜索关键词
        :param search_mode: 
        :return: 
        """
        search_url = self.url_search.format(k=search_key, md=search_mode)
        search_page = requests.get(cookies=self.cookies, url=search_url)
        return search_page.text

    def db_reseed_update(self, download_id, reseed_id, db_client):
        update_sql = "UPDATE seed_list SET `{col}` = {rid}" \
                     " WHERE download_id={did}".format(col=self.reseed_column, rid=reseed_id, did=download_id)
        db_client.commit_sql(update_sql)

    def get_last_torrent_id(self, search_key, search_mode: int, tid=0) -> int:
        bs = BeautifulSoup(self.page_search_text(search_key=search_key, search_mode=search_mode), "lxml")
        if bs.find_all("a", href=re.compile("download.php")):  # If exist
            href = bs.find_all("a", href=re.compile("download.php"))[0]["href"]
            tid = re.search("id=(\d+)", href).group(1)  # 找出种子id
        return tid

    def extend_descr(self, torrent, info_dict, encode) -> str:
        return self.descr.out(raw=info_dict["descr"], torrent=torrent, encode=encode,
                              before_torrent_id=info_dict["before_torrent_id"])
