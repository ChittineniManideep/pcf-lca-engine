# Emission-factor assessment and dataset applicability

Choosing the dataset is where most of the expert judgement in a PCF goes. Two analysts with the same BOM can differ by 30% or more depending on which datasets they pick. This project makes every choice explicit, scored and logged.

## The selection algorithm (`src/pcf/ef_library.py`)

For each BOM line:

1. **Filter** the library by `material_class`, technology (virgin/generic vs recycled) and unit (`kg` for mass-based lines, `unit` for per-piece components such as sensors).
2. **Score** each candidate on five pedigree dimensions. Temporal and geographical scores are calculated **against this specific activity**, not taken from the dataset's own metadata.
3. **Combine** the scores into an applicability score (lower is better):

   | Dimension | Weight | Why this weight |
   |---|---|---|
   | Geographical | 0.35 | Grid mix and smelting energy source dominate metals, plastics and electronics |
   | Technological | 0.25 | Wrong technology (e.g. generic PCBA for a 2-layer board) gives the largest errors |
   | Temporal | 0.20 | Grid decarbonisation and process efficiency change over time |
   | Reliability | 0.10 | Measured and verified beats estimated |
   | Completeness | 0.10 | Representative sample |

4. **Select** the lowest score and write the justification, the runner-up and every candidate's score to `ef_selection_log.csv`.
5. **Blend** for recycled content: `EF = (1 − r) × EF_virgin + r × EF_recycled`, with pedigree scores blended the same way. If no recycled dataset exists, the virgin factor is used (conservative) and a warning is raised.

Try it from the command line:

```bash
python -m pcf select aluminium CN --tech virgin generic
python -m pcf select PCBA CN
```

## Worked examples from this study

| Line | Candidates | Selected | Judgement |
|---|---|---|---|
| Keyboard top case, aluminium, made in CN | `EF-AL-CN-V` (20.0), `EF-AL-GLO-V` (16.5) | **EF-AL-CN-V** | China's coal-heavy smelting makes the regional dataset more representative. Using the global average would understate the part by about 18%. |
| PC/ABS shells, CN | `EF-PCABS-RAS-V` (2020), `EF-PCABS-GLO-V` (2021) | **RAS** | Parent-region match outweighs being one year older |
| Recycled PC/ABS share | only `EF-PCABS-GLO-R` | GLO | No regional PCR dataset, so geography scores 3. This is flagged in the data-quality priorities view. |
| Silicone domes | `EF-SIL-GLO-V` (2017) | only option | 8 years old → temporal score 3. The validation report shows a WARN to refresh it. |
| Electricity at a CN assembly plant | CN, RAS, VN, GLO, RER… | **EF-ELEC-CN** | Exact match. The PPA solar factor is excluded from the baseline because it's a market-based instrument and is used only in the `renewable_assembly` scenario. |
| Keyboard PCBA, supplier data from 2019 | supplier PCF 2.05 kg vs `EF-PCBA-RAS` | **secondary** | Supplier data rejected as older than 3 years. Recorded in `supplier_data_decisions.csv`. |

## Applicability red flags (checklist)

- **Unit mismatch:** per-kg PCBA factors applied to per-cm² board areas, or per-unit IC factors applied by mass.
- **Boundary mismatch:** a supplier "PCF" that is gate-to-gate (only their own factory) being used as cradle-to-gate. *The engine rejects these.*
- **Double counting:** a supplier cradle-to-gate value for an assembly **plus** secondary factors for its sub-parts. *The engine skips material and processing lines once primary data is accepted.*
- **Market-based vs location-based electricity** mixed within one baseline.
- **Allocation inside the dataset:** ecoinvent *cut-off* vs *APOS* vs *consequential* system models give different values for the same material. Use one system model throughout.
- **GWP version:** mixing AR5 and AR6 factors (methane GWP100 differs between them).
- **Biogenic carbon:** some fibre datasets net off biogenic uptake and others don't. Check before using.
- **Proxy datasets:** when using a proxy (e.g. "generic plastic" for TPE), set the technological score to 4 or 5 so the uncertainty widens to reflect it.
- **Old datasets for fast-changing sectors:** semiconductor and battery footprints have dropped sharply over the last decade, so a 2015 dataset can be badly outdated.

## Turning judgement into a data-improvement backlog

`sql/02_views.sql → v_data_quality_priorities` ranks lines by **share of total × DQR**. The top of that list is where supplier engagement or better datasets would most reduce uncertainty. In this study that's the keyboard PCBA (23% of the total, secondary data) and the mouse optical sensor (11%, generic dataset).
