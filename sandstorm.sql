-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Nov 13, 2024 at 07:18 PM
-- Server version: 10.6.19-MariaDB-cll-lve
-- PHP Version: 8.1.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `rrgaming_sandstorm`
--

-- --------------------------------------------------------

--
-- Table structure for table `assist_log`
--

CREATE TABLE `assist_log` (
  `id` int(11) NOT NULL,
  `steam_id` bigint(20) NOT NULL,
  `timestamp` datetime NOT NULL,
  `second_assistor_steam_id` bigint(20) DEFAULT NULL,
  `victim_steam_id` bigint(20) NOT NULL,
  `victim_name` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Table structure for table `capture_log`
--

CREATE TABLE `capture_log` (
  `id` int(11) NOT NULL,
  `steam_id` bigint(20) NOT NULL,
  `timestamp` datetime NOT NULL,
  `captured_team` int(11) NOT NULL,
  `previous_team` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Table structure for table `destroyed_log`
--

CREATE TABLE `destroyed_log` (
  `id` int(11) NOT NULL,
  `steam_id` bigint(20) NOT NULL,
  `timestamp` datetime NOT NULL,
  `destroyed_team` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Table structure for table `kill_log`
--

CREATE TABLE `kill_log` (
  `id` int(11) NOT NULL,
  `steam_id` bigint(20) NOT NULL,
  `timestamp` datetime NOT NULL,
  `victim_steam_id` bigint(20) NOT NULL,
  `victim_name` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Table structure for table `login_log`
--

CREATE TABLE `login_log` (
  `id` int(11) NOT NULL,
  `steam_id` bigint(20) NOT NULL,
  `timestamp` datetime NOT NULL,
  `player_name` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Table structure for table `logout_log`
--

CREATE TABLE `logout_log` (
  `id` int(11) NOT NULL,
  `steam_id` bigint(20) NOT NULL,
  `timestamp` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Table structure for table `onlineplayers`
--

CREATE TABLE `onlineplayers` (
  `steamid` varchar(50) NOT NULL,
  `online` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `first_connection` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `players`
--

CREATE TABLE `players` (
  `id` int(11) NOT NULL,
  `steam_id` bigint(20) NOT NULL,
  `player_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `elo` int(11) DEFAULT 1000,
  `elo2` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Table structure for table `round_result_log`
--

CREATE TABLE `round_result_log` (
  `id` int(11) NOT NULL,
  `steam_id` bigint(20) NOT NULL,
  `timestamp` datetime NOT NULL,
  `winner_team` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Table structure for table `team_join_log`
--

CREATE TABLE `team_join_log` (
  `id` int(11) NOT NULL,
  `steam_id` bigint(20) NOT NULL,
  `timestamp` datetime NOT NULL,
  `team` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `assist_log`
--
ALTER TABLE `assist_log`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_event` (`steam_id`,`timestamp`);

--
-- Indexes for table `capture_log`
--
ALTER TABLE `capture_log`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_event` (`steam_id`,`timestamp`);

--
-- Indexes for table `destroyed_log`
--
ALTER TABLE `destroyed_log`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_event` (`steam_id`,`timestamp`);

--
-- Indexes for table `kill_log`
--
ALTER TABLE `kill_log`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_event` (`steam_id`,`timestamp`);

--
-- Indexes for table `login_log`
--
ALTER TABLE `login_log`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_event` (`steam_id`,`timestamp`);

--
-- Indexes for table `logout_log`
--
ALTER TABLE `logout_log`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_event` (`steam_id`,`timestamp`);

--
-- Indexes for table `onlineplayers`
--
ALTER TABLE `onlineplayers`
  ADD PRIMARY KEY (`steamid`);

--
-- Indexes for table `players`
--
ALTER TABLE `players`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_steam_id` (`steam_id`);

--
-- Indexes for table `round_result_log`
--
ALTER TABLE `round_result_log`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_event` (`steam_id`,`timestamp`);

--
-- Indexes for table `team_join_log`
--
ALTER TABLE `team_join_log`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_event` (`steam_id`,`timestamp`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `assist_log`
--
ALTER TABLE `assist_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `capture_log`
--
ALTER TABLE `capture_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `destroyed_log`
--
ALTER TABLE `destroyed_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `kill_log`
--
ALTER TABLE `kill_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `login_log`
--
ALTER TABLE `login_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `logout_log`
--
ALTER TABLE `logout_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `players`
--
ALTER TABLE `players`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `round_result_log`
--
ALTER TABLE `round_result_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `team_join_log`
--
ALTER TABLE `team_join_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
