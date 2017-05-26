# ！/usr/bin/python3
# -*- coding: utf-8 -*-

from utils.loadsetting import setting
from .mediainfo import MediaInfo
from .thumbnails import thumbnails

raw_dict = setting.extend_descr_raw


def out(raw, torrent, clone_id, encode="bbcode") -> str:
    file = setting.trans_downloaddir + "/" + torrent.files()[0]["name"]
    before = build_before(encode)
    shot = build_shot(file=file, encode=encode)
    media_info = build_mediainfo(file=file, encode=encode)
    clone_info = build_clone_info(before_torrent_id=clone_id, encode=encode)

    return """{before}{raw}{shot}{mediainfo}{clone_info}""" \
        .format(before=before, raw=raw, shot=shot, mediainfo=media_info, clone_info=clone_info)


def build_before(encode) -> str:
    str_before = ""
    if raw_dict["before"]["status"]:
        min_time = int(setting.torrent_minSeedTime / 86400)
        max_time = int(setting.torrent_maxSeedTime / 86400)
        str_before = raw_dict["before"][encode].format(min_reseed_time=min_time, max_reseed_time=max_time)
    return str_before


def build_shot(file, encode) -> str:
    str_screenshot = ""
    if raw_dict["shot"]["status"]:
        file_url = thumbnails(file=file)
        if file_url:
            str_screenshot = raw_dict["shot"][encode].format(img_url=file_url)
    return str_screenshot


def build_clone_info(before_torrent_id, encode) -> str:
    str_clone_info = ""
    if raw_dict["clone_info"]["status"]:
        str_clone_info = raw_dict["clone_info"][encode].format(torrent_id=before_torrent_id)
    return str_clone_info


def build_mediainfo(file, encode) -> str:
    str_media_info = ""
    if raw_dict["mediainfo"]["status"]:
        media_info = MediaInfo(file=file, encode=encode).show()
        if media_info:
            str_media_info = raw_dict["mediainfo"][encode].format(info=media_info)
    return str_media_info
