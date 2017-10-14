-- phpMyAdmin SQL Dump
-- version 4.7.4
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: 2017-10-09 12:25:13
-- 服务器版本： 5.6.37-log
-- PHP Version: 7.0.7

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

CREATE TABLE IF NOT EXISTS `info_list` (
  `sort_id`               INT(11) NOT NULL AUTO_INCREMENT,
  `search_name`           TEXT    NOT NULL
  COMMENT '搜索名称',
  `tracker.byr.cn`        INT(11)          DEFAULT NULL
  COMMENT 'byr克隆种子号',
  `npupt.com`             INT(11)          DEFAULT NULL
  COMMENT 'npubits克隆种子号',
  `pt.nwsuaf6.edu.cn`     INT(11)          DEFAULT NULL
  COMMENT 'nwsuaf6克隆种子号',
  `pttracker6.tju.edu.cn` INT(11)          DEFAULT NULL
  COMMENT 'tju克隆种子号',
  PRIMARY KEY (`sort_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- 表的结构 `seed_list`
--

CREATE TABLE IF NOT EXISTS `seed_list` (
  `id`                    INT(11) NOT NULL AUTO_INCREMENT,
  `title`                 TEXT    NOT NULL,
  `download_id`           INT(11) NOT NULL,
  `tracker.byr.cn`        INT(11) NOT NULL DEFAULT '0',
  `npupt.com`             INT(11) NOT NULL DEFAULT '0',
  `pt.nwsuaf6.edu.cn`     INT(11) NOT NULL DEFAULT '0',
  `pttracker6.tju.edu.cn` INT(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `download_id` (`download_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
COMMIT;