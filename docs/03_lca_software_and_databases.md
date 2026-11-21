# Mapping to commercial LCA platforms and LCI databases

The engine is plain Python so every step is visible. The same concepts appear under different names in each LCA platform. This page maps them so the model can be rebuilt in any of them.

## Concept map

| This repo | openLCA | SimaPro | Sphera LCA for Experts (GaBi) | iPoint / Makersite (PCF-at-scale tools) |
|---|---|---|---|---|
| `products/*.yaml` + BOM | Product system | Assembly / Life cycle | Plan (top level) | Product / BOM import |
| BOM line | Input exchange of a process | Material / assembly input | Process input flow | BOM line item |
| `ef_library.csv` row | Provider process (ecoinvent / other) | Library process | Sphera MLC dataset | Mapped dataset (often AI-assisted matching) |
| `material_class` matching | Manual provider linking | Manual library search | Manual flow linking | Automated BOM-to-dataset matching with confidence score |
| Applicability score + log | Data quality system (pedigree) | Pedigree uncertainty | Data quality indicators | Mapping confidence / data quality |
| Process scrap → gross input | Waste output + higher input | "Avoided products"/waste scenario | Plan with scrap loop | Manufacturing loss factor |
| Use / EoL stages | Separate processes in the product system | Life cycle stage + waste scenario | Use / EoL plans | Stage modules |
| Monte Carlo | Built-in uncertainty simulation | Monte Carlo analysis | Uncertainty analysis add-on | Usually not exposed |
| Scenarios (`scenarios.yaml`) | Parameter sets / project variants | Parameters / scenarios | Parameter variation / scenario analysis | What-if / design alternatives |
| Supplier PCF | User-defined process with supplier value | User-defined process | Supplier dataset | Supplier data exchange (PACT / Catena-X) |

## Life cycle inventory databases

| Database | Notes |
|---|---|
| **ecoinvent** (v3.x) | Most widely used general LCI database. It comes in three system models (*cut-off*, *APOS*, *consequential*); pick one and use it throughout. This repo mirrors the cut-off logic. Uses the pedigree matrix that this project replicates. |
| **Sphera Managed LCA Content** (formerly GaBi databases) | Strong industrial and electronics coverage, and used in many automotive and electronics PCFs. Its data quality approach differs from ecoinvent's, so don't mix the two in one product system without documenting it. |
| **Others** | Environmental Footprint (EF) secondary datasets for PEF studies; industry association datasets (e.g. for plastics or aluminium); the ELCD archive. Electronics companies often also commission component datasets for ICs and PCBAs. |

## Rebuilding this model in openLCA (free) in about an hour

1. Import an LCI database (ecoinvent cut-off if licensed; otherwise a free database from openLCA Nexus).
2. Create a **process** "WM-100 assembly" with inputs from `data/bom/WM-100.csv`, using the gross masses from `reports/WM-100/inventory.csv` (`activity_amount` where `sub_stage = materials`).
3. Link each input to the provider closest to `selected_ef` in `ef_selection_log.csv`, and enter the pedigree scores from `inventory.csv` in the exchange's data quality fields.
4. Add electricity inputs (`sub_stage = component_processing, final_assembly, factory_overhead`) linked to the CN grid process.
5. Create transport, use and EoL processes from the same inventory lines and connect them into a **product system**.
6. Calculate with **IPCC 2021 GWP100** and compare the stage results with `reports/WM-100/stage_summary.csv`. Remaining differences come from the background database.

## Swapping in licensed data

The library format is deliberately flat so licensed values can drop in:

```csv
ef_id,name,category,material_class,technology,geography,unit,value_kgco2e,reference_year,source,reliability,completeness,technological
```

Keep `material_class` as the join key, set `source` to the dataset UUID/version, and re-run `python -m pcf validate && pytest`. The regression test (`test_regression_baseline`) will fail on purpose, which is the reminder to update the reference values after a data change.
