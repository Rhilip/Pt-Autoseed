# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

"""
The Enhance module to get thumbnails, and show it in torrent's description.
Use "/thumbnails/{hash}.jpg" as the src of thumbnails image,
If the image file is not exist anymore, the default "404.jpg" will return.

Warning : To enable this module, You should follow those steps:
1. Install `ffmpeg` : apt-get -y install ffmpeg
2. Have the web service, and move the file "web/404.jpg" to your web server root.
3. Manage your web service's config, For nginx ,you may add :
   ```
    location /thumbnails {
        try_files $uri /404.jpg =404;
    }
   ```
4. Install Crontab to auto del unnecessary images ,for example,
    `0 23 * * 6 find dir/to/thumbnails/ -mtime +30 -name "*.jpg" -exec rm -rf {} \;`
"""

import base64
import logging
import os

from utils.load.config import setting

dict_thumbnails = setting.extend_descr_raw["thumbnails"]

thumbnails_pattern = "thumbnails"  # Notes: Change with `pic.php` together
web_loc_pat = os.path.join(setting.web_loc, thumbnails_pattern)
web_url_pat = setting.web_url + "/" + thumbnails_pattern

if not os.path.exists(web_loc_pat):
    os.makedirs(web_loc_pat)

baseCommand = "ffmpeg -ss 00:10:10 -y -i '{file}' -vframes 1 '{thu_loc}' >> /dev/null 2>&1"


def thumbnails(file, img_url=None, img_file_loc=None) -> str:
    img_hash = base64.b64encode(bytes(file, "utf-8")).decode()[-32:]
    img_file_name = "{}.jpg".format(img_hash)
    img_file_loc = img_file_loc or os.path.join(web_loc_pat, img_file_name)

    stderr = 0
    if not os.path.isfile(img_file_loc):
        # TODO Automatically generated Screenshot time.
        ffmpeg_sh = baseCommand.format(file=file, thu_loc=img_file_loc)
        logging.debug("Run Command: \"{command}\" to get Thumbnails.".format(command=ffmpeg_sh))
        stderr = os.system(ffmpeg_sh)

    if stderr == 0:
        img_url = img_url or "{web_url}/{file}".format(web_url=web_url_pat, file=img_file_name)
        logging.info("The thumbnail of \"{0}\" save on: \"{1}\", with uri: \"{2}\"".format(file, img_file_loc, img_url))
    else:
        logging.warning("Can't get Screenshot for \"{0}\".".format(file))

    return img_url


def build_shot(file, encode="bbcode") -> str:
    str_thumbnails = ""
    if dict_thumbnails["status"]:
        file_url = thumbnails(file=file)
        if file_url:
            str_thumbnails = dict_thumbnails[encode].format(img_url=file_url)
    return str_thumbnails


if __name__ == "__main__":
    movie_file = ""
    print(thumbnails(file=movie_file))
