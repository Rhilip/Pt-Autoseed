# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import time
import logging


# 生成展示信息
def generate_web_json(setting, tr_client, data_list):
    data = []
    time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    for t in data_list:
        try:
            download_torrent = tr_client.get_torrent(t[2])
            if t[3] == 0:
                reseed_status = "Not found."
                reseed_ratio = 0
            else:
                reseed_torrent = tr_client.get_torrent(t[3])
                reseed_status = reseed_torrent.status
                reseed_ratio = reseed_torrent.uploadRatio
        except KeyError:
            logging.error("This torrent (Which name: {0}) has been deleted from transmission "
                          "(Maybe By other Management software).".format(t[1]))
            continue
        else:
            start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(download_torrent.addedDate))
            info_dict = {
                "tid": str(t[0]),
                "title": download_torrent.name,
                "size": "{:.2f} MiB".format(download_torrent.totalSize / (1024 * 1024)),
                "download_start_time": start_time,
                "download_status": download_torrent.status,
                "download_upload_ratio": "{:.2f}".format(download_torrent.uploadRatio),
                "reseed_status": reseed_status,
                "reseed_ratio": "{:.2f}".format(reseed_ratio)
            }
        data.append(info_dict)
    out_list = {
        "last_update_time": time_now,
        "data": data
    }

    with open(setting.web_loc + "/tostatus.json", "wt") as f:
        json.dump(out_list, f)

    logging.debug("Generate Autoseed's status at {time}.".format(time=time_now))
