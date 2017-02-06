-- phpMyAdmin SQL Dump
-- version 4.4.15.6
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: 2017-02-06 16:03:03
-- 服务器版本： 5.5.48-log
-- PHP Version: 5.4.45

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `test`
--

-- --------------------------------------------------------

--
-- 表的结构 `seed_list`
--

CREATE TABLE IF NOT EXISTS `seed_list` (
  `id` int(11) NOT NULL,
  `title` text NOT NULL,
  `download_id` int(11) NOT NULL,
  `seed_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- 表的结构 `tv_info`
--

CREATE TABLE IF NOT EXISTS `tv_info` (
  `sort_id` int(11) NOT NULL,
  `type` smallint(6) NOT NULL COMMENT '一级分类',
  `second_type` tinyint(4) NOT NULL COMMENT '二级分类',
  `file` text NOT NULL COMMENT '种子文件',
  `tv_type` text NOT NULL COMMENT '剧集类型',
  `cname` text NOT NULL COMMENT '中文名',
  `tv_ename` text NOT NULL COMMENT '英文名(主)',
  `tv_season` text NOT NULL COMMENT '剧集季度信息',
  `tv_filetype` text NOT NULL COMMENT '剧集文件格式',
  `type_2` smallint(6) NOT NULL COMMENT '(不知道怎么用，值同type)',
  `small_descr` text NOT NULL COMMENT '副标题',
  `url` text NOT NULL COMMENT 'IMDb链接',
  `dburl` text NOT NULL COMMENT '豆瓣链接',
  `nfo` text NOT NULL COMMENT 'NFO文件',
  `descr` text NOT NULL COMMENT '简介',
  `uplver` text NOT NULL COMMENT '匿名发布'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `seed_list`
--
ALTER TABLE `seed_list`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `tv_info`
--
ALTER TABLE `tv_info`
  ADD PRIMARY KEY (`sort_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `seed_list`
--
ALTER TABLE `seed_list`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `tv_info`
--
ALTER TABLE `tv_info`
  MODIFY `sort_id` int(11) NOT NULL AUTO_INCREMENT;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
