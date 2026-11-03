{{ config(
    materialized='view',
    schema='gold_layer'
) }}

SELECT
    '1. Bronze (Dữ liệu thô)' AS layer,
    COUNT(*) AS total_records,
    COUNT(DISTINCT id) AS unique_ids,
    ROUND(AVG(
        CASE 
            WHEN LOWER(price) = 'nan' OR price IS NULL THEN NULL 
            ELSE SAFE_CAST(REGEXP_REPLACE(CAST(price AS STRING), r'[\$, ]', '') AS FLOAT64) 
        END
    ), 2) AS avg_price
FROM `{{ env_var('GCP_PROJECT_ID') }}.bronze_layer.airbnb_raw`

UNION ALL

SELECT
    '2. Silver (Đã làm sạch)' AS layer,
    COUNT(*) AS total_records,
    COUNT(DISTINCT listing_id) AS unique_ids,
    ROUND(AVG(price_usd), 2) AS avg_price
FROM {{ ref('silver_airbnb_cleaned') }}
WHERE price_usd IS NOT NULL AND NOT IS_NAN(price_usd)