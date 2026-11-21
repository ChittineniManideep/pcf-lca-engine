# From product footprints to Scope 3, and supplier emission data

## Product PCF → corporate Scope 3

For a brand that outsources manufacturing, almost all its footprint sits in Scope 3. Product footprints are the most accurate way to calculate the largest categories, because they replace spend × average-sector factors with physical data.

| Life-cycle stage of the product | Scope 3 category of the brand owner | Notes |
|---|---|---|
| Materials, components, packaging, contract assembly, inbound logistics | **Cat 1** Purchased goods & services | Cradle-to-gate of what is bought |
| Factory → port → DC freight paid by the brand | **Cat 4** Upstream transportation & distribution | Includes air-expedited share |
| DC → retailer (paid by the retailer) | **Cat 9** Downstream transportation & distribution | Mapping depends on who pays, set in `study.yaml` |
| Electricity used in the use phase | **Cat 11** Use of sold products (direct use-phase emissions) | Total expected lifetime emissions of units sold in the year |
| Replacement batteries | Cat 11 (indirect use-phase, optional under the GHG Protocol) | Tagged `use:consumables` so it can be excluded |
| End-of-life treatment | **Cat 12** End-of-life treatment of sold products | Uses the sales region's EoL scenario |

`src/pcf/scope3.py` recalculates each product **per sales region**, because the use-phase grid and EoL scenario differ between Europe and North America. It maps each inventory line to its category and multiplies by units sold (`data/sales/units_sold.csv`).

### Product-based vs spend-based Cat 1

The pipeline also estimates Cat 1 the spend-based way (purchased COGS × EEIO factor) and compares the two:

| Product | Product-based Cat 1 | Spend-based Cat 1 | Difference |
|---|---|---|---|
| WK-200 | ~9,500 t | ~11,300 t | +18% |
| WM-100 | ~4,500 t | ~13,600 t | **+200%** |

Spend-based methods track price, not physics. A light, high-margin product is overstated by a large factor, so moving from spend-based to product-based data changes both the baseline and where the hotspots appear. That's the main argument for building a PCF programme.

## Supplier emission data

### Acceptance rules (`study.yaml → supplier_data_rules`)

| Rule | Why |
|---|---|
| Boundary must be **cradle-to-gate** | A gate-to-gate value (supplier's own factory only) would omit the materials, which are most of the impact |
| Reference year within **3 years** | Grid mixes and yields change; stale data gets a temporal penalty or is rejected |
| Verification **third-party** (reliability 1) or **self-declared** (reliability 3) | Unverified data is accepted but widens the uncertainty |

Every decision is logged in `supplier_data_decisions.csv` with a reason, which is the audit trail a verifier asks for.

### Primary data share (PDS)

PDS = share of the PCF that comes from primary data, meaning supplier-specific PCFs **plus** company-specific activity data (metered assembly and overhead energy) even when multiplied by a secondary grid factor. It follows the definition in the PACT methodology and is the key metric in supplier engagement programmes.

| Product | PDS | What drives it |
|---|---|---|
| WM-100 | ~45% | Verified PCBA PCF + self-declared battery PCF + metered assembly |
| WK-200 | ~6% | PCBA supplier data rejected (2019); only metered assembly is primary |

The keyboard is the obvious supplier-engagement target: a current, verified PCBA PCF would raise PDS to roughly 30% and narrow the uncertainty interval.

### Data exchange format

`pact_footprint.json` is a simplified ProductFootprint record modelled on the PACT (Partnership for Carbon Transparency) technical specification. It includes declared unit, fossil emissions excluding biogenic, biogenic carbon content, AR6 characterisation, ISO 14067 as the cross-sectoral standard, reference period, primary data share, DQR and an uncertainty description. It is **not schema-validated**. Validate against the current PACT JSON schema before any real exchange.
