CREATE TABLE IF NOT EXISTS `warns` (
  `id` int(11) NOT NULL,
  `user_id` varchar(20) NOT NULL,
  `server_id` varchar(20) NOT NULL,
  `moderator_id` varchar(20) NOT NULL,
  `reason` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `maple_mob` (
  `id` int(11) NOT NULL PRIMARY KEY,
  `name` varchar(20) NOT NULL,
  `mobType` varchar(2),
  `level` int(11),
  `isBoss` boolean,
  `isBodyAttack` boolean,
  `maxHP` int(11),
  `speed` int(11),
  `physicalDamage` int(11),
  `magicDamage` int(11),
  `accuracy` int(11),
  `evasion` int(11),
  `exp` int(11),
  `isAutoAggro` boolean
);

CREATE TABLE IF NOT EXISTS `maple_mob_map` (
  `mob_id` int(11) NOT NULL,
  `map_id` varchar(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS `maple_map` (
  `id` int(11) NOT NULL PRIMARY KEY,
  `name` varchar(20) NOT NULL,
  `streetName` varchar(20)
);

CREATE TABLE IF NOT EXISTS `maple_character` (
  `discord_name` varchar(20) NOT NULL,
  `ign` varchar(12) NOT NULL PRIMARY KEY,
  `class_idx` int(11) NOT NULL,
  `level` int(11) DEFAULT 0,
  `attack` int(11) DEFAULT 0,
  `attack_p` int(11) DEFAULT 0,
  `dmg_p` int(11) DEFAULT 0,
  `boss_p` int(11) DEFAULT 0,
  `strike_p` real DEFAULT 0,
  `ignore_p` real DEFAULT 0,
  `finaldmg_p` int(11) DEFAULT 0,
  `str_clear` int(11) DEFAULT 0,
  `str_p` int(11) DEFAULT 0,
  `str_unique` int(11) DEFAULT 0,
  `dex_clear` int(11) DEFAULT 0,
  `dex_p` int(11) DEFAULT 0,
  `dex_unique` int(11) DEFAULT 0,
  `int_clear` int(11) DEFAULT 0,
  `int_p` int(11) DEFAULT 0,
  `int_unique` int(11) DEFAULT 0,
  `luk_clear` int(11) DEFAULT 0,
  `luk_p` int(11) DEFAULT 0,
  `luk_unique` int(11) DEFAULT 0
);