# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import pymysql
import logging


class Database(object):
    def __init__(self, setting):
        self.db = pymysql.connect(host=setting.db_address, port=setting.db_port,
                                  user=setting.db_user, password=setting.db_password,
                                  db=setting.db_name, charset='utf8')

    def commit_sql(self, sql: str):
        """Submit SQL statement"""
        cursor = self.db.cursor()
        try:
            cursor.execute(sql)
            self.db.commit()
            cursor.close()
            logging.debug("A commit to db success,DDL: \"{sql}\"".format(sql=sql))
        except:
            logging.critical("A commit to db ERROR,DDL: " + sql)
            self.db.rollback()

    def get_sql(self, sql: str, r_dict=False):
        """Get data from the database"""
        cursor = self.db.cursor()
        if r_dict:  # 以字典形式返回
            cursor = self.db.cursor(pymysql.cursors.DictCursor)
        row = cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        logging.debug("Some information from db,DDL: \"{sql}\",Affect rows: {row}".format(sql=sql, row=row))
        return result

    def get_max_in_one_column(self, table, column):
        """Find the maximum value of the table in that column from the database"""
        sql = "SELECT MAX(`" + column + "`) FROM `" + table + "`"
        result = self.get_sql(sql)
        t = result[0][0]
        if not t:
            t = 0
        return t

    def get_max_in_column(self, table, column_list: list or str, max_num=0):
        """Find the maximum value of the table in a list of column from the database"""
        if isinstance(column_list, list):
            for column in column_list:
                t = self.get_max_in_one_column(table=table, column=column)
                max_num = max(max_num, t)
        else:
            max_num = self.get_max_in_one_column(table=table, column=column_list)
        logging.debug("Max number in column:{co} is {mn}".format(mn=max_num, co=column_list))
        return max_num

    def get_table_seed_list(self, decision: str = None):
        """从db获取seed_list"""
        sql = "SELECT * FROM seed_list"
        if decision:
            sql = "{sql} {decision}".format(sql=sql, decision=decision)
        return self.get_sql(sql, r_dict=True)

    def _get_raw_info(self, torrent_search_name, table, column):
        """从数据库中获取剧集简介（根据种子文件的search_name搜索对应数据库）"""
        search_name = torrent_search_name.replace(" ", "%").replace(".", "%")  # 模糊匹配
        sql = "SELECT * FROM {table} WHERE {column} " \
              "LIKE '{search_name}%'".format(table=table, column=column, search_name=search_name)
        return self.get_sql(sql, r_dict=True)[0]

    def data_raw_info(self, torrent_info_search, table, column):
        search_name = torrent_info_search.group("search_name")
        try:  # Get series info from database
            torrent_info_raw_dict_from_db = self._get_raw_info(search_name, table=table, column=column)
            logging.debug("Get series info from db OK,Which search name: \"{name}\"".format(name=search_name))
        except IndexError:  # The database doesn't have the search data, using the default information
            torrent_info_raw_dict_from_db = self._get_raw_info("default", table=table, column=column)
            torrent_name = torrent_info_search.group(0)
            logging.warning("Not Find info from db of torrent: \"{0}\",Use normal template!!".format(torrent_name))
        return torrent_info_raw_dict_from_db
