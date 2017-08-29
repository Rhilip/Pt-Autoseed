# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

"""
The Enhance module to get mediainfo, and show it in torrent's description.

Warning : To enable this module, You should follow those steps:
 -  Install `mediainfo` : apt-get -y install mediainfo

"""

import logging
import re
import subprocess

from utils.load.config import setting

dict_mediainfo = setting.extend_descr_raw["mediainfo"]

baseCommand = "mediainfo {option} {FileName}"


def show_mediainfo(file, encode="bbcode"):
    option = ""
    if encode == "html":
        option += " --Output=HTML"
    command = baseCommand.format(option=option, FileName=file)

    logging.debug("Run Command: {command}.".format(command=command))
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

    if not error:
        output = output.decode()  # bytes -> string

        # Hide file path
        short_file = re.search(r"(?:.+/)?(.+)$", file).group(1)
        output = re.sub(file, short_file, output)

        if encode == "html":
            # Raw HTML Format may like this.
            """
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
            output = re.search(r"<body>(?P<in>.+)</body>", output, re.S).group("in")  # Move unnecessary tag
    else:
        logging.error("Something ERROR when get mediainfo,With Return: {err}".format(err=error))
        output = None

    return output


def build_mediainfo(file, encode) -> str:
    str_media_info = ""
    if dict_mediainfo["status"]:
        media_info = show_mediainfo(file=file, encode=encode)
        if media_info:
            str_media_info = dict_mediainfo[encode].format(info=media_info)
    return str_media_info


if __name__ == '__main__':
    movie = ""
    print(show_mediainfo(file=movie, encode="html"))
