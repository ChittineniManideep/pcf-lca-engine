-- Reporting views (ANSI SQL; Snowflake- and DuckDB-compatible)

-- PCF per declared unit by life-cycle stage
CREATE OR REPLACE VIEW v_pcf_by_stage AS
SELECT
    product_id,
    stage,
    SUM(kgco2e)                                                         AS kgco2e,
    100 * SUM(kgco2e) / SUM(SUM(kgco2e)) OVER (PARTITION BY product_id) AS share_pct
FROM fact_pcf_inventory
GROUP BY product_id, stage;

-- Headline KPIs: total, primary data share (PACT), contribution-weighted DQR
CREATE OR REPLACE VIEW v_pcf_kpis AS
SELECT
    product_id,
    SUM(kgco2e)                                                                    AS pcf_kgco2e,
    100 * SUM(CASE WHEN data_type IN ('primary', 'primary_activity') THEN kgco2e ELSE 0 END)
        / SUM(kgco2e)                                                              AS primary_data_share_pct,
    SUM(dqr * GREATEST(kgco2e, 0)) / SUM(GREATEST(kgco2e, 0))                      AS weighted_dqr,
    COUNT(*)                                                                       AS inventory_lines
FROM fact_pcf_inventory
GROUP BY product_id;

-- Hotspots: lines with weak data quality that carry material weight (data-improvement backlog)
CREATE OR REPLACE VIEW v_data_quality_priorities AS
WITH line AS (
    SELECT
        product_id, component_id, item, ef_id, data_type, dqr, gsd95, kgco2e,
        100 * kgco2e / SUM(kgco2e) OVER (PARTITION BY product_id) AS share_pct
    FROM fact_pcf_inventory
)
SELECT *,
       share_pct * dqr AS improvement_priority   -- big contribution x poor quality first
FROM line
WHERE share_pct >= 2 AND dqr >= 2
ORDER BY improvement_priority DESC;

-- Scope 3 roll-up: per-unit footprint x units sold, by GHG Protocol category
CREATE OR REPLACE VIEW v_scope3_by_category AS
SELECT
    s.year,
    i.scope3_category,
    SUM(i.kgco2e * s.units) / 1000.0 AS tco2e
FROM fact_unit_inventory_by_region i
JOIN fact_units_sold s
  ON s.product_id = i.product_id
 AND s.region     = i.region
GROUP BY s.year, i.scope3_category;

-- Scope 3 by product and region with emission intensity per EUR revenue
CREATE OR REPLACE VIEW v_scope3_by_product_region AS
WITH per_unit AS (
    SELECT product_id, region, SUM(kgco2e) AS kgco2e_per_unit
    FROM fact_unit_inventory_by_region
    GROUP BY product_id, region
)
SELECT
    s.year, s.product_id, s.region, s.units,
    p.kgco2e_per_unit,
    p.kgco2e_per_unit * s.units / 1000.0               AS tco2e,
    p.kgco2e_per_unit * s.units / s.revenue_eur * 1000 AS gco2e_per_eur
FROM fact_units_sold s
JOIN per_unit p
  ON p.product_id = s.product_id
 AND p.region     = s.region;

-- Emission-factor usage audit: which datasets drive the footprint
CREATE OR REPLACE VIEW v_ef_usage AS
SELECT
    i.ef_id,
    MAX(e.name)              AS ef_name,
    MAX(e.geography)         AS geography,
    MAX(e.reference_year)    AS reference_year,
    COUNT(*)                 AS lines,
    SUM(i.kgco2e)            AS kgco2e
FROM fact_pcf_inventory i
LEFT JOIN dim_emission_factor e ON e.ef_id = i.ef_id
GROUP BY i.ef_id;
