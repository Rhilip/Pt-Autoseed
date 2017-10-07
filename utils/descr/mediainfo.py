# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

"""
The Enhance module to get mediainfo, and show it in torrent's description.

 1.Use mediainfo-cli, You should install firstly, for example: `apt-get -y install mediainfo`

 2. when add `--Output=HTML` as option, Raw HTML Format may like this. It is not beautify
    (although you can use another format), So I choose change "\n" to HTML line-break tag "<br>"
<html>
    <head><META http-equiv="Content-Type" content="text/html; charset=utf-8" /></head>
    <body>
        {foreach track}
            <table width="100%" border="0" cellpadding="1" cellspacing="2" style="border:1px solid Navy">
                {foreach $track -> stream}
                    <tr>
                        <td><i>{$stream -> name}</i></td>
                        <td colspan="3">{$stream -> detail}</td>
                    </tr>
                {/foreach}
            </table>
            <br />
        {/foreach}
        <br />
    </body>
</html>
"""

import logging
import os
import re
import subprocess

from utils.load.config import setting

dict_mediainfo = setting.extend_descr_raw["mediainfo"]
track_tag = ["General", "Video", "Audio", "Text", "Other"]


def show_mediainfo(file, encode="bbcode"):
    logging.debug("Run Command: \"mediainfo '{file}'\" to get Mediainfo.".format(file=file))
    process = subprocess.Popen(["mediainfo", file], stdout=subprocess.PIPE)
    output, error = process.communicate()

    if not error and output != b"\n":
        output = output.decode()  # bytes -> string
        output = re.sub(re.escape(file), os.path.basename(file), output)  # Hide file path

        strong_tag = r"[b]\1[/b]\2"
        if encode == "html":
            strong_tag = r"<strong>\1</strong>\2"
            output = re.sub("\n", "<br>", output)  # Change \n -> <br>

        output = re.sub("(" + "|".join(track_tag) + ")(\n|<br>)", strong_tag, output)  # Strong Track menu
    else:
        logging.error("Something ERROR when get mediainfo,With Return: {err}".format(err=error))
        output = None

    return output


def build_mediainfo(file, encode="bbcode") -> str:
    str_media_info = ""
    if dict_mediainfo["status"]:
        media_info = show_mediainfo(file=file, encode=encode)
        if media_info:
            str_media_info = dict_mediainfo[encode].format(info=media_info)
    return str_media_info


if __name__ == '__main__':
    movie = ""
    print(show_mediainfo(file=movie, encode="html"))
