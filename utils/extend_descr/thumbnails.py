import os
import base64
import logging
from utils.loadsetting import setting

thumbnails_pattern = "/thumbnails"

web_loc = setting.web_loc
web_url = setting.web_url
web_loc_pat = "{web_loc}{pat}".format(web_loc=web_loc, pat=thumbnails_pattern)

if not os.path.exists(web_loc_pat):
    os.makedirs(web_loc_pat)


def thumbnails(file) -> str:
    file_url = None
    shot_file_name = base64.b64encode(bytes(file, "utf-8")).decode("utf-8")[0:32]
    thumbnails_file_name = "{file}.png".format(file=shot_file_name)
    thu_file_loc = "{web_loc_pat}/{s_f}".format(web_loc_pat=web_loc_pat, s_f=thumbnails_file_name)

    stderr = 0
    if not os.path.isfile(thu_file_loc):
        # TODO Automatically generated Screenshot time.
        ffmpeg_sh = "ffmpeg -ss 00:10:10 -y -i {file} -vframes 1 {thu_loc}".format(file=file, thu_loc=thu_file_loc)
        stderr = os.system(ffmpeg_sh)  # err -> 1

    if stderr == 0:
        file_url = "{web_url}{pat}/{s_f}".format(web_url=web_url, pat=thumbnails_pattern, s_f=thumbnails_file_name)
        logging.info("The screenshot of \"{0}\" save on: \"{1}\"".format(file, thu_file_loc))
    else:
        logging.warning("Can't get Screenshot for \"{0}\".".format(file))

    return file_url
