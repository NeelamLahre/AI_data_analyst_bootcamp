-- Active: 1787461488803@@127.0.0.1@3306@bootcamp_sales
USE bootcamp_sales;

SHOW TABLES;

-- 1. Explore bm_customers
SELECT *
FROM bm_customers
LIMIT 10;


-- 2. Explore bm_skus
SELECT *
FROM bm_skus
LIMIT 10;


-- 3. Explore bm_stores
SELECT *
FROM bm_stores
LIMIT 10;


-- 4. Explore bm_sales
SELECT *
FROM bm_sales
LIMIT 10;


-- 5. Explore bm_inventory
SELECT *
FROM bm_inventory
LIMIT 10;


-- 6. Explore the bm_promotions

SELECT *
FROM bm_promotions
LIMIT 10;



-- ==========================================
-- ROW COUNTS
-- ==========================================

-- 1. Customers
SELECT COUNT(*) AS row_count
FROM bm_customers;


-- 2. SKUs / Products
SELECT COUNT(*) AS row_count
FROM bm_skus;


-- 3. Stores
SELECT COUNT(*) AS row_count
FROM bm_stores;


-- 4. Sales
SELECT COUNT(*) AS row_count
FROM bm_sales;


-- 5. Inventory
SELECT COUNT(*) AS row_count
FROM bm_inventory;


-- 6. Promotions
SELECT COUNT(*) AS row_count
FROM bm_promotions;


--missing values in bm_skus
SELECT
    COUNT(*) - COUNT(sku_id) AS missing_sku_id,
    COUNT(*) - COUNT(sku_name) AS missing_sku_name,
    COUNT(*) - COUNT(category) AS missing_category,
    COUNT(*) - COUNT(unit_price) AS missing_unit_price
FROM bm_skus;






-- SELECT queries with WHERE filter


-- 1. Products in Electronics
SELECT *
FROM bootcamp_sales.bm_skus
WHERE category = 'Electronics';

-- 2. Customers in Dubai with Gold loyalty
SELECT *
FROM bootcamp_sales.bm_customers
WHERE city = 'Dubai'
  AND loyalty_segment = 'Gold';

-- 3. Store sales with quantity greater than 5
SELECT *
FROM bootcamp_sales.bm_sales
WHERE channel = 'Store'
  AND quantity > 5;


-- Queries using INNER JOIN (2 tables)

-- 4. Sales with customer details
SELECT s.date, s.store_id, s.sku_id, s.total_value, c.cust_id, c.city
FROM bootcamp_sales.bm_sales s
INNER JOIN bootcamp_sales.bm_customers c
    ON s.customer_id = c.cust_id;

-- 5. Sales with store details
SELECT s.date, s.sku_id, s.total_value, st.store_name, st.city
FROM bootcamp_sales.bm_sales s
INNER JOIN bootcamp_sales.bm_stores st
    ON s.store_id = st.store_id;

-- 6. Inventory with product details
SELECT i.store_id, i.sku_id, i.stock_on_hand, sk.sku_name, sk.unit_price
FROM bootcamp_sales.bm_inventory i
INNER JOIN bootcamp_sales.bm_skus sk
    ON i.sku_id = sk.sku_id;


-- Queries joining 3 or more tables

-- 7. Sales + customer + product
SELECT c.cust_id, c.city, sk.sku_name, s.quantity, s.total_value
FROM bootcamp_sales.bm_sales s
INNER JOIN bootcamp_sales.bm_customers c
    ON s.customer_id = c.cust_id
INNER JOIN bootcamp_sales.bm_skus sk
    ON s.sku_id = sk.sku_id;

-- 8. Inventory + store + SKU
SELECT st.store_name, st.city, sk.sku_name, i.stock_on_hand, i.reorder_point
FROM bootcamp_sales.bm_inventory i
INNER JOIN bootcamp_sales.bm_stores st
    ON i.store_id = st.store_id
INNER JOIN bootcamp_sales.bm_skus sk
    ON i.sku_id = sk.sku_id
WHERE i.stock_on_hand < i.reorder_point;

-- 9. Sales + store + customer + product
SELECT st.store_name, c.city AS customer_city, sk.sku_name, s.date, s.total_value
FROM bootcamp_sales.bm_sales s
INNER JOIN bootcamp_sales.bm_stores st
    ON s.store_id = st.store_id
INNER JOIN bootcamp_sales.bm_customers c
    ON s.customer_id = c.cust_id
INNER JOIN bootcamp_sales.bm_skus sk
    ON s.sku_id = sk.sku_id
WHERE s.channel = 'Website';


-- Queries using LEFT JOIN

-- 10. All customers with their sales count
SELECT c.cust_id, c.city, COUNT(s.customer_id) AS sales_count
FROM bootcamp_sales.bm_customers c
LEFT JOIN bootcamp_sales.bm_sales s
    ON c.cust_id = s.customer_id
GROUP BY c.cust_id, c.city;

-- 11. All stores with inventory info
SELECT st.store_id, st.store_name, i.stock_on_hand, i.sku_id
FROM bootcamp_sales.bm_stores st
LEFT JOIN bootcamp_sales.bm_inventory i
    ON st.store_id = i.store_id;

-- 12. All products with available inventory
SELECT sk.sku_id, sk.sku_name, i.stock_on_hand
FROM bootcamp_sales.bm_skus sk
LEFT JOIN bootcamp_sales.bm_inventory i
    ON sk.sku_id = i.sku_id;




-- Queries to find top records (ORDER BY + TOP)

-- 13. Top 10 most expensive products
SELECT *
FROM bootcamp_sales.bm_skus
ORDER BY unit_price DESC
LIMIT 10;

-- 14. Top 10 highest sale values
-- 14. Top 10 highest sale values

SELECT
    sku_id,
    customer_id,
    total_value,
    quantity
FROM bootcamp_sales.bm_sales
ORDER BY total_value DESC
LIMIT 10;
-- 15. Top 10 stores by revenue

SELECT
    st.store_name,
    SUM(s.total_value) AS total_revenue
FROM bootcamp_sales.bm_sales s
INNER JOIN bootcamp_sales.bm_stores st
    ON s.store_id = st.store_id
GROUP BY st.store_name
ORDER BY total_revenue DESC
LIMIT 10;




