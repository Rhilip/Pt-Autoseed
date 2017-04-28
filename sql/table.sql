-- phpMyAdmin SQL Dump
-- version 4.4.15.6
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: 2017-04-28 22:35:38
-- 服务器版本： 5.5.48-log
-- PHP Version: 7.0.7

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `autoseed`
--

-- --------------------------------------------------------

--
-- 表的结构 `info_anime`
--

CREATE TABLE IF NOT EXISTS `info_anime` (
  `sort_id` int(11) NOT NULL,
  `type` smallint(6) NOT NULL COMMENT '一级分类',
  `second_type` tinyint(4) NOT NULL COMMENT '二级分类',
  `comic_type` text NOT NULL COMMENT '动漫类别',
  `subteam` text NOT NULL COMMENT '字幕/压制/作者/EAC',
  `comic_cname` text NOT NULL COMMENT '中文名',
  `comic_ename` text NOT NULL COMMENT '英文名',
  `comic_episode` text NOT NULL COMMENT '集数/卷数/张数 (自动更改)',
  `comic_quality` text NOT NULL COMMENT '分辨率/码率/扫图者',
  `comic_source` text NOT NULL COMMENT '片源/出版社',
  `comic_filetype` text NOT NULL COMMENT '动漫文件格式',
  `comic_year` text NOT NULL COMMENT '发行时间',
  `comic_country` text NOT NULL COMMENT '动漫国别',
  `small_descr` text NOT NULL COMMENT '副标题',
  `url` text NOT NULL COMMENT 'IMDb链接',
  `dburl` text NOT NULL COMMENT '豆瓣链接',
  `descr` text NOT NULL COMMENT '简介',
  `uplver` text NOT NULL COMMENT '匿名发布(yes or no)',
  `before_torrent_id` int(11) NOT NULL COMMENT '克隆种子号，可空'
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;

--
-- 转存表中的数据 `info_anime`
--

INSERT INTO `info_anime` (`sort_id`, `type`, `second_type`, `comic_type`, `subteam`, `comic_cname`, `comic_ename`, `comic_episode`, `comic_quality`, `comic_source`, `comic_filetype`, `comic_year`, `comic_country`, `small_descr`, `url`, `dburl`, `descr`, `uplver`, `before_torrent_id`) VALUES
  (1, 404, 19, '连载|长篇|TV', '字幕组', '自动发种', 'default', '01', '720p|1080p', 'TVRip', 'MKV|MP4', '2017.04', '日漫|美漫|国产', '自动发种 简介待修改', '', '', '', 'yes', 1);

-- --------------------------------------------------------

--
-- 表的结构 `info_series`
--

CREATE TABLE IF NOT EXISTS `info_series` (
  `sort_id` int(11) NOT NULL,
  `type` smallint(6) NOT NULL COMMENT '一级分类',
  `second_type` tinyint(4) NOT NULL COMMENT '二级分类',
  `tv_type` text NOT NULL COMMENT '剧集类型',
  `cname` text NOT NULL COMMENT '中文名',
  `tv_ename` text NOT NULL COMMENT '英文名(主)',
  `tv_season` text NOT NULL COMMENT '剧集季度信息',
  `tv_filetype` text NOT NULL COMMENT '剧集文件格式',
  `small_descr` text NOT NULL COMMENT '副标题',
  `url` text NOT NULL COMMENT 'IMDb链接',
  `dburl` text NOT NULL COMMENT '豆瓣链接',
  `descr` text NOT NULL COMMENT '简介',
  `uplver` text NOT NULL COMMENT '匿名发布',
  `before_torrent_id` int(11) DEFAULT NULL COMMENT '克隆种子号，可空'
) ENGINE=InnoDB AUTO_INCREMENT=102 DEFAULT CHARSET=utf8mb4;

--
-- 转存表中的数据 `info_series`
--

INSERT INTO `info_series` (`sort_id`, `type`, `second_type`, `tv_type`, `cname`, `tv_ename`, `tv_season`, `tv_filetype`, `small_descr`, `url`, `dburl`, `descr`, `uplver`, `before_torrent_id`) VALUES
  (1, 401, 17, '欧美', '自动发种', 'default', 'S01', 'MKV', '自动发种 简介待修改', '', '', '', 'yes', NULL);
-- --------------------------------------------------------

--
-- 表的结构 `seed_list`
--

CREATE TABLE IF NOT EXISTS `seed_list` (
  `id` int(11) NOT NULL,
  `title` text NOT NULL,
  `download_id` int(11) NOT NULL,
  `tracker.byr.cn` int(11) NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4;

--
-- 转存表中的数据 `seed_list`
--

INSERT INTO `seed_list` (`id`, `title`, `download_id`, `tracker.byr.cn`) VALUES
  (5, 'APB.S01E12.720p.HDTV.x264-AVS.mkv', 1, 2);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `info_anime`
--
ALTER TABLE `info_anime`
  ADD PRIMARY KEY (`sort_id`);

--
-- Indexes for table `info_series`
--
ALTER TABLE `info_series`
  ADD PRIMARY KEY (`sort_id`);

--
-- Indexes for table `seed_list`
--
ALTER TABLE `seed_list`
  ADD PRIMARY KEY (`id`),
  ADD KEY `download_id` (`download_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `info_anime`
--
ALTER TABLE `info_anime`
  MODIFY `sort_id` int(11) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=2;
--
-- AUTO_INCREMENT for table `info_series`
--
ALTER TABLE `info_series`
  MODIFY `sort_id` int(11) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=102;
--
-- AUTO_INCREMENT for table `seed_list`
--
ALTER TABLE `seed_list`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=6;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
