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
        "\.?(?P<full_name>(?P<search_name>[\w\-. ]+?)[. ]"
        "(?P<episode>(?:(?:[Ss]\d+)?[Ee][Pp]?\d+(?:-[Ee]?[Pp]?\d+)?)|(?:[Ss]\d+)).+?(?:-(?P<group>.+?))?)"
        "(?:\.(?P<filetype>\w+)$|$)"
    ),
    re.compile(  # Anime - One_piece(Skytree)
        "(?P<full_name>\[(?P<group>Skytree)\]\[海贼王\]\[(?P<search_name>One_Piece)\]"
        "\[(?P<episode>789)\]\[GB_JP\]\[X264_AAC\]\[720P\]\[CRRIP\]\[天空树双语字幕组\])"
        "(?:\.(?P<filetype>mp4)$|$)"
    ),
    re.compile(  # Anime (Normal)
        "(?P<full_name>\[(?P<group>.+?)\]\[?(?P<search_name>.+?)\]?\[(?P<episode>\d+(?:\.?\(?\d+\)?)?)\].+)"
        "(?:\.(?P<filetype>\w+)$|$)"
    )
]
