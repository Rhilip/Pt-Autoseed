-- MySQL dump 10.13  Distrib 5.5.54, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: autoseed
-- ------------------------------------------------------
-- Server version	5.5.54-0ubuntu0.14.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `autoseed`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `autoseed` /*!40100 DEFAULT CHARACTER SET latin1 */;

USE `autoseed`;

--
-- Table structure for table `seed_list`
--

DROP TABLE IF EXISTS `seed_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `seed_list` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` text NOT NULL,
  `download_id` int(11) NOT NULL,
  `seed_id` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tv_info`
--

DROP TABLE IF EXISTS `tv_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tv_info` (
  `sort_id` int(11) NOT NULL AUTO_INCREMENT,
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
  `uplver` text NOT NULL COMMENT '匿名发布',
  PRIMARY KEY (`sort_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-03-27 12:26:21
