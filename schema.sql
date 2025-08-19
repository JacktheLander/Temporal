CREATE DATABASE Trellis;
USE Trellis;

-- Orders table
CREATE TABLE orders (
    id            VARCHAR(255) PRIMARY KEY,
    state         VARCHAR(100) NOT NULL,
    address_json  JSON NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Payments table
CREATE TABLE payments (
    payment_id    VARCHAR(255) PRIMARY KEY,
    order_id      VARCHAR(255) NOT NULL,
    status        VARCHAR(100) NOT NULL,
    amount        FLOAT NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id)
        ON DELETE CASCADE
);

-- Events table
CREATE TABLE events (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id      VARCHAR(255) NOT NULL,
    type          VARCHAR(100) NOT NULL,
    payload_json  JSON NOT NULL,
    ts            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id)
        ON DELETE CASCADE
);