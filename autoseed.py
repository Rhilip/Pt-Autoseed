# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import time

from utils.connect import Connect
from utils.load.config import setting
from utils.load.handler import rootLogger

connect = Connect()  # Connect
rootLogger.info("Initialization settings Success~")
# -*- End of Loading Model -*-


def main():
    rootLogger.info("Autoseed start~,will check database record at the First time.")
    last_id_check = connect.update_torrent_info_from_rpc_to_db(force_clean_check=True)
    i = 0
    while True:
        connect.update_torrent_info_from_rpc_to_db()  # 更新表
        connect.reseeders_update()  # reseed判断主函数

        sleep_time = setting.sleep_free_time
        if setting.busy_start_hour <= int(time.strftime("%H", time.localtime())) < setting.busy_end_hour:
            sleep_time = setting.sleep_busy_time

        rootLogger.debug("Check time {ti} OK, Reach check id {cid},"
                         " Will Sleep for {slt} seconds.".format(ti=i, cid=last_id_check, slt=sleep_time))

        i += 1
        time.sleep(sleep_time)


if __name__ == '__main__':
    main()
