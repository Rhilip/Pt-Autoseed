# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import logging
import re
from threading import Lock

import pymysql

from utils.constants import TABLE_INFO_LIST, TABLE_SEED_LIST


class Database(object):
    cache_torrent_name = []

    def __init__(self, host, port, user, password, db):
        self._commit_lock = Lock()

        self.db = pymysql.connect(host=host, port=port, user=user, password=password, db=db, charset='utf8')

        self.col_seed_list = [i[0] for i in self.exec("SHOW COLUMNS FROM `seed_list`", fetch_all=True)]
        self.cache_torrent_list()

    @staticmethod
    def _safety_table(sql: str) -> str:
        # TODO It's not good, but it is useful when add or change table `seed_list
        sql = re.sub("`seed_list`", "`{}`".format(TABLE_SEED_LIST), sql)
        sql = re.sub("`info_list`", "`{}`".format(TABLE_INFO_LIST), sql)
        return sql

    # Based Function
    def exec(self, sql: str, r_dict: bool = False, fetch_all: bool = False):
        with self._commit_lock:
            # The style of return info (dict or tuple)
            cursor = self.db.cursor(pymysql.cursors.DictCursor) if r_dict else self.db.cursor()
            row = cursor.execute(self._safety_table(sql))
            try:
                self.db.commit()
                logging.debug("Success,DDL: \"{sql}\",Affect rows: {row}".format(sql=sql, row=row))
            except pymysql.Error as err:
                logging.critical("Mysql Error: \"{err}\",DDL: \"{sql}\"".format(err=err.args, sql=sql))
                self.db.rollback()

            # The lines of return info (one or all)
            return cursor.fetchall() if fetch_all else cursor.fetchone()

    def cache_torrent_list(self):
        self.cache_torrent_name = [i[0] for i in self.exec(sql="SELECT `title` FROM `seed_list`", fetch_all=True)]

    # Procedure Oriented Function
    def get_max_in_seed_list(self, column_list: list or str):
        """Find the maximum value of the table in a list of column from the database"""
        if isinstance(column_list, str):
            column_list = [column_list]
        field = ", ".join(["MAX(`{col}`)".format(col=c) for c in column_list])
        raw_result = self.exec(sql="SELECT {fi} FROM `seed_list`".format(fi=field))
        max_num = max([i for i in raw_result if i is not None] + [0])
        logging.debug("Max number in column: {co} is {mn}".format(mn=max_num, co=column_list))
        return max_num

    def get_data_clone_id(self, key, site) -> None or int:
        clone_id = None

        key = pymysql.escape_string(re.sub(r"[_\-. ]", "%", key))
        sql = "SELECT `{site}` FROM `info_list` WHERE `search_name` LIKE '{key}%'".format(site=site, key=key)
        try:  # Get clone id info from database
            clone_id = int(self.exec(sql=sql)[0])
        except TypeError:  # The database doesn't have the search data, Return dict only with raw key.
            logging.warning(
                "No record for key: \"{key}\" in \"{site}\". Or may set as `None`".format(key=key, site=site))

        return clone_id

    def upsert_seed_list(self, torrent_info):
        tid, name, tracker = torrent_info

        while True:
            if name in self.cache_torrent_name:
                raw_sql = "UPDATE `seed_list` SET `{cow}` = {id:d} WHERE `title`='{name}'"
                break
            else:
                exist = "SELECT COUNT(*) FROM `seed_list` WHERE `title`='{}'".format(pymysql.escape_string(name))
                if self.exec(sql=exist)[0] == 0:
                    raw_sql = "INSERT INTO `seed_list` (`title`,`{cow}`) VALUES ('{name}',{id:d})"
                    break
                else:
                    self.cache_torrent_list()

        sql = raw_sql.format(cow=tracker, name=pymysql.escape_string(name), id=tid)
        return self.exec(sql=sql)
