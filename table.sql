-- phpMyAdmin SQL Dump
-- version 4.4.15.6
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: 2017-05-26 15:31:41
-- 服务器版本： 5.5.48-log
-- PHP Version: 7.0.7

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

--
-- Database: `autoseed`
--

-- --------------------------------------------------------

--
-- 表的结构 `info_list`
--

CREATE TABLE IF NOT EXISTS `info_list` (
  `sort_id`           int(11) NOT NULL,
  `search_name`       text NOT NULL COMMENT '搜索名称',
  `tracker.byr.cn`    int(11) DEFAULT NULL COMMENT 'byr克隆种子号',
  `npupt.com`         INT(11) DEFAULT NULL
  COMMENT 'npubits克隆种子号',
  `pt.nwsuaf6.edu.cn` INT(11) DEFAULT NULL
  COMMENT 'nwsuaf6克隆种子号'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- 表的结构 `seed_list`
--

CREATE TABLE IF NOT EXISTS `seed_list` (
  `id`                int(11) NOT NULL,
  `title`             text    NOT NULL,
  `download_id`       int(11) NOT NULL,
  `tracker.byr.cn`    int(11) NOT NULL,
  `npupt.com`         INT(11) NOT NULL,
  `pt.nwsuaf6.edu.cn` INT(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `info_list`
--
ALTER TABLE `info_list`
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
-- AUTO_INCREMENT for table `info_list`
--
ALTER TABLE `info_list`
  MODIFY `sort_id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `seed_list`
--
ALTER TABLE `seed_list`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;