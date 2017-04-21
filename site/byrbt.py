import re
import logging
import requests
from utils.cookie import cookies_raw2jar
from bs4 import BeautifulSoup

tracker_pattern = "tracker.byr.cn"


class Byrbt:
    def __init__(self, setting):
        self.passkey = setting.byr_passkey
        self.cookies = cookies_raw2jar(setting.byr_cookies)

    def download_torrent(self, tr_client, tid, thanks=True):
        """
        直接使用transmissionrpc.Client.add_torrent方法向tr添加url直链种子
        https://pythonhosted.org/transmissionrpc/reference/transmissionrpc.html#transmissionrpc.Client.add_torrent
        """
        download_torrent_link = "http://bt.byr.cn/download.php?id={tid}&passkey={pk}".format(tid=tid, pk=self.passkey)
        added_torrent = tr_client.add_torrent(torrent=download_torrent_link)
        logging.info("Download Torrent which id = {id} OK!".format(id=tid))
        if thanks:
            requests.post(url="http://bt.byr.cn/thanks.php", cookies=self.cookies, data={"id": str(tid)})  # 自动感谢
        return added_torrent.id

    def post_torrent(self, tr_client, multipart_data: tuple):
        """使用已经构造好的表单发布种子"""
        post = requests.post(url="http://bt.byr.cn/takeupload.php", cookies=self.cookies, files=multipart_data)
        if post.url != "http://bt.byr.cn/takeupload.php":  # 发布成功检查
            seed_torrent_download_id = re.search("id=(\d+)", post.url).group(1)  # 获取种子编号
            flag = self.download_torrent(tr_client=tr_client, tid=seed_torrent_download_id)
            logging.info("Post OK,The id in Byrbt: {id},in tr: {fl}".format(id=seed_torrent_download_id, fl=flag))
        else:  # 未发布成功打log
            outer_bs = BeautifulSoup(post.text, "lxml").find("td", id="outer")
            if outer_bs.find_all("table"):  # 移除不必要的table信息
                for table in outer_bs.find_all("table"):
                    table.extract()
            outer_message = outer_bs.get_text().replace("\n", "")
            flag = -1
            logging.error("Upload this torrent Error,The Server echo:\"{0}\",Stop Posting".format(outer_message))
        return flag

    def exist_judge(self, search_title, torrent_file_name):
        """如果种子在byr存在，返回种子id，不存在返回0，已存在且种子一致返回种子号，不一致返回-1"""
        search_url = "http://bt.byr.cn/torrents.php?search={key}&search_mode=2".format(key=search_title)
        exits_judge_raw = requests.get(url=search_url, cookies=self.cookies)
        bs = BeautifulSoup(exits_judge_raw.text, "lxml")
        tag = 0
        if bs.find_all("a", href=re.compile("download.php")):  # 如果存在（还有人比Autoseed快。。。
            href = bs.find_all("a", href=re.compile("download.php"))[0]["href"]
            tag_temp = re.search("id=(\d+)", href).group(1)  # 找出种子id
            # 使用待发布种子全名匹配已有种子的名称
            details_page = requests.get("http://bt.byr.cn/details.php?id={0}&hit=1".format(tag_temp),
                                        cookies=self.cookies)
            details_bs = BeautifulSoup(details_page.text, "lxml")
            torrent_title_in_site = details_bs.find("a", class_="index", href=re.compile(r"^download.php")).string
            torrent_title = re.search(r"\[BYRBT\]\.(.+?)\.torrent", torrent_title_in_site).group(1)
            if torrent_file_name == torrent_title:  # 如果匹配，返回种子号
                tag = tag_temp
            else:  # 如果不匹配，返回-1
                tag = -1
        return tag
