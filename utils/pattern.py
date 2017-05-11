import re

# Search_pattern
pattern_group = [
    re.compile(  # Series
        u"(?:^[\u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ff:：]+[. ]?|^)"  # 移除平假名、片假名、中文
        "(?P<full_name>(?P<search_name>[\w\-. ]+?)[. ]"
        "(?P<episode>(?:(?:[Ss]\d+)?[Ee][Pp]?\d+(?:-[Ee]?[Pp]?\d+)?)|(?:[Ss]\d+)).+?(?:-(?P<group>.+?))?)"
        "(?:\.(?P<filetype>\w+)$|$)"
    ),
    re.compile(  # Anime
        "(?P<full_name>\[(?P<group>.+?)\]\[?(?P<search_name>.+?)\]?\[(?P<episode>\d+)\].+)"
        "(?:\.(?P<filetype>mp4|mkv))?"
    )
]
