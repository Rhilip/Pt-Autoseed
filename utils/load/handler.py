# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>

import logging
from logging.handlers import RotatingFileHandler

from utils.load.config import setting

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

rootLogger = logging.getLogger('')  # Logging
rootLogger.setLevel(logging.NOTSET)
while rootLogger.handlers:  # Remove un-format logging in Stream, or all of messages are appearing more than once.
    rootLogger.handlers.pop()
rootLogger.addHandler(fileHandler)
rootLogger.addHandler(consoleHandler)

# Disable log messages from the Requests library
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
