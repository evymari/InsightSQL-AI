-- ============================================================
-- Verificación de datos importados del dataset Olist
-- ============================================================

SELECT 'customers'      AS tabla, COUNT(*) AS total FROM customers
UNION ALL
SELECT 'sellers',               COUNT(*) FROM sellers
UNION ALL
SELECT 'products',              COUNT(*) FROM products
UNION ALL
SELECT 'orders',                COUNT(*) FROM orders
UNION ALL
SELECT 'order_items',           COUNT(*) FROM order_items
UNION ALL
SELECT 'order_payments',        COUNT(*) FROM order_payments
UNION ALL
SELECT 'order_reviews',         COUNT(*) FROM order_reviews
ORDER BY tabla;

-- ============================================================
-- Verificación de fechas de pedidos
-- ============================================================

SELECT 
    MIN(order_purchase_timestamp) AS primera_compra,
    MAX(order_purchase_timestamp) AS ultima_compra,
    COUNT(DISTINCT DATE_TRUNC('year', order_purchase_timestamp)) AS años_con_datos
FROM orders;

-- ============================================================
-- Verificación de integridad de FKs
-- ============================================================

SELECT 
    'orders_sin_customer' AS verificacion,
    COUNT(*) AS total
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL

UNION ALL

SELECT 
    'order_items_sin_order',
    COUNT(*)
FROM order_items oi
LEFT JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_id IS NULL

UNION ALL

SELECT 
    'order_items_sin_product',
    COUNT(*)
FROM order_items oi
LEFT JOIN products p ON oi.product_id = p.product_id
WHERE p.product_id IS NULL

UNION ALL

SELECT 
    'order_items_sin_seller',
    COUNT(*)
FROM order_items oi
LEFT JOIN sellers s ON oi.seller_id = s.seller_id
WHERE s.seller_id IS NULL;
