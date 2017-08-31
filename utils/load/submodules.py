# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0


import transmissionrpc

from utils.database import Database
from utils.load.config import setting

# from utils.serverchan import ServerChan

# -*- Assign Sub-module -*-
db = Database(host=setting.db_address, port=setting.db_port, db=setting.db_name,
              user=setting.db_user, password=setting.db_password)  # Database with its function
tc = transmissionrpc.Client(address=setting.trans_address, port=setting.trans_port,  # Transmission
                            user=setting.trans_user, password=setting.trans_password)
# push = ServerChan(status=setting.ServerChan_status, key=setting.ServerChan_SCKEY)
