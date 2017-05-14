import logging
from logging.handlers import RotatingFileHandler

import transmissionrpc
from .extend_descr import ExtendDescr
from .database import Database

try:
    import usersetting as setting
except ImportError:
    import setting

db = Database(setting)  # Database with its function
tc = transmissionrpc.Client(address=setting.trans_address, port=setting.trans_port,  # Transmission
                            user=setting.trans_user, password=setting.trans_password)
descr = ExtendDescr(setting=setting)  # TODO Separate(It's not good idea to assign in every autoseed)

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
