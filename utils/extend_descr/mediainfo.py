# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import logging
import subprocess

baseCommand = "mediainfo {option} {FileName}"


def show_mediainfo(file, encode):
    option = ""
    if encode == "html":
        option += " --Output=HTML"
    command = baseCommand.format(option=option, FileName=file)

    logging.debug("Run Command: {command}.".format(command=command))
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

    if not error:
        output = output.decode()
    else:
        output = None

    return output
