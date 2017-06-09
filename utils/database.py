# ！/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import time

import pymysql


class Database(object):
    def __init__(self, host, port, user, password, db):
        self.db = pymysql.connect(host=host, port=port, user=user, password=password, db=db, charset='utf8')
        self.cursor = self.db.cursor()

    def commit_sql(self, sql: str, log=True):
        """Submit SQL statement"""
        try:
            self.cursor.execute(sql)
            self.db.commit()
            if log:
                logging.debug("A commit to db success,DDL: \"{sql}\"".format(sql=sql))
        except pymysql.Error as err:
            logging.critical("Mysql Error: {err},DDL: {sql}".format(err=err.args, sql=sql))
            self.db.rollback()

    def get_sql(self, sql: str, r_dict=False, fetch_all=True, log=True):
        """Get data from the database"""
        if r_dict:  # Dict Cursor
            cursor = self.db.cursor(pymysql.cursors.DictCursor)
        else:
            cursor = self.cursor
        row = cursor.execute(sql)
        if fetch_all:
            result = cursor.fetchall()
        else:
            result = cursor.fetchone()
        if log:
            logging.debug("Some information from db,DDL: \"{sql}\",Affect rows: {row}".format(sql=sql, row=row))
        return result

    def get_max_in_one_column(self, table, column, log=True):
        """Find the maximum value of the table in that column from the database"""
        sql = "SELECT MAX(`" + column + "`) FROM `" + table + "`"
        result = self.get_sql(sql, log=log)
        t = result[0][0]
        if not t:
            t = 0
        return t

    def get_max_in_columns(self, table, column_list: list or str, max_num=0):
        """Find the maximum value of the table in a list of column from the database"""
        if isinstance(column_list, list):
            for column in column_list:
                t = self.get_max_in_one_column(table=table, column=column, log=False)
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

    def get_data_clone_id(self, key, table='info_list', column='search_name'):
        sql = "SELECT * FROM `{tb}` WHERE `{cow}` LIKE '{key}%'".format(tb=table, cow=column, key=key.replace(" ", "%"))
        try:  # Get clone id info from database
            clone_id = self.get_sql(sql, r_dict=True)[0]
        except IndexError:  # The database doesn't have the search data, Return dict only with raw key.
            clone_id = {"search_name": key}

        return clone_id

    def reseed_update(self, did, rid, site):
        sql = "UPDATE seed_list SET `{col}` = {rid} WHERE download_id={did}".format(col=site, rid=rid, did=did)
        self.commit_sql(sql)


class MySQLHandler(logging.Handler):
    """
    Logging handler for MySQL.
    """

    initial_sql = """CREATE TABLE IF NOT EXISTS log(
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

    insertion_sql = """INSERT INTO log(
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
            self.db.commit_sql(sql=self.initial_sql, log=False)

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
