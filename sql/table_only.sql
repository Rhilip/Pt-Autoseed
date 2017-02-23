-- --------------------------------------------------------

--
-- 表的结构 `seed_list`
--

CREATE TABLE IF NOT EXISTS `seed_list` (
  `id` int(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
  `title` text NOT NULL,
  `download_id` int(11) NOT NULL,
  `seed_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- 表的结构 `tv_info`
--

CREATE TABLE IF NOT EXISTS `tv_info` (
  `sort_id` int(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
  `type` smallint(6) NOT NULL COMMENT '一级分类',
  `second_type` tinyint(4) NOT NULL COMMENT '二级分类',
  `file` text NOT NULL COMMENT '种子文件',
  `tv_type` text NOT NULL COMMENT '剧集类型',
  `cname` text NOT NULL COMMENT '中文名',
  `tv_ename` text NOT NULL COMMENT '英文名(主)',
  `tv_season` text NOT NULL COMMENT '剧集季度信息',
  `tv_filetype` text NOT NULL COMMENT '剧集文件格式',
  `type_2` smallint(6) NOT NULL COMMENT '(值同type)',
  `small_descr` text NOT NULL COMMENT '副标题',
  `url` text NOT NULL COMMENT 'IMDb链接',
  `dburl` text NOT NULL COMMENT '豆瓣链接',
  `nfo` text NOT NULL COMMENT 'NFO文件',
  `descr` text NOT NULL COMMENT '简介',
  `uplver` text NOT NULL COMMENT '匿名发布'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------