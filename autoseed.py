# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import sys
import time

from extractors import Autoseed
from utils.connect import Connect
from utils.loadsetting import setting, fileHandler, consoleHandler

# -*- Logging Model -*-
rootLogger = logging.getLogger('')  # Logging
rootLogger.setLevel(logging.NOTSET)
while rootLogger.handlers:  # Remove un-format logging in Stream, or all of messages are appearing more than once.
    rootLogger.handlers.pop()
rootLogger.addHandler(fileHandler)
rootLogger.addHandler(consoleHandler)

autoseed = Autoseed()  # Autoseed
if autoseed.active_tracker:
    connect = Connect(tracker_list=autoseed.active_tracker)  # Connect
    logging.info("Initialization settings Success~")
else:
    sys.exit("None of autoseed is active,Exit.")
# -*- End of Loading Model -*-


def main():
    logging.info("Autoseed start~,will check database record at the First time.")
    last_id_check = connect.update_torrent_info_from_rpc_to_db(force_clean_check=True)
    i = 0
    while True:
        last_id_check = connect.update_torrent_info_from_rpc_to_db(last_id_check=last_id_check)  # 更新表
        autoseed.update()  # reseed判断主函数
        if i % setting.delete_check_round == 0:
            connect.check_to_del_torrent_with_data_and_db()  # 清理种子
        if setting.web_show_status:  # 发种机运行状态展示
            connect.generate_web_json()

        sleep_time = setting.sleep_free_time
        if setting.busy_start_hour <= int(time.strftime("%H", time.localtime())) < setting.busy_end_hour:
            sleep_time = setting.sleep_busy_time

        logging.debug("Check time {ti} OK, Reach check id {cid},"
                      " Will Sleep for {slt} seconds.".format(ti=i, cid=last_id_check, slt=sleep_time))

        i += 1
        time.sleep(sleep_time)


if __name__ == '__main__':
    main()
