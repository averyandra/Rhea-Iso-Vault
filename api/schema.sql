-- Create database if it does not exist
CREATE DATABASE IF NOT EXISTS rhea_iso;

-- Select the database
USE rhea_iso;

-- Create table if it does not exist
CREATE TABLE IF NOT EXISTS iso_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(512) UNIQUE NOT NULL,
    size_mb FLOAT NOT NULL,
    last_scanned DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);