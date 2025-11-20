CREATE DATABASE IF NOT EXISTS students_db;
USE students_db;

CREATE TABLE IF NOT EXISTS notification_trace (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  request_id VARCHAR(100) NOT NULL,
  balanceador VARCHAR(200),
  api_instance VARCHAR(200),
  queue_name VARCHAR(100),
  worker_name VARCHAR(100),
  notification_type ENUM('email','sms'),
  payload JSON,
  status VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS student (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  age INT NULL,
  email VARCHAR(255) NULL
);