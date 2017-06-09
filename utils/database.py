# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import time

import pymysql

name_table_info_list = "info_list"
name_table_seed_list = "seed_list"
name_table_log = "log"

create_table_info_list = """
CREATE TABLE IF NOT EXISTS `{info_list}` (
  `sort_id`           INT(11) NOT NULL,
  `search_name`       TEXT NOT NULL COMMENT '搜索名称'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""".format(info_list=name_table_info_list)

create_table_seed_list = """
CREATE TABLE IF NOT EXISTS `{seed_list}` (
  `id`                INT(11) NOT NULL,
  `title`             TEXT    NOT NULL,
  `download_id`       INT(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
""".format(seed_list=name_table_seed_list)

create_table_log = """
CREATE TABLE IF NOT EXISTS `log`(
    Created TEXT,
    Name TEXT,
    LogLevel INT,
    LogLevelName TEXT,
    Message TEXT,
    Args TEXT,
    Module TEXT,
    FuncName TEXT,
    LineNo INT,
    Exception TEXT,
    Process INT,
    Thread TEXT,
    ThreadName TEXT
    )"""


class Database(object):
    def __init__(self, host, port, user, password, db):
        self.db = pymysql.connect(host=host, port=port, user=user, password=password, db=db, charset='utf8')
        self.check_table_presence()

    # Based Function
    def commit_sql(self, sql: str, log=True):
        """Submit SQL statement"""
        cursor = self.db.cursor()
        try:
            cursor.execute(sql)
            self.db.commit()
            if log:
                logging.debug("A commit to db success,DDL: \"{sql}\"".format(sql=sql))
        except pymysql.Error as err:
            if log:
                logging.critical("Mysql Error: {err},DDL: {sql}".format(err=err.args, sql=sql))
            self.db.rollback()

    def get_sql(self, sql: str, r_dict=False, fetch_all=True, log=True):
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
        if log:
            logging.debug("Some information from db,DDL: \"{sql}\",Affect rows: {row}".format(sql=sql, row=row))
        return result

    # Table check
    def check_table_presence(self):
        log_status = False
        sql = "SHOW TABLES"
        result = self.get_sql(sql=sql, fetch_all=True, log=log_status)
        table_list = [cow[0] for cow in result]
        if name_table_seed_list not in table_list:
            self.commit_sql(sql=create_table_seed_list, log=log_status)
            # del create_table_seed_list
        if name_table_info_list not in table_list:
            self.commit_sql(sql=create_table_info_list, log=log_status)
            # del create_table_info_list

    # Procedure Oriented Function
    def get_max_in_one_column(self, table, column, log=True):
        """Find the maximum value of the table in that column from the database"""
        sql = "SELECT MAX(`" + column + "`) FROM `" + table + "`"
        result = self.get_sql(sql, log=log, fetch_all=False)
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
                t = self.get_max_in_one_column(table=table, column=column, log=False)
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

    def get_data_clone_id(self, key, table='info_list', column='search_name'):
        decision = "WHERE `{cow}` LIKE '{key}%'".format(tb=table, cow=column, key=key.replace(" ", "%"))
        try:  # Get clone id info from database
            clone_info_dict = self.get_whole_table(table=name_table_info_list, decision=decision,
                                                   fetch_all=False, r_dict=True)
            if clone_info_dict is None:
                raise ValueError("No db-record for key: \"{key}\".".format(key=key))
        except ValueError:  # The database doesn't have the search data, Return dict only with raw key.
            clone_info_dict = {"search_name": key}

        return clone_info_dict

    def reseed_update(self, did, rid, site):
        sql = "UPDATE seed_list SET `{col}` = {rid} WHERE download_id={did}".format(col=site, rid=rid, did=did)
        self.commit_sql(sql)


class MySQLHandler(logging.Handler):
    """
    Logging handler for MySQL.
    """

    insertion_sql = """INSERT INTO `log`(
    Created,
    Name,
    LogLevel,
    LogLevelName,
    Message,
    Args,
    Module,
    FuncName,
    LineNo,
    Exception,
    Process,
    Thread,
    ThreadName
    )
    VALUES (
    '%(dbtime)s',
    '%(name)s',
    '%(levelno)d',
    '%(levelname)s',
    '%(msg)s',
    '%(args)s',
    '%(module)s',
    '%(funcName)s',
    '%(lineno)d',
    '%(exc_text)s',
    '%(process)d',
    '%(thread)s',
    '%(threadName)s'
    );
    """

    def __init__(self, db: Database):
        """
        Constructor
        @param db: class utils.database.Database
        @return: mySQLHandler
        """

        logging.Handler.__init__(self)

        # Try to connect to DB
        self.db = db

        # Check if 'log' table in db already exists, else create it.
        self.check_table_presence()

    def check_table_presence(self):
        sql = "SHOW TABLES LIKE 'log'"
        result = self.db.get_sql(sql=sql, fetch_all=False, log=False)
        if not result:
            self.db.commit_sql(sql=create_table_log, log=False)
            # del create_table_log

    def emit(self, record):
        """
        Connect to DB, execute SQL Request, disconnect from DB
        @param record:
        @return: 
        """
        # Use default formatting:
        self.format(record)
        # Set the database time up:
        record.dbtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))

        if record.exc_info:
            record.exc_text = logging._defaultFormatter.formatException(record.exc_info)
        else:
            record.exc_text = ""
        # Insert log record:
        sql = self.insertion_sql % record.__dict__
        self.db.commit_sql(sql=sql, log=False)
