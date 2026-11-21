-- Snowflake load pattern for the warehouse extracts produced by `python -m pcf run`
-- (reports/warehouse/*.csv). Run 01_schema.sql first, then this, then 02_views.sql.

CREATE DATABASE IF NOT EXISTS SUSTAINABILITY;
CREATE SCHEMA IF NOT EXISTS SUSTAINABILITY.PCF;
USE SCHEMA SUSTAINABILITY.PCF;

CREATE OR REPLACE FILE FORMAT ff_csv
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('', 'NULL')
    EMPTY_FIELD_AS_NULL = TRUE;

CREATE OR REPLACE STAGE stg_pcf FILE_FORMAT = ff_csv;

-- From SnowSQL:  PUT file://reports/warehouse/*.csv @stg_pcf AUTO_COMPRESS=TRUE;

COPY INTO dim_product                   FROM @stg_pcf/dim_product.csv.gz;
COPY INTO dim_emission_factor           FROM @stg_pcf/dim_emission_factor.csv.gz;
COPY INTO fact_pcf_inventory            FROM @stg_pcf/fact_pcf_inventory.csv.gz;
COPY INTO fact_unit_inventory_by_region FROM @stg_pcf/fact_unit_inventory_by_region.csv.gz;
COPY INTO fact_units_sold               FROM @stg_pcf/fact_units_sold.csv.gz;

-- Post-load reconciliation: row counts and totals must match the pipeline's pcf_summary.csv
SELECT product_id, COUNT(*) AS lines, SUM(kgco2e) AS pcf_kgco2e
FROM fact_pcf_inventory
GROUP BY product_id;
