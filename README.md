[![dUb6BEB.md.jpg](https://iili.io/dUb6BEB.md.jpg)](https://freeimage.host/i/dUb6BEB)
# GabutEngine
This is A simple search engine using Flask and Automation to crawl from google please install before start using.

```bash
pip install bs4 flask
```

## Simple template
Using tailwind for setup appearance

## To start
I am using Mariadb for database, you should install mariadb with
```bash
pip install mariadb
```
and make the database. in database have 4 content , title , url , description, content

###Query for database
```bash
CREATE DATABASE Gabut;

USE Gabut;

CREATE TABLE `websites` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) DEFAULT NULL,
  `url` varchar(255) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `content` longtext DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=69 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```
