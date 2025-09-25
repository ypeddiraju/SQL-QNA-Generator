-- Sample MySQL database schema for testing the QNA Generator
-- This creates a simple e-commerce database with relationships

-- Create tables
CREATE TABLE customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(200) NOT NULL,
    category_id INT,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Insert sample data
INSERT INTO customers (first_name, last_name, email, phone) VALUES
('John', 'Smith', 'john.smith@email.com', '555-0101'),
('Jane', 'Johnson', 'jane.johnson@email.com', '555-0102'),
('Mike', 'Brown', 'mike.brown@email.com', '555-0103'),
('Sarah', 'Davis', 'sarah.davis@email.com', '555-0104'),
('Tom', 'Wilson', 'tom.wilson@email.com', '555-0105');

INSERT INTO categories (category_name, description) VALUES
('Electronics', 'Electronic devices and gadgets'),
('Clothing', 'Apparel and fashion items'),
('Books', 'Books and educational materials'),
('Home & Garden', 'Home improvement and garden supplies');

INSERT INTO products (product_name, category_id, price, stock_quantity) VALUES
('Laptop Computer', 1, 999.99, 25),
('Smartphone', 1, 699.99, 50),
('T-Shirt', 2, 19.99, 100),
('Jeans', 2, 59.99, 75),
('Programming Book', 3, 39.99, 30),
('Garden Hose', 4, 29.99, 40),
('LED Monitor', 1, 299.99, 20),
('Winter Jacket', 2, 89.99, 60);

INSERT INTO orders (customer_id, total_amount, status) VALUES
(1, 1299.98, 'completed'),
(2, 59.99, 'completed'),
(3, 329.98, 'pending'),
(4, 109.98, 'completed'),
(5, 999.99, 'shipped');

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 999.99),
(1, 7, 1, 299.99),
(2, 4, 1, 59.99),
(3, 3, 2, 19.99),
(3, 6, 1, 29.99),
(4, 5, 1, 39.99),
(4, 8, 1, 89.99),
(5, 1, 1, 999.99);
