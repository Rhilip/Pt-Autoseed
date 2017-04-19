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

# Byrbt
byr_cookies = ""

# Reseed_Torrent_Setting
torrent_maxUploadRatio = 3
torrent_minSeedTime = 86400
torrent_maxSeedTime = 691200

# Show_Site
web_url = "http://"  # demo网站的url
web_loc = "/var/www"  # demo网站在服务器上的地址
web_show_entries_number = 10  # 展示页面显示的做种条目数量

# Search_pattern
series_pattern = u"(?:^[\u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ff:：]+[. ]?|^)"  # 移除平假名、片假名、中文
"(?P<full_name>(?P<search_name>[\w\-. ]+?)[. ]"
"(?P<tv_season>(?:(?:[Ss]\d+)?[Ee][Pp]?\d+(?:-[Ee]?[Pp]?\d+)?)|(?:[Ss]\d+)).+?(?:-(?P<group>.+?))?)"
"(?:\.(?P<tv_filetype>\w+)$|$)"


# Function
def pre_delete_judge(status: str, time_now: int, time_added: int, ratio: int, judge: bool = False) -> bool:
    """
    note: 根据传入的种子信息判定是否能够删除种子,预设判断流程: 发布种子无上传速度 -> 达到最小做种时间 -> 达到(最大做种时间 或者 最大分享率)
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
