{{ config(
    materialized='table',
    schema='gold_layer',
    tags=['gold', 'bi_mart']
) }}

WITH silver AS (
    SELECT * FROM {{ ref('silver_airbnb_cleaned') }}
)

SELECT
    neighbourhood_group,
    room_type,
    price_tier,
    COUNT(listing_id) AS total_listings,
    ROUND(COUNTIF(host_identity_status = 'verified') * 100.0 / COUNT(*), 2) AS pct_verified_host,
    ROUND(AVG(price_usd), 2) AS avg_price_usd,
    ROUND(MIN(price_usd), 2) AS min_price_usd,
    ROUND(MAX(price_usd), 2) AS max_price_usd,
    ROUND(AVG(service_fee_usd), 2) AS avg_service_fee_usd,
    ROUND(AVG(total_initial_cost_usd), 2) AS avg_total_initial_cost_usd,
    ROUND(AVG(availability_pct), 2) AS avg_availability_pct,
    ROUND(AVG(minimum_nights), 1) AS avg_minimum_nights,
    ROUND(AVG(number_of_reviews), 1) AS avg_reviews_count,
    ROUND(AVG(review_rating), 2) AS avg_review_rating,
    CURRENT_TIMESTAMP() AS gold_loaded_at
FROM silver
GROUP BY 1, 2, 3
ORDER BY total_listings DESC