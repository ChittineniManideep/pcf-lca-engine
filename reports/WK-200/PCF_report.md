# Product Carbon Footprint study — WK-200 wireless low-profile keyboard, aluminium top case (fictional)

*Generated 2026-11-21 by `pcf-lca-engine`. Fictional product, illustrative emission factors.*

## 1. Result

| | |
|---|---|
| **PCF (cradle-to-grave, excl. biogenic)** | **12.19 kg CO2e** per declared unit |
| 95% interval (Monte Carlo, 10,000 runs) | 11.58 – 12.99 kg CO2e (CV 3.0%) |
| Primary data share (PACT definition) | 6.1% |
| Data quality rating (contribution-weighted) | 1.88 — Very good |
| Recycling credits (reported separately) | -1.257 kg CO2e |

## 2. Goal and scope

- **Declared unit:** 1 wireless keyboard with batteries and retail packaging, used for 5 years
- **Intended application:** Hotspot identification, eco-design decisions and Scope 3 Cat 1/11/12 inputs
- **System boundary:** Cradle-to-grave: raw materials, packaging, production, distribution, use, end of life
- **GWP method:** IPCC AR6 GWP100 (kg CO2e)
- **System model / end-of-life allocation:** Cut-off (recycled content) — recycling burdens to the user of recycled material, no credits in the total
- **Reference year:** 2025
- **Excluded:** Capital goods (moulds, factory buildings, SMT lines); Employee commuting and business travel of suppliers; Retail store energy; Adhesives and labels (below cut-off, see validation report)
- **Cut-off:** excluded mass ≤ 1.0% and estimated impact ≤ 1.0%
- **Allocation:** factory overhead allocated by **mass** (0.675 kWh/unit); alternatives tested in §6
- **Use phase:** 5 years in RER, 0.250 kWh/year
- **End of life:** RER scenario, WEEE collection 45%

## 3. Results by life-cycle stage

| Stage | kg CO2e | Share % |
|---|---|---|
| Raw materials | 8.766 | 71.935 |
| Packaging | 0.230 | 1.885 |
| Production | 1.574 | 12.919 |
| Distribution | 0.438 | 3.593 |
| Use | 0.669 | 5.488 |
| End of life | 0.509 | 4.180 |

## 4. Hotspots

| Hotspot | kg CO2e | Share % |
|---|---|---|
| C01 Top case | 4.752 | 38.995 |
| C08 Main PCBA | 2.816 | 23.108 |
| C02 Bottom case | 0.660 | 5.415 |
| plastic product — incineration | 0.400 | 3.279 |
| C03 Keycaps (set) | 0.399 | 3.278 |
| Factory overhead (mass allocation) | 0.392 | 3.216 |
| Replacement alkaline battery cells | 0.350 | 2.872 |
| Final assembly & test (metered) | 0.349 | 2.861 |

## 5. Life cycle inventory and data sources

- Inventory lines: 55 (see `inventory.csv`, each with activity amount, EF, pedigree scores and GSD²)
- Emission-factor selections with justification and competing candidates: `ef_selection_log.csv`

**Supplier-specific (primary) data**

| component_id | supplier_id | pcf_kgco2e_per_unit | reference_year | verification | decision | reason |
|---|---|---|---|---|---|---|
| C02 | SUP-PL1 | 0.410 | 2025 | self_declared | rejected | boundary 'gate-to-gate' not cradle-to-gate |
| C08 | SUP-EL1 | 2.050 | 2019 | third_party | rejected | reference year 2019 older than 3 years |

**Material emission-factor selections**

| component_id | role | selected_ef | applicability_score | n_candidates |
|---|---|---|---|---|
| C01 | material | EF-AL-CN-V | 1.400 | 2 |
| C02 | material:virgin | EF-PCABS-RAS-V | 2.000 | 2 |
| C02 | material:recycled | EF-PCABS-GLO-R | 2.350 | 1 |
| C03 | material | EF-ABS-GLO-V | 2.100 | 2 |
| C04 | material | EF-POM-GLO-V | 2.100 | 1 |
| C05 | material | EF-SIL-GLO-V | 2.750 | 1 |
| C06 | material | EF-PET-GLO-V | 2.350 | 1 |
| C07 | material | EF-STL-GLO-V | 1.900 | 1 |
| C08 | material | EF-PCBA-RAS | 2.350 | 2 |
| C09 | material | EF-PCBA-RAS | 2.350 | 2 |
| C10 | material | EF-ABS-GLO-V | 2.100 | 2 |
| C11 | material | EF-TPE-GLO-V | 2.450 | 1 |
| C12 | material | EF-STL-GLO-V | 1.900 | 1 |
| C13 | component | EF-ALK-GLO | 2.550 | 1 |
| C14 | material | EF-CU-GLO-V | 2.100 | 1 |
| P01 | material:virgin | EF-CRTN-GLO-V | 2.100 | 2 |
| P01 | material:recycled | EF-CRTN-GLO-R | 2.100 | 2 |
| P02 | material | EF-PULP-GLO | 2.450 | 1 |
| P03 | material | EF-PAPER-GLO | 2.350 | 1 |
| P04 | material | EF-LDPE-GLO-V | 2.000 | 1 |

**Biogenic carbon (ISO 14067 requirement):** Biogenic CO2 removal in fibre packaging: **-0.376 kg CO2**; released at end of life: 0.054; stored in landfill: 0.009; transferred to recycling: 0.312. Reported separately and **not** included in the PCF total.

## 6. Interpretation (ISO 14044 §4.5)

**Sensitivity (one-at-a-time)**

| Parameter (±20%) | −20% → Δ% | +20% → Δ% |
|---|---|---|
| Aluminium emission factor | -7.0 | 7.0 |
| PCBA emission factor | -4.8 | 4.8 |
| Production grid intensity | -2.6 | 2.6 |
| Product lifetime | -1.3 | 1.3 |
| Use-phase power draw | -0.5 | 0.5 |
| Ocean freight distance | -0.3 | 0.3 |
| WEEE collection rate | -0.0 | 0.0 |

**Allocation-key sensitivity**

| allocation_key | overhead_kwh_per_unit | total_kgco2e | vs_mass_pct |
|---|---|---|---|
| mass | 0.675 | 12.186 | 0.000 |
| units | 0.281 | 11.958 | -1.875 |
| economic | 0.373 | 12.011 | -1.436 |

**Eco-design scenarios**

| scenario | kg CO2e | Δ vs baseline % |
|---|---|---|
| baseline | 12.186 | 0.000 |
| recycled_aluminium | 9.296 | -23.720 |
| pcr_plastics | 11.783 | -3.306 |
| renewable_assembly | 11.503 | -5.606 |
| no_air_freight | 12.049 | -1.126 |
| combined | 8.072 | -33.758 |

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
| every material mapped to an emission factor | PASS | 18 lines mapped |
| every material has an end-of-life group | PASS | ok |
| recycled-content lines have a recycled dataset | PASS | ok |
| mass balance: product | PASS | BOM 627.1 g vs declared 627.1 g (0.00%) |
| mass balance: packaging | PASS | BOM 240.0 g vs declared 240.0 g (0.00%) |
| cut-off: excluded mass share | PASS | 2.3 g excluded = 0.27% (limit 1.0%) |
| cut-off: estimated excluded impact | PASS | ~0.0184 kg CO2e at proxy 8.0 kg/kg = 0.15% of PCF |

## 8. Limitations

- Emission factors are illustrative values in plausible ranges, not licensed ecoinvent / Sphera datasets.
- Monte Carlo covers emission-factor uncertainty only; activity-data uncertainty and correlations are not modelled.
- Distribution uses one representative Asia → Europe route for all markets.
- Replacement batteries' end-of-life is not modelled (below 1% of the total).
- Not third-party verified; not for comparative assertions disclosed to the public.

Warnings: none
