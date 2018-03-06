-- phpMyAdmin SQL Dump
-- version 4.7.7
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: 2018-03-06 18:57:24
-- 服务器版本： 5.6.39-log
-- PHP Version: 7.0.21

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

--
-- Database: `autoseed`
--

-- --------------------------------------------------------

--
-- 表的结构 `info_list`
--

CREATE TABLE `info_list` (
  `sort_id`              INT(11) NOT NULL,
  `search_name`          TEXT    NOT NULL
  COMMENT '搜索名称',
  `tracker.byr.cn`       INT(11) DEFAULT NULL
  COMMENT 'byr克隆种子号',
  `npupt.com`            INT(11) DEFAULT NULL
  COMMENT 'npubits克隆种子号',
  `pt.nwsuaf6.edu.cn`    INT(11) DEFAULT NULL
  COMMENT 'nwsuaf6克隆种子号',
  `pttracker6.tjupt.org` INT(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- 表的结构 `seed_list`
--

CREATE TABLE `seed_list` (
  `id`                   INT(11) NOT NULL,
  `title`                TEXT    NOT NULL,
  `download_id`          INT(11)          DEFAULT '0',
  `tracker.byr.cn`       INT(11) NOT NULL DEFAULT '0',
  `npupt.com`            INT(11) NOT NULL DEFAULT '0',
  `pt.nwsuaf6.edu.cn`    INT(11)          DEFAULT '0',
  `pttracker6.tjupt.org` INT(11) NOT NULL DEFAULT '0'
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
-- 在导出的表使用AUTO_INCREMENT
--

--
-- 使用表AUTO_INCREMENT `info_list`
--
ALTER TABLE `info_list`
  MODIFY `sort_id` INT(11) NOT NULL AUTO_INCREMENT;

--
-- 使用表AUTO_INCREMENT `seed_list`
--
ALTER TABLE `seed_list`
  MODIFY `id` INT(11) NOT NULL AUTO_INCREMENT;
COMMIT;
