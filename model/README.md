# model
这里列出来一些附加模块

## mediainfo.py
* 模块类型：必须模块
* 作用：查询mkv、mp4文件的mediainfo信息，并返回html格式的字符串信息
* 依赖：pymediainfo`pip install pymediainfo`

## Magnet_To_Torrent2.py
* 模块类型：独立模块
* 作用：通过magnet链接生成对应的torrent种子。
* 依赖：libtorrent`apt-get install python-libtorrent`

## rss_ZhuixinFan.py
* 模块类型：独立模块
* 作用：自动从ZhuixinFan读取最新剧集的magnet链接，并使用Magnet_To_Torrent2.py提供的生成函数生成对应种子
* 依赖：Magnet_To_Torrent2.py