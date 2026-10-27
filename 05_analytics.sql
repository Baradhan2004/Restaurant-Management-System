-- name: top_items_per_category
SELECT * FROM (
  SELECT c.name AS category, m.name AS item, SUM(oi.quantity) AS units,
         ROUND(SUM(oi.quantity*oi.unit_price),2) AS revenue,
         RANK() OVER (PARTITION BY c.name ORDER BY SUM(oi.quantity*oi.unit_price) DESC) AS rnk
    FROM order_items oi
    JOIN menu_items m ON m.item_id = oi.item_id
    JOIN menu_categories c ON c.category_id = m.category_id
   GROUP BY c.name, m.name)
 WHERE rnk <= 3 ORDER BY category, rnk;

-- name: rolling_7day_revenue
SELECT day, revenue,
       ROUND(AVG(revenue) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW),2) AS ma7
  FROM v_daily_revenue ORDER BY day DESC LIMIT 5;

-- name: peak_hours
SELECT CAST(strftime('%H', opened_at) AS INTEGER) AS hour, COUNT(*) AS orders
  FROM orders GROUP BY hour ORDER BY orders DESC LIMIT 5;

-- name: customer_rfm
SELECT customer_id, recency_days, frequency, monetary,
       NTILE(4) OVER (ORDER BY recency_days DESC) AS r,
       NTILE(4) OVER (ORDER BY frequency)         AS f,
       NTILE(4) OVER (ORDER BY monetary)          AS m
  FROM (SELECT o.customer_id,
               CAST(julianday((SELECT MAX(paid_at) FROM payments)) - julianday(MAX(p.paid_at)) AS INTEGER) AS recency_days,
               COUNT(*) AS frequency, ROUND(SUM(p.amount),2) AS monetary
          FROM orders o JOIN payments p ON p.order_id = o.order_id
         WHERE o.customer_id IS NOT NULL GROUP BY o.customer_id)
 ORDER BY monetary DESC LIMIT 5;

-- name: staff_sales_leaderboard
SELECT s.full_name, s.role, COUNT(DISTINCT o.order_id) AS orders, ROUND(SUM(p.amount),2) AS sales,
       ROUND(SUM(p.tip),2) AS tips
  FROM staff s JOIN orders o ON o.staff_id = s.staff_id JOIN payments p ON p.order_id = o.order_id
 WHERE s.role = 'waiter' GROUP BY s.staff_id ORDER BY sales DESC LIMIT 5;
