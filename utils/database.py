# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import logging
import re
from threading import Lock

import pymysql


class Database(object):
    cache_torrent_name = []
    _commit_lock = Lock()

    def __init__(self, host, port, user, password, db):
        self.db = pymysql.connect(host=host, port=port, user=user, password=password, db=db,
                                  charset='utf8', autocommit=True)

        self.col_seed_list = [i[0] for i in self.exec("SHOW COLUMNS FROM `seed_list`", fetch_all=True)]

    # Based Function
    def exec(self, sql: str, args=None, r_dict: bool = False, fetch_all: bool = False, ret_rows: bool = False):
        with self._commit_lock:
            cursor = self.db.cursor(pymysql.cursors.DictCursor) if r_dict else self.db.cursor()  # Cursor type
            row = cursor.execute(sql, args)
            data = cursor.fetchall() if fetch_all else cursor.fetchone()  # The lines of return info (one or all)
            logging.debug(
                "Success, DDL: \"{sql}\",args:\"{args}\",Affect rows: {row}".format(sql=sql, args=(args or ""),
                                                                                    row=row))

        return (row, data) if ret_rows else data

    # Procedure Oriented Function
    def get_max_in_seed_list(self, column_list: list or str) -> int:
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
        sql = "SELECT `{site}` FROM `info_list` WHERE `search_name` LIKE '{key}'".format(site=site, key=key)
        try:  # Get clone id info from database
            clone_id = int(self.exec(sql=sql)[0])
        except TypeError:  # The database doesn't have the search data, Return dict only with raw key.
            logging.warning(
                "No record for key: \"{key}\" in \"{site}\". Or may set as `None`".format(key=key, site=site)
            )

        return clone_id

    def upsert_seed_list(self, torrent_info: tuple):
        tid, name, tracker = torrent_info
        raw_sql = ("INSERT INTO `seed_list` (`title`,`{cow}`) "
                   "VALUES (%(name)s,%(id)s) "
                   "ON DUPLICATE KEY UPDATE `{cow}`=VALUES(`{cow}`)".format(cow=tracker))
        return self.exec(sql=raw_sql, args={"name": name, "id": tid})
