# -*- Main Setting about Autoseed,Transmission,Database -*-
# Autoseed
sleep_free_time = 600  # 空闲期脚本每次运行间隔
sleep_busy_time = 120  # 繁忙期脚本每次运行间隔
busy_start_hour = 8  # 繁忙期开始钟点 [0,24)
busy_end_hour = 14  # 繁忙期结束钟点 (busy_start_hour,24)
delete_check_round = 5  # 每多少次运行检查一次种子删除情况

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
byr_reseed = True  # TODO 暂时没有用的开关
byr_cookies = ""
byr_passkey = ""
byr_clone_mode = "database"  # "database" or "clone"
byr_anonymous_release = True  # 匿名发种
# -*- End of Reseed Site Setting -*-

# -*- Feeding Torrent Setting -*-
# Search_pattern
search_series_pattern = (
    u"(?:^[\u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ff:：]+[. ]?|^)"  # 移除平假名、片假名、中文
    "(?P<full_name>(?P<search_name>[\w\-. ]+?)[. ]"
    "(?P<tv_season>(?:(?:[Ss]\d+)?[Ee][Pp]?\d+(?:-[Ee]?[Pp]?\d+)?)|(?:[Ss]\d+)).+?(?:-(?P<group>.+?))?)"
    "(?:\.(?P<tv_filetype>\w+)$|$)"
)
search_anime_pattern = (
    "(?P<full_name>\[(?P<group>.+?)\]\[?(?P<search_name>.+?)\]?\[(?P<anime_episode>\d+)\].+)"
    "(?:\.(mp4|mkv))?"
)

# Reseed_Torrent_Setting
torrent_maxUploadRatio = 3
torrent_minSeedTime = 86400
torrent_maxSeedTime = 691200
# -*- End of Feeding Torrent Setting -*-

# -*- Show status Setting -*-
# Show Site
web_url = "http://"  # demo网站的url
web_loc = "/var/www"  # demo网站在服务器上的地址
web_show_status = True  # 是否生成json信息
web_show_entries_number = 10  # 展示页面显示的做种条目数量

# Logging
logging_debug_level = False  # debug模式
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
# Function switch
descr_before_status = True
descr_media_info_status = True
descr_screenshot_status = True
descr_clone_info_status = True


# Function realization
def descr_before(str_before=""):
    if descr_before_status:
        str_before = """
    <fieldset class="autoseed">
        <legend><b>Quote:</b></legend>
        <ul>
            <li>这是一个远程发种的文件，所有信息以主标题或者文件名为准，简介信息采用本站之前剧集信息，若发现有误请以"举报"的形式通知工作人员审查和编辑。</li>
            <li>欢迎下载、辅种、分流。保种{min_reseed_time}-{max_reseed_time}天。断种恕不补种。</li>
            <li>如果发布档较大，请耐心等待校验。</li>
            <li>请勿上传机翻字幕，如有发现请"举报"。</li>
            <li>欧美剧更新说明请查看论坛区： <a href="/forums.php?action=viewtopic&forumid=7&topicid=10140" target="_blank">剧集区--欧美剧播放列表及订阅列表</a> ，申请补发、搬运，请于该帖按格式留言。</li>
        </ul>
    </fieldset><br />
    """.format(min_reseed_time=(int(torrent_minSeedTime / 86400)), max_reseed_time=(int(torrent_maxSeedTime / 86400)))
    return str_before


def descr_screenshot(url: str, str_screenshot="") -> str:
    if descr_screenshot_status:
        str_screenshot = """
    <fieldset class="autoseed">
        <legend><b>自动截图</b></legend>
        <ul>
            <li><span style="color:red">以下是<a href="//github.com/Rhilip/Byrbt-Autoseed" target="_blank">Autoseed</a>自动完成的截图，不喜勿看。</span></li>
        </ul>
        <img src="{img_url}" style="max-width: 100%">
    </fieldset>
    """.format(img_url=url)
    return str_screenshot


def descr_clone_info(before_torrent_id, str_clone_info="") -> str:
    if descr_clone_info_status:
        str_clone_info = """
    <div class="byrbt_info_clone autoseed" data-clone="{torrent_id}" data-version="Rhilip_Autoseed" style="display:none">
        <a href="http://github.com/Rhilip/Byrbt-Autoseed" target="_blank">Powered by Rhilip's Autoseed</a>
    </div>
    """.format(torrent_id=before_torrent_id)
    return str_clone_info


def descr_media_info(info: str, str_media_info="") -> str:
    if descr_media_info_status:
        str_media_info = """
    <fieldset class="autoseed">
        <legend><b>MediaInfo:（自动生成，仅供参考）</b></legend>
        <div id="mediainfo">{info}</div>
    </fieldset>
    """.format(info=info)
    return str_media_info


# -*- End of Extended description Setting -*-


# Other Function
def pre_delete_judge(status: str, time_now: int, time_added: int, ratio: int, judge: bool = False) -> bool:
    """
    根据传入的种子信息判定是否能够删除种子,
    预设判断流程: 发布种子无上传速度 -> 达到最小做种时间 -> 达到(最大做种时间 或者 最大分享率)
    
    :param ratio: 传入种子上传比率
    :param status: 传入种子的状态
    :param time_now: 当前时间(传入) int(time.time())
    :param time_added: 传入种子添加时间
    :param judge: 判定flag
    :return: 符合判定条件 -> True
    """
    # 判定条件
    if status == "seeding":
        torrent_live_time = int(time_now - time_added)
        if torrent_live_time >= torrent_minSeedTime and \
                (ratio >= torrent_maxUploadRatio or torrent_live_time >= torrent_maxSeedTime):
            judge = True  # 符合判定，设置返回值为真

    return judge
