# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import logging
from logging.handlers import RotatingFileHandler

import utils
import transmissionrpc
from extractors import Autoseed

try:
    import usersetting as setting
except ImportError:
    import setting

# -*- Logging Setting -*-
logging_level = logging.INFO
if setting.logging_debug_level:
    logging_level = logging.DEBUG

logFormatter = logging.Formatter(fmt=setting.logging_format, datefmt=setting.logging_datefmt)
rootLogger = logging.getLogger('')
rootLogger.setLevel(logging.NOTSET)

fileHandler = RotatingFileHandler(filename=setting.logging_filename, mode='a', backupCount=2,
                                  maxBytes=setting.logging_file_maxBytes, encoding=None, delay=0)
fileHandler.setFormatter(logFormatter)
fileHandler.setLevel(logging_level)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
# -*- End of Logging Setting -*-

# -*- Loading Model -*-
db = utils.Database(setting)  # Database with its function
tc = transmissionrpc.Client(address=setting.trans_address, port=setting.trans_port,  # Transmission
                            user=setting.trans_user, password=setting.trans_password)
autoseed = Autoseed(setting=setting, tr_client=tc, db_client=db)  # Autoseed
connect = utils.Connect(tc_client=tc, db_client=db, tracker_list=autoseed.tracker_list, setting=setting)  # Connect
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
    logging.info("Initialization settings Success~")
    main()
