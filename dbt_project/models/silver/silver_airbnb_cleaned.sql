{{ config(
    materialized='table',
    schema='silver_layer',
    tags=['silver', 'airbnb_cleaned']
) }}

WITH raw_source AS (
    SELECT * FROM `{{ env_var('GCP_PROJECT_ID') }}.bronze_layer.airbnb_raw`
),

deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER(
            PARTITION BY id 
            ORDER BY 
                CASE 
                    WHEN Construction_year IS NULL OR LOWER(TRIM(Construction_year)) IN ('nan', 'null', '') THEN NULL 
                    ELSE SAFE_CAST(Construction_year AS FLOAT64) 
                END DESC NULLS LAST,
                CASE 
                    WHEN reviews_per_month IS NULL OR LOWER(TRIM(reviews_per_month)) IN ('nan', 'null', '') THEN NULL 
                    ELSE SAFE_CAST(reviews_per_month AS FLOAT64) 
                END DESC NULLS LAST
        ) AS row_num
    FROM raw_source
),

filtered_records AS (
    SELECT * 
    FROM deduplicated
    WHERE row_num = 1 
      AND id IS NOT NULL
      AND id != 'nan'
),

cleaned_casts AS (
    SELECT
        CAST(id AS INT64) AS listing_id,
        COALESCE(NULLIF(TRIM(NAME), ''), 'Unknown Listing') AS listing_name,
        SAFE_CAST(host_id AS INT64) AS host_id,
        COALESCE(NULLIF(TRIM(host_name), ''), 'Anonymous Host') AS host_name,
        
        CASE 
            WHEN LOWER(TRIM(host_identity_verified)) = 'verified' THEN 'verified'
            ELSE 'unconfirmed'
        END AS host_identity_status,

        CASE 
            WHEN LOWER(TRIM(neighbourhood_group)) IN ('manhattan', 'manhatan') THEN 'Manhattan'
            WHEN LOWER(TRIM(neighbourhood_group)) IN ('brooklyn', 'brookln') THEN 'Brooklyn'
            WHEN LOWER(TRIM(neighbourhood_group)) = 'queens' THEN 'Queens'
            WHEN LOWER(TRIM(neighbourhood_group)) = 'bronx' THEN 'Bronx'
            WHEN LOWER(TRIM(neighbourhood_group)) = 'staten island' THEN 'Staten Island'
            ELSE 'Other/Unknown'
        END AS neighbourhood_group,

        COALESCE(NULLIF(TRIM(neighbourhood), ''), 'Unknown Area') AS neighbourhood,
        ROUND(SAFE_CAST(lat AS FLOAT64), 6) AS latitude,
        ROUND(SAFE_CAST(long AS FLOAT64), 6) AS longitude,
        COALESCE(NULLIF(TRIM(country), ''), 'United States') AS country,
        COALESCE(NULLIF(UPPER(TRIM(country_code)), ''), 'US') AS country_code,
        INITCAP(TRIM(room_type)) AS room_type,

        CASE 
            WHEN LOWER(TRIM(cancellation_policy)) IN ('strict', 'moderate', 'flexible') 
            THEN LOWER(TRIM(cancellation_policy))
            ELSE 'flexible'
        END AS cancellation_policy,

        COALESCE(SAFE_CAST(instant_bookable AS BOOL), FALSE) AS is_instant_bookable,
        
        -- Construction year
        CASE 
            WHEN Construction_year IS NULL OR LOWER(TRIM(Construction_year)) IN ('nan', 'null', '') THEN NULL
            ELSE CAST(ROUND(SAFE_CAST(Construction_year AS FLOAT64)) AS INT64)
        END AS construction_year,

        -- 1. Bóc tách Price và triệt tiêu chuỗi 'nan'
        CASE 
            WHEN LOWER(TRIM(price)) = 'nan' OR price IS NULL THEN NULL
            ELSE SAFE_CAST(REGEXP_REPLACE(CAST(price AS STRING), r'[\$, ]', '') AS FLOAT64)
        END AS price_usd,

        -- 2. Bóc tách Service Fee và triệt tiêu chuỗi 'nan'
        CASE 
            WHEN LOWER(TRIM(service_fee)) = 'nan' OR service_fee IS NULL THEN 0.0
            ELSE COALESCE(SAFE_CAST(REGEXP_REPLACE(CAST(service_fee AS STRING), r'[\$, ]', '') AS FLOAT64), 0.0)
        END AS service_fee_usd,

        -- 3. Xử lý minimum_nights (xử lý an toàn chuỗi nan/float-string và clip về [1, 365])
        CASE 
            WHEN minimum_nights IS NULL OR LOWER(TRIM(minimum_nights)) IN ('nan', 'null', '') OR SAFE_CAST(minimum_nights AS FLOAT64) <= 0 THEN 1
            WHEN SAFE_CAST(minimum_nights AS FLOAT64) > 365 THEN 365
            ELSE CAST(ROUND(SAFE_CAST(minimum_nights AS FLOAT64)) AS INT64)
        END AS minimum_nights,

        -- 4. Xử lý availability_365
        CASE 
            WHEN availability_365 IS NULL OR LOWER(TRIM(availability_365)) IN ('nan', 'null', '') OR SAFE_CAST(availability_365 AS FLOAT64) <= 0 THEN 0
            WHEN SAFE_CAST(availability_365 AS FLOAT64) > 365 THEN 365
            ELSE CAST(ROUND(SAFE_CAST(availability_365 AS FLOAT64)) AS INT64)
        END AS availability_365,

        -- 5. Đánh giá (reviews, rating)
        CASE 
            WHEN number_of_reviews IS NULL OR LOWER(TRIM(number_of_reviews)) IN ('nan', 'null', '') OR SAFE_CAST(number_of_reviews AS FLOAT64) <= 0 THEN 0
            ELSE CAST(ROUND(SAFE_CAST(number_of_reviews AS FLOAT64)) AS INT64)
        END AS number_of_reviews,

        CASE 
            WHEN SAFE.PARSE_DATE('%m/%d/%Y', last_review) > CURRENT_DATE() THEN NULL
            ELSE SAFE.PARSE_DATE('%m/%d/%Y', last_review)
        END AS last_review_date,

        CASE 
            WHEN reviews_per_month IS NULL OR LOWER(TRIM(reviews_per_month)) IN ('nan', 'null', '') OR SAFE_CAST(reviews_per_month AS FLOAT64) <= 0 THEN 0.0
            ELSE ROUND(SAFE_CAST(reviews_per_month AS FLOAT64), 2)
        END AS reviews_per_month,
        
        -- Sửa triệt để review_rating: '5.0' -> FLOAT64 -> INT64
        CASE 
            WHEN review_rate_number IS NULL OR LOWER(TRIM(review_rate_number)) IN ('nan', 'null', '') OR SAFE_CAST(review_rate_number AS FLOAT64) <= 0 THEN 0
            ELSE CAST(ROUND(SAFE_CAST(review_rate_number AS FLOAT64)) AS INT64)
        END AS review_rating,

        CASE 
            WHEN calculated_host_listings_count IS NULL OR LOWER(TRIM(calculated_host_listings_count)) IN ('nan', 'null', '') OR SAFE_CAST(calculated_host_listings_count AS FLOAT64) <= 0 THEN 1
            ELSE CAST(ROUND(SAFE_CAST(calculated_host_listings_count AS FLOAT64)) AS INT64)
        END AS host_total_listings_count

    FROM filtered_records
)

SELECT
    *,
    -- Feature Engineering
    ROUND(price_usd + service_fee_usd, 2) AS total_initial_cost_usd,
    ROUND(availability_365 / 365.0 * 100, 2) AS availability_pct,
    
    CASE 
        WHEN price_usd < 300 THEN 'Budget (< $300)'
        WHEN price_usd <= 800 THEN 'Mid-range ($300-$800)'
        ELSE 'Luxury (> $800)'
    END AS price_tier,

    CURRENT_TIMESTAMP() AS silver_loaded_at
FROM cleaned_casts
WHERE price_usd IS NOT NULL 
  AND NOT IS_NAN(price_usd)
  AND NOT IS_NAN(service_fee_usd)
