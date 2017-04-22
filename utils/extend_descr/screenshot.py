import logging
import os
# TODO Split this util


def screenshot(setting, screenshot_file, file):
    ret_str = ""
    file_loc = "{web_loc}/{s_file}".format(web_loc=setting.web_loc, s_file=screenshot_file)

    ffmpeg_sh = "ffmpeg -ss 00:10:10 -y -i {file} -vframes 1 {file_loc}".format(file=file, file_loc=file_loc)
    shot = os.system(ffmpeg_sh)

    if shot == 0:
        ret_str = setting.descr_screenshot(url="{web_url}/{s_f}".format(web_url=setting.web_url, s_f=screenshot_file))
        logging.info("The screenshot of \"{0}\" save on: \"{1}\"".format(file, file_loc))
    else:
        logging.warning("Can't get Screenshot for \"{0}\".".format(screenshot_file))

    return ret_str
