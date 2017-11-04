# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>
# Licensed under the GNU General Public License v3.0

import re

"""
This package includes a list about search patterns which the Autoseed only accept torrent's name match with.

NOTICE: 
1.Every pattern should includes at least below groups, even it's empty.
  groups list:  `full_name` `search_name` `episode` `group` `filetype`
2.Every pattern should use re.compile() to compile a regular expression pattern into a regular expression object.
"""

# Search_pattern
pattern_group = [
    re.compile(  # Series (Which name match with 0day Source,see https://scenerules.org/t.html?id=tvx2642k16.nfo 16.4)
        "\.?(?P<full_name>(?P<search_name>[\w\-. ]+?)[. ]"
        "(?P<episode>([Ss]\d+)?[Ee][Pp]?\d+(-[Ee]?[Pp]?\d+)?|[Ss]\d+|Complete).+?(-(?P<group>.+?))?)"
        "(\.(?P<filetype>\w+)$|$)"
    ),
    re.compile(  # Anime - One_piece(Skytree)
        "(?P<full_name>\[(?P<group>Skytree)\]\[海贼王\]\[(?P<search_name>One_Piece)\]"
        "\[(?P<episode>\d+)\]\[GB_JP\]\[X264_AAC\]\[720P\]\[CRRIP\]\[天空树双语字幕组\])"
        "(\.(?P<filetype>mp4)$|$)"
    ),
    re.compile(  # Anime - Group: 八重樱字幕组
        "(?P<full_name>\[(?P<group>八重[樱櫻]字幕[组組])\]\[.+?\]\[(?P<search_name>[^\[\]]+?)\]"
        "\[?(?P<episode>\d+(\.?\d+|-\d+|[ _]?[Vv]2)?)\]?.+?)"
        "(\.(?P<filetype>\w+)$|$)"
    ),
    # re.compile(  # Anime - Foreign Group
    #     "(?P<full_name>\[(?P<group>[^\[\]]+?)\] (?P<search_name>.+?) - (?P<episode>\d+(\.?\d+|-\d+|[ _]?[Vv]2)?) \[\d+?[Pp]\])"
    #     "(\.(?P<filetype>\w+)$|$)"
    # ),
    re.compile(  # Anime - Normal Pattern
        "(?P<full_name>\[(?P<group>[^\[\]]+?)\](?P<n_s>\[)?(?P<search_name>[^\[\]]+?)(?(n_s)\])"
        "\[?(?P<episode>\d+(\.?\d+|-\d+|[ _]?[Vv]2)?)\]?.+?)"
        "(\.(?P<filetype>\w+)$|$)"
    )
]

if __name__ == '__main__':
    import requests

    test_txt_url = "https://gist.github.com/Rhilip/34ad82070d71bb3fa75f293d24101588/raw/9%2520-%2520RegExp%2520Test%2520set.txt"
    r = requests.get(test_txt_url)
    test_list = r.text.split("\n")
    for test_item in test_list:
        print("Test item: {}".format(test_item))
        for ptn in pattern_group:
            search = re.search(ptn, test_item)
            if search:
                print(search.groupdict())
                break
        print()
