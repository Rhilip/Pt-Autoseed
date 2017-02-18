# model
这里列出来一些附加模块

## mediainfo
* 模块类型：必须模块
* 作用：查询mkv、mp4文件的mediainfo信息，并返回html格式的字符串信息
* 依赖：pymediainfo`pip install pymediainfo`

## Magnet_To_Torrent(from [danfolkes/Magnet2Torrent](https://github.com/danfolkes/Magnet2Torrent))
* 模块类型：独立模块
* 作用：通过magnet链接生成对应的torrent种子。
* 依赖：libtorrent`apt-get install python3-libtorrent`

## rss_ZhuixinFan
* 模块类型：独立模块
* 作用：自动从 [追新番日剧站](http://www.zhuixinfan.com/) 读取最新剧集的magnet链接，并使用Magnet_To_Torrent提供的生成函数生成对应种子
* 依赖：model.Magnet_To_Torrent