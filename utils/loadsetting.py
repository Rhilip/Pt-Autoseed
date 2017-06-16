import logging
from logging.handlers import RotatingFileHandler

import transmissionrpc

from utils.database import Database, MySQLHandler
from utils.serverchan import ServerChan

try:
    import usersetting as setting
except ImportError:
    import setting

# -*- Assign Sub-module -*-
db = Database(host=setting.db_address, port=setting.db_port, db=setting.db_name,
              user=setting.db_user, password=setting.db_password)  # Database with its function
tc = transmissionrpc.Client(address=setting.trans_address, port=setting.trans_port,  # Transmission
                            user=setting.trans_user, password=setting.trans_password)
push = ServerChan(status=setting.ServerChan_status, key=setting.ServerChan_SCKEY)

# -*- Assign logging Handler -*-
logging_level = logging.INFO
if setting.logging_debug_level:
    logging_level = logging.DEBUG

logFormatter = logging.Formatter(fmt=setting.logging_format, datefmt=setting.logging_datefmt)

fileHandler = RotatingFileHandler(filename=setting.logging_filename, mode='a', backupCount=2,
                                  maxBytes=setting.logging_file_maxBytes, encoding=None, delay=0)
fileHandler.setFormatter(logFormatter)
fileHandler.setLevel(logging_level)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)

dbHandler = MySQLHandler(db=db)
dbHandler.setLevel(logging.INFO)
