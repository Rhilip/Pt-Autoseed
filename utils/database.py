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

    def get_table_seed_list_limit(self, tracker_list, operator, condition, other_decision=""):
        tracker_list_judge = []
        for i in tracker_list:
            tracker_list_judge.append("`{j}` {con}".format(j=i, con=condition))
        raw_judge = ' {oper} '.format(oper=operator).join(tracker_list_judge)
        judge = "WHERE {raw} {left}".format(raw=raw_judge, left=other_decision)
        return self.get_table_seed_list(decision=judge)

    def get_data_clone_id(self, key, site, table='info_list', column='search_name', clone_id=None):
        key = key.replace(" ", "%").replace(".", "%")
        sql = "SELECT * FROM `{tb}` WHERE `{cow}` LIKE '{key}%'".format(tb=table, cow=column, key=key)
        try:  # Get series info from database
            clone_id = self.get_sql(sql, r_dict=True)[0][site]
        except IndexError:  # The database doesn't have the search data, Return `None`
            pass

        return clone_id

    def reseed_update(self, did, rid, site):
        sql = "UPDATE seed_list SET `{col}` = {rid} WHERE download_id={did}".format(col=site, rid=rid, did=did)
        self.commit_sql(sql)
