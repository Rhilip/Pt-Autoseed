#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

from utils.descr.mediainfo import build_mediainfo
from utils.descr.thumbnails import build_shot
from utils.load.config import setting

dict_setting = setting.extend_descr_raw


def build_before(encode) -> str:
    return dict_setting["before"][encode] if dict_setting["before"]["status"] else ""


def build_clone_info(clone_id, encode) -> str:
    str_clone_info = ""
    if dict_setting["clone_info"]["status"]:
        str_clone_info = dict_setting["clone_info"][encode].format(torrent_id=clone_id)
    return str_clone_info
