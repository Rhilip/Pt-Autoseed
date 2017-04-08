import pymysql
try:
    import userconfig as config
except ImportError:
    import config

db = pymysql.connect(host=config.MYSQL_HOST, port=config.MYSQL_PORT,
                     user=config.MYSQL_USER, password=config.MYSQL_PASS,
                     db=config.MYSQL_DB, charset='utf8')


def find_max_in_rss_record(db, table):
    cursor = db.cursor()
    sql = "SELECT MAX(id) FROM `{0}`".format(table)
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    t = result[0][0]
    if not t:
        t = 0
    return t


def commit_cursor_into_db(db, sql):
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        db.commit()
        cursor.close()
    except:
        db.rollback()
