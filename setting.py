# Autoseed
sleep_busy_time = 120
sleep_free_time = 600

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
web_url = ""
web_loc = ""


# Function
def pre_delete_judge(status: str, time_now: int, time_added: int, ratio: int, judge: bool = False) -> bool:
    """
    note: 根据传入的种子信息判定是否能够删除种子,预设判断流程: 发布种子无上传速度 -> 达到最小做种时间 -> 达到(最大做种时间 或者 最大分享率)
    :param ratio: 种子上传比率
    :param status: 种子的状态
    :param time_now: 当前时间
    :param time_added: 种子添加时间
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
