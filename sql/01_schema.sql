-- Sustainability data mart: product carbon footprint + Scope 3
-- ANSI SQL that runs unchanged on Snowflake and DuckDB.

CREATE OR REPLACE TABLE dim_product (
    product_id      VARCHAR PRIMARY KEY,
    product_name    VARCHAR,
    declared_unit   VARCHAR
);

CREATE OR REPLACE TABLE dim_emission_factor (
    ef_id           VARCHAR PRIMARY KEY,
    name            VARCHAR,
    category        VARCHAR,
    material_class  VARCHAR,
    technology      VARCHAR,
    geography       VARCHAR,
    unit            VARCHAR,
    value_kgco2e    DECIMAL(18, 6),
    reference_year  INTEGER,
    source          VARCHAR,
    reliability     INTEGER,
    completeness    INTEGER,
    technological   INTEGER
);

-- One row per inventory line of one declared unit (baseline, default market)
CREATE OR REPLACE TABLE fact_pcf_inventory (
    product_id      VARCHAR,
    stage           VARCHAR,
    sub_stage       VARCHAR,
    component_id    VARCHAR,
    item            VARCHAR,
    activity_amount DECIMAL(18, 6),
    activity_unit   VARCHAR,
    ef_id           VARCHAR,
    ef_value        DECIMAL(18, 6),
    ef_unit         VARCHAR,
    kgco2e          DECIMAL(18, 6),
    data_type       VARCHAR,
    category        VARCHAR,
    reliability     INTEGER,
    completeness    INTEGER,
    temporal        INTEGER,
    geographical    INTEGER,
    technological   INTEGER,
    note            VARCHAR,
    dqr             DECIMAL(6, 3),
    gsd95           DECIMAL(10, 4)
);

-- Per-unit inventory recalculated for each sales region, tagged with Scope 3 category
CREATE OR REPLACE TABLE fact_unit_inventory_by_region (
    product_id      VARCHAR,
    stage           VARCHAR,
    sub_stage       VARCHAR,
    item            VARCHAR,
    kgco2e          DECIMAL(18, 6),
    data_type       VARCHAR,
    region          VARCHAR,
    scope3_category INTEGER
);

CREATE OR REPLACE TABLE fact_units_sold (
    year            INTEGER,
    product_id      VARCHAR,
    region          VARCHAR,
    units           BIGINT,
    revenue_eur     DECIMAL(18, 2)
);
