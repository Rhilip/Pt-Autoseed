import re

"""
This package includes a list about search patterns which the Autoseed only accept torrent's name match with.

NOTICE: 
1.Every pattern should includes at least below groups,even it's empty.
  groups list:  `full_name` `search_name` `episode` `group` `filetype`
2.It's better to use re.compile() to compile a regular expression pattern into a regular expression object.
"""

# Search_pattern
pattern_group = [
    re.compile(  # Series (Which name match with 0day Source,see https://scenerules.org/t.html?id=tvx2642k16.nfo 16.4)
        u"(?:^[\u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ff:：]+[. ]?|^)"  # Remove unnecessary hiragana, katakana, Chinese
        "(?P<full_name>(?P<search_name>[\w\-. ]+?)[. ]"
        "(?P<episode>(?:(?:[Ss]\d+)?[Ee][Pp]?\d+(?:-[Ee]?[Pp]?\d+)?)|(?:[Ss]\d+)).+?(?:-(?P<group>.+?))?)"
        "(?:\.(?P<filetype>\w+)$|$)"
    ),
    re.compile(  # Anime
        "(?P<full_name>\[(?P<group>.+?)\]\[?(?P<search_name>.+?)\]?\[(?P<episode>\d+)\].+)"
        "(?:\.(?P<filetype>mp4|mkv))?"
    )
]
