{{ config(
    materialized='table',
    schema='gold_layer',
    tags=['gold', 'ml_features']
) }}

SELECT
    listing_id,
    neighbourhood_group,
    room_type,
    cancellation_policy,
    host_identity_status,
    is_instant_bookable,
    construction_year,
    minimum_nights,
    number_of_reviews,
    reviews_per_month,
    review_rating,
    availability_365,
    price_usd AS target_price_usd
FROM {{ ref('silver_airbnb_cleaned') }}
WHERE price_usd > 0
  AND neighbourhood_group != 'Other/Unknown'