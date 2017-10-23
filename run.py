# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

# -*- Loading Model -*-
from utils.controller import Controller
from utils.load.handler import rootLogger

if __name__ == '__main__':
    controller = Controller()  # Connect
    rootLogger.info("Initialization settings Success~")
    controller.start()
