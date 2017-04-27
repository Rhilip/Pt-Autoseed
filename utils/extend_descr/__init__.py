# ！/usr/bin/python3
# -*- coding: utf-8 -*-


def extend_descr(setting, torrent, raw, before_torrent_id) -> str:
    from .mediainfo import show_media_info as media_info
    from .screenshot import screenshot as shot
    file = setting.trans_downloaddir + "/" + torrent.files()[0]["name"]
    screenshot_file = "screenshot/{file}.png".format(file=str(torrent.files()[0]["name"]).split("/")[-1])
    shot = shot(setting, screenshot_file, file)
    media_info = media_info(setting, file=file)
    clone_info = setting.descr_clone_info(before_torrent_id=before_torrent_id)
    return """{before}{raw}{shot}{mediainfo}{clone_info}""" \
        .format(before=setting.descr_before(), raw=raw, shot=shot, mediainfo=media_info, clone_info=clone_info)
