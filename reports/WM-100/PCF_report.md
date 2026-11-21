# Product Carbon Footprint study — WM-100 wireless rechargeable mouse (fictional)

*Generated 2026-11-21 by `pcf-lca-engine`. Fictional product, illustrative emission factors.*

## 1. Result

| | |
|---|---|
| **PCF (cradle-to-grave, excl. biogenic)** | **2.79 kg CO2e** per declared unit |
| 95% interval (Monte Carlo, 10,000 runs) | 2.69 – 2.94 kg CO2e (CV 2.2%) |
| Primary data share (PACT definition) | 45.3% |
| Data quality rating (contribution-weighted) | 1.72 — Very good |
| Recycling credits (reported separately) | -0.039 kg CO2e |

## 2. Goal and scope

- **Declared unit:** 1 wireless mouse with charging cable and retail packaging, used for 4 years
- **Intended application:** Hotspot identification, eco-design decisions and Scope 3 Cat 1/11/12 inputs
- **System boundary:** Cradle-to-grave: raw materials, packaging, production, distribution, use, end of life
- **GWP method:** IPCC AR6 GWP100 (kg CO2e)
- **System model / end-of-life allocation:** Cut-off (recycled content) — recycling burdens to the user of recycled material, no credits in the total
- **Reference year:** 2025
- **Excluded:** Capital goods (moulds, factory buildings, SMT lines); Employee commuting and business travel of suppliers; Retail store energy; Adhesives and labels (below cut-off, see validation report)
- **Cut-off:** excluded mass ≤ 1.0% and estimated impact ≤ 1.0%
- **Allocation:** factory overhead allocated by **mass** (0.107 kWh/unit); alternatives tested in §6
- **Use phase:** 4 years in RER, 0.307 kWh/year
- **End of life:** RER scenario, WEEE collection 45%

## 3. Results by life-cycle stage

| Stage | kg CO2e | Share % |
|---|---|---|
| Raw materials | 1.862 | 66.657 |
| Packaging | 0.075 | 2.684 |
| Production | 0.316 | 11.295 |
| Distribution | 0.131 | 4.686 |
| Use | 0.313 | 11.192 |
| End of life | 0.097 | 3.487 |

## 4. Hotspots

| Hotspot | kg CO2e | Share % |
|---|---|---|
| C08 Main PCBA | 0.880 | 31.494 |
| C09 Optical sensor module | 0.320 | 11.452 |
| Charging + receiver power, 4 years (RER) | 0.313 | 11.192 |
| Final assembly & test (metered) | 0.203 | 7.278 |
| C17 USB-C charging cable | 0.162 | 5.798 |
| C11 Li-ion polymer battery 500mAh | 0.120 | 4.295 |
| C14 USB receiver PCBA | 0.102 | 3.665 |
| C01 Top shell | 0.083 | 2.978 |

## 5. Life cycle inventory and data sources

- Inventory lines: 56 (see `inventory.csv`, each with activity amount, EF, pedigree scores and GSD²)
- Emission-factor selections with justification and competing candidates: `ef_selection_log.csv`

**Supplier-specific (primary) data**

| component_id | supplier_id | pcf_kgco2e_per_unit | reference_year | verification | decision | reason |
|---|---|---|---|---|---|---|
| C08 | SUP-EL1 | 0.880 | 2025 | third_party | accepted | meets boundary, age and verification rules |
| C11 | SUP-BT1 | 0.120 | 2024 | self_declared | accepted | meets boundary, age and verification rules |

**Material emission-factor selections**

| component_id | role | selected_ef | applicability_score | n_candidates |
|---|---|---|---|---|
| C01 | material:virgin | EF-PCABS-RAS-V | 2.000 | 2 |
| C01 | material:recycled | EF-PCABS-GLO-R | 2.350 | 1 |
| C02 | material:virgin | EF-PCABS-RAS-V | 2.000 | 2 |
| C02 | material:recycled | EF-PCABS-GLO-R | 2.350 | 1 |
| C03 | material | EF-TPE-GLO-V | 2.450 | 1 |
| C04 | material | EF-ABS-GLO-V | 2.100 | 2 |
| C05 | material | EF-POM-GLO-V | 2.100 | 1 |
| C06 | material | EF-SIL-GLO-V | 2.750 | 1 |
| C07 | material | EF-SST-GLO-V | 2.100 | 1 |
| C09 | component | EF-SENSOR-GLO | 2.800 | 1 |
| C10 | component | EF-SWITCH-GLO | 2.800 | 1 |
| C12 | material | EF-STL-GLO-V | 1.900 | 1 |
| C13 | material | EF-PTFE-GLO-V | 2.750 | 1 |
| C14 | material | EF-PCBA-RAS | 2.350 | 2 |
| C15 | material | EF-ABS-GLO-V | 2.100 | 2 |
| C16 | material | EF-CU-GLO-V | 2.100 | 1 |
| C17 | material | EF-CABLE-GLO | 2.700 | 1 |
| P01 | material:virgin | EF-CRTN-GLO-V | 2.100 | 2 |
| P01 | material:recycled | EF-CRTN-GLO-R | 2.100 | 2 |
| P02 | material | EF-PULP-GLO | 2.450 | 1 |
| P03 | material | EF-PAPER-GLO | 2.350 | 1 |
| P04 | material | EF-LDPE-GLO-V | 2.000 | 1 |

**Biogenic carbon (ISO 14067 requirement):** Biogenic CO2 removal in fibre packaging: **-0.120 kg CO2**; released at end of life: 0.017; stored in landfill: 0.003; transferred to recycling: 0.099. Reported separately and **not** included in the PCF total.

## 6. Interpretation (ISO 14044 §4.5)

**Sensitivity (one-at-a-time)**

| Parameter (±20%) | −20% → Δ% | +20% → Δ% |
|---|---|---|
| PCBA emission factor | -7.0 | 7.0 |
| Production grid intensity | -2.3 | 2.3 |
| Product lifetime | -2.2 | 2.2 |
| Use-phase power draw | -2.2 | 2.2 |
| Ocean freight distance | -0.3 | 0.3 |
| WEEE collection rate | -0.1 | 0.1 |

**Allocation-key sensitivity**

| allocation_key | overhead_kwh_per_unit | total_kgco2e | vs_mass_pct |
|---|---|---|---|
| mass | 0.107 | 2.794 | 0.000 |
| units | 0.281 | 2.895 | 3.625 |
| economic | 0.216 | 2.858 | 2.271 |

**Eco-design scenarios**

| scenario | kg CO2e | Δ vs baseline % |
|---|---|---|
| baseline | 2.794 | 0.000 |
| recycled_aluminium | 2.794 | 0.000 |
| pcr_plastics | 2.744 | -1.798 |
| renewable_assembly | 2.549 | -8.765 |
| no_air_freight | 2.724 | -2.497 |
| combined | 2.429 | -13.060 |

## 7. Data quality and validation

26 checks — 0 FAIL, 1 WARN.

| check | status | detail |
|---|---|---|
| required columns | PASS | all present |
| unique ef_id | PASS | 61 factors |
| positive values | PASS | ok |
| pedigree scores in 1-5 | PASS | ok |
| reference year <= study year | PASS | ok |
| dataset age <= 6 years | WARN | older datasets (temporal penalty applied): ['EF-SIL-GLO-V', 'EF-PTFE-GLO-V'] |
| geographies in region hierarchy | PASS | ok |
| EoL fractions sum to 1 (RER) | PASS | ok |
| treatment factors defined (RER) | PASS | ok |
| EoL fractions sum to 1 (RNA) | PASS | ok |
| treatment factors defined (RNA) | PASS | ok |
| allocation key valid | PASS | mass |
| all products in factory allocation table | PASS | ok |
| BOM required columns | PASS | all present |
| unique component ids | PASS | ok |
| positive mass and quantity | PASS | ok |
| recycled content 0-100% | PASS | ok |
| ef_basis is mass|unit | PASS | ok |
| process in process-energy table | PASS | ok |
| every material mapped to an emission factor | PASS | 21 lines mapped |
| every material has an end-of-life group | PASS | ok |
| recycled-content lines have a recycled dataset | PASS | ok |
| mass balance: product | PASS | BOM 99.4 g vs declared 99.4 g (0.00%) |
| mass balance: packaging | PASS | BOM 77.0 g vs declared 77.0 g (0.00%) |
| cut-off: excluded mass share | PASS | 0.5 g excluded = 0.28% (limit 1.0%) |
| cut-off: estimated excluded impact | PASS | ~0.0040 kg CO2e at proxy 8.0 kg/kg = 0.14% of PCF |

## 8. Limitations

- Emission factors are illustrative values in plausible ranges, not licensed ecoinvent / Sphera datasets.
- Monte Carlo covers emission-factor uncertainty only; activity-data uncertainty and correlations are not modelled.
- Distribution uses one representative Asia → Europe route for all markets.
- Replacement batteries' end-of-life is not modelled (below 1% of the total).
- Not third-party verified; not for comparative assertions disclosed to the public.

Warnings: none
