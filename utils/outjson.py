# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import time
import logging


# 生成展示信息
def generate_web_json(setting, tr_client, data_list):
    data = []
    for cow in data_list:
        sid = cow.pop("id")
        s_title = cow.pop("title")
        try:
            download_torrent_id = cow.pop("download_id")
            download_torrent = tr_client.get_torrent(download_torrent_id)
            reseed_info_list = []
            for tracker, tid in cow.items():
                if int(tid) == 0:
                    reseed_status = "Not found."
                    reseed_ratio = 0
                else:
                    reseed_torrent = tr_client.get_torrent(tid)
                    reseed_status = reseed_torrent.status
                    reseed_ratio = reseed_torrent.uploadRatio
                reseed_info_list.append((tracker, reseed_status, reseed_ratio))
        except KeyError:
            logging.error("One of torrents (Which name: \"{0}\") may delete from transmission.".format(s_title))
        else:
            start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(download_torrent.addedDate))
            torrent_reseed_list = []
            for tracker, reseed_status, reseed_ratio in reseed_info_list:
                torrent_dict = {
                    "reseed_tracker": tracker,
                    "reseed_status": reseed_status,
                    "reseed_ratio": "{:.2f}".format(reseed_ratio)
                }
                torrent_reseed_list.append(torrent_dict)
            info_dict = {
                    "tid": sid,
                    "title": s_title,
                    "size": "{:.2f} MiB".format(download_torrent.totalSize / (1024 * 1024)),
                    "download_start_time": start_time,
                    "download_status": download_torrent.status,
                    "download_upload_ratio": "{:.2f}".format(download_torrent.uploadRatio),
                    "reseed_info": torrent_reseed_list
                }
            data.append(info_dict)
    out_list = {
        "last_update_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "data": data
    }

    with open(setting.web_loc + "/tostatus.json", "wt") as f:
        json.dump(out_list, f)

    logging.debug("Generate Autoseed's status OK.")
