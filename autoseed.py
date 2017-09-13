# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import time

from utils.controller import Controller
from utils.load.config import setting
from utils.load.handler import rootLogger

controller = Controller()  # Connect
rootLogger.info("Initialization settings Success~")
# -*- End of Loading Model -*-


def main():
    rootLogger.info("Autoseed start~,will check database record at the First time.")
    i = 0
    while True:
        controller.update_torrent_info_from_rpc_to_db()  # 更新表
        controller.reseeders_update()  # reseed判断主函数

        sleep_time = setting.sleep_free_time
        if setting.busy_start_hour <= int(time.strftime("%H", time.localtime())) < setting.busy_end_hour:
            sleep_time = setting.sleep_busy_time

        rootLogger.debug("Check time {ti} OK, Reach check id {cid},"
                         " Will Sleep for {slt} seconds.".format(ti=i, cid=controller.last_id_check, slt=sleep_time))

        i += 1
        time.sleep(sleep_time)


if __name__ == '__main__':
    main()
