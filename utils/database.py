# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import logging

import pymysql

name_table_info_list = "info_list"
name_table_seed_list = "seed_list"


class Database(object):

    def __init__(self, host, port, user, password, db):
        self.db = pymysql.connect(host=host, port=port, user=user, password=password, db=db, charset='utf8')

    # Based Function
    def commit_sql(self, sql: str):
        """Submit SQL statement"""
        cursor = self.db.cursor()
        try:
            cursor.execute(sql)
            self.db.commit()
            logging.debug("A commit to db success,DDL: \"{sql}\"".format(sql=sql))
        except pymysql.Error as err:
            logging.critical("Mysql Error: {err},DDL: {sql}".format(err=err.args, sql=sql))
            self.db.rollback()

    def get_sql(self, sql: str, r_dict=False, fetch_all=True):
        """Get data from the database"""
        # The style of info (dict or tuple)
        if r_dict:
            cursor = self.db.cursor(pymysql.cursors.DictCursor)  # Dict Cursor
        else:
            cursor = self.db.cursor()

        row = cursor.execute(sql)

        # The return info (one or all)
        if fetch_all:
            result = cursor.fetchall()
        else:
            result = cursor.fetchone()

        # Logging or not
        logging.debug("Some information from db,DDL: \"{sql}\",Affect rows: {row}".format(sql=sql, row=row))
        return result

    # Procedure Oriented Function
    def get_max_in_one_column(self, table, column):
        """Find the maximum value of the table in that column from the database"""
        sql = "SELECT MAX(`" + column + "`) FROM `" + table + "`"
        result = self.get_sql(sql, fetch_all=False)
        t = result[0]
        if not t:
            t = 0
        return t

    def get_whole_table(self, table, decision: str = None, fetch_all=True, r_dict=True):
        sql = "SELECT * FROM `{tb}`".format(tb=table)
        if decision:
            sql = "{sql} {decision}".format(sql=sql, decision=decision)
        return self.get_sql(sql, r_dict=r_dict, fetch_all=fetch_all)

    # Object Oriented Function
    def get_table_seed_list(self, decision: str = None):
        """Get table `seed_list` from database"""
        return self.get_whole_table(table=name_table_seed_list, decision=decision)

    def get_max_in_columns(self, table, column_list: list or str):
        """Find the maximum value of the table in a list of column from the database"""
        max_num = 0
        if isinstance(column_list, list):
            for column in column_list:
                t = self.get_max_in_one_column(table=table, column=column)
                max_num = max(max_num, t)
        else:
            max_num = self.get_max_in_one_column(table=table, column=column_list)
        logging.debug("Max number in column:{co} is {mn}".format(mn=max_num, co=column_list))
        return max_num

    def get_table_seed_list_limit(self, tracker_list, operator, condition, other_decision=""):
        tracker_list_judge = []
        for i in tracker_list:
            tracker_list_judge.append("`{j}` {con}".format(j=i, con=condition))
        raw_judge = ' {oper} '.format(oper=operator).join(tracker_list_judge)
        judge = "WHERE {raw} {left}".format(raw=raw_judge, left=other_decision)
        return self.get_table_seed_list(decision=judge)

    def get_data_clone_id(self, key, table=name_table_info_list, column='search_name'):
        decision = "WHERE `{cow}` LIKE '{key}%'".format(tb=table, cow=column, key=key.replace(" ", "%"))
        try:  # Get clone id info from database
            clone_info_dict = self.get_whole_table(table=table, decision=decision, fetch_all=False, r_dict=True)
            if clone_info_dict is None:
                raise ValueError("No db-record for key: \"{key}\".".format(key=key))
        except ValueError:  # The database doesn't have the search data, Return dict only with raw key.
            clone_info_dict = {"search_name": key}

        return clone_info_dict

    def reseed_update(self, did, rid, site):
        sql = "UPDATE seed_list SET `{col}` = {rid} WHERE download_id={did}".format(col=site, rid=rid, did=did)
        self.commit_sql(sql)
