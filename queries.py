SALES_DATA_QUERY = """
SELECT
    o.id AS order_id,
    o.order_date,
    o.shipped_date,

    c.id AS customer_id,
    c.company AS customer,
    c.city,
    c.state_province,
    c.country_region AS country,

    p.id AS product_id,
    p.product_name,
    p.category,

    od.quantity,
    od.unit_price,
    od.discount,

    (
        od.quantity
        * od.unit_price
        * (1 - od.discount)
    ) AS revenue

FROM orders o

JOIN customers c
    ON o.customer_id = c.id

JOIN order_details od
    ON o.id = od.order_id

JOIN products p
    ON od.product_id = p.id

WHERE o.order_date IS NOT NULL;
"""