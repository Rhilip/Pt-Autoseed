# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import time

# -*- Main Setting about Autoseed,Transmission,Database -*-
# Autoseed
SLEEP_TIME = 60 * 3
CYCLE_CHECK_RESEEDER_ONLINE = 60 * 10
CYCLE_SHUT_UNRESEEDER_DB = 60 * 60 * 2
CYCLE_DEL_TORRENT_CHECK = 60 * 60

# Transmission
trans_address = "localhost"
trans_port = 9091
trans_user = ""
trans_password = ""
trans_watchdir = ""
trans_downloaddir = ""

# Database_MySQL
db_address = "localhost"
db_port = 3306
db_user = ""
db_password = ""
db_name = ""
# -*- End of Main Setting -*-

# -*- Reseed Site Setting -*-
# """Byrbt"""
site_byrbt = {
    "status": True,  # default: False
    "cookies": "",  # raw_cookies
    "passkey": "",
}
# """NPUBits"""
site_npubits = {
    "status": True,
    "cookies": "",
    "passkey": "",
}
# """MTPT(nwsuaf6)"""
site_nwsuaf6 = {
    "status": True,
    "cookies": "",
    "passkey": "",
}
# """TJUPT"""
site_tjupt = {
    "status": True,
    "cookies": "",
    "passkey": "",
}
# -*- End of Reseed Site Setting -*-

# -*- Feeding Torrent Setting -*-
# Reseed_Torrent_Setting
torrent_maxUploadRatio = 3
torrent_minSeedTime = 86400
torrent_maxSeedTime = 691200
# -*- End of Feeding Torrent Setting -*-

# -*- Show status Setting -*-
# Show Site
web_url = "http://"  # demo网站的url
web_loc = "/var/www"  # demo网站在服务器上的地址

# Logging
logging_debug_level = False  # debug model
logging_filename = "autoseed.log"
logging_file_maxBytes = 5 * 1024 * 1024
logging_format = "%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
logging_datefmt = "%m/%d/%Y %I:%M:%S %p"

# ServerChan
"具体见：http://sc.ftqq.com/，用于向微信通知发种机发布状态"
ServerChan_status = False
ServerChan_SCKEY = ""
# -*- End of Show status Setting -*-

# -*- Extended description Setting -*-
min_time = int(torrent_minSeedTime / 86400)
max_time = int(torrent_maxSeedTime / 86400)

extend_descr_raw = {
    "before": {  # Key : min_reseed_time, max_reseed_time
        "status": True,
        "bbcode": """
        [quote]
        [*]这是一个自动发种的文件，所有信息以主标题或者文件名为准，简介信息采用本站之前相关种子信息，若发现有误请以"举报"或"留言"的形式通知工作人员审查和编辑。
        [*]欢迎下载、辅种、分流。保种{min_reseed_time}-{max_reseed_time}天。断种恕不补种。
        [*]如果发布档较大，请耐心等待校验。
        [*]有关更新说明请查看对应 Github :[url=https://github.com/Rhilip/Pt-Autoseed]Rhilip/Pt-Autoseed[/url]，申请搬运，请发Issues留言。
        [/quote]""".format(min_reseed_time=min_time, max_reseed_time=max_time),
        "html": """
        <fieldset class="autoseed">
            <legend><b>Quote:</b></legend>
            <ul>
                <li>这是一个远程发种的文件，所有信息以主标题或者文件名为准，简介信息采用本站之前信息，若发现有误请以"举报"或"留言"的形式通知工作人员审查和编辑。</li>
                <li>欢迎下载、辅种、分流。保种{min_reseed_time}-{max_reseed_time}天。断种恕不补种。</li>
                <li>如果发布档较大，请耐心等待校验。</li>
                <li>请勿上传机翻字幕，如有发现请"举报"。</li>
                <li>有关更新说明请查看对应 Github : <a href="https://github.com/Rhilip/Pt-Autoseed" target="_blank">Rhilip/Pt-Autoseed</a> ，申请搬运，请发Issues留言。</li>
            </ul>
        </fieldset>
        """.format(min_reseed_time=min_time, max_reseed_time=max_time)
    },
    "thumbnails": {  # Key : img_url
        "status": False,
        "bbcode": """
        [quote][color=Red]以下是Autoseed自动完成的截图，不喜勿看 [/color]
        [img]{img_url}[/img]
        [/quote]""",
        "html": """
        <fieldset class="autoseed">
            <legend><b>自动截图</b></legend>
                <ul>
                    <li><span style="color:red">以下是<a href="//github.com/Rhilip/Byrbt-Autoseed" target="_blank">Autoseed</a>自动完成的截图，不喜勿看。</span></li>
                </ul>
                <img src="{img_url}" style="max-width: 100%">
        </fieldset>
        """
    },
    "mediainfo": {  # Key : info
        "status": True,
        "bbcode": "[quote=MediaInfo (自动生成，仅供参考)]{info}[/quote]",
        "html": """
        <fieldset class="autoseed">
            <legend><b>MediaInfo:（自动生成，仅供参考）</b></legend>
            <div id="mediainfo">{info}</div>
        </fieldset>
        """
    },
    "clone_info": {  # Key : torrent_id
        "status": True,
        "bbcode": "[quote=Clone Info]该种子信息克隆自本站种子： [url=/details.php?id={torrent_id}&hit=1]{torrent_id}[/url][/quote]",
        "html": """
        <div class="byrbt_info_clone autoseed" data-clone="{torrent_id}" data-version="Autoseed" style="display:none">
            <a href="https://github.com/Rhilip/Pt-Autoseed" target="_blank">Powered by Rhilip's Autoseed</a>
        </div>
        """
    }
}
# -*- End of Extended description Setting -*-


# Other Function
def pre_delete_judge(torrent) -> bool:
    """
    According to the incoming torrent's information to determine whether can be deleted or not,
    Default process: Match Minimal time -> Match Maximum time or Maximum upload Ratio
    
    :param torrent: class transmissionrpc.Torrent
    :return: bool, True if Meet the criteria
    """
    judge = False
    # Determine conditions
    if torrent.status == "seeding":
        torrent_live_time = int(time.time() - torrent.addedDate)
        if torrent_live_time >= torrent_minSeedTime and \
                (torrent.uploadRatio >= torrent_maxUploadRatio or torrent_live_time >= torrent_maxSeedTime):
            judge = True  # Meet the criteria, return True

    return judge
