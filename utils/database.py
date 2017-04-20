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
        """提交SQL语句"""
        cursor = self.db.cursor()
        try:
            cursor.execute(sql)
            self.db.commit()
            cursor.close()
            logging.debug("A commit to db success,DDL: \"{sql}\"".format(sql=sql))
        except:
            logging.critical("A commit to db ERROR,DDL: " + sql)
            self.db.rollback()

    def get_sql(self, sql: str):
        """从数据库中获取数据"""
        cursor = self.db.cursor()
        row = cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        logging.debug("Some information from db,DDL: \"{sql}\",Affect rows: {row}".format(sql=sql, row=row))
        return result

    def get_max_in_column(self, table, column):
        """从数据库中找到该表该列最大值"""
        sql = "SELECT MAX(" + column + ") FROM `" + table + "`"
        result = self.get_sql(sql)
        t = result[0][0]
        if not t:
            t = 0
        return t

    def get_table_seed_list(self, decision: str = None):
        """从db获取seed_list"""
        sql = "SELECT id,title,download_id,seed_id FROM seed_list"
        if decision:
            sql = "{sql} {decision}".format(sql=sql, decision=decision)
        return self.get_sql(sql)

    def get_raw_info(self, torrent_search_name, table, column):
        """从数据库中获取剧集简介（根据种子文件的search_name搜索对应数据库）"""
        search_name = torrent_search_name.replace(" ", "%").replace(".", "%")  # 模糊匹配
        sql = "SELECT * FROM {table} WHERE {column} " \
              "LIKE '{search_name}%'".format(table=table, column=column, search_name=search_name)
        return self.get_sql(sql)[0]
