# Task-Aligned Segmentation Evaluation

**Authors:** Fan Hu and Khalid M. Mosalam

This repository contains the minimal processed analysis materials supporting the manuscript *From Semantic Segmentation Errors to Crop Canopy Fraction Estimates: A Task-Aligned Evaluation Framework*.

The package reproduces the primary task-aligned numerical analysis from processed fixed-model outputs and regenerates the reported date-stratified tables and figures from the included date-level summaries. It is not the full model-development repository and does not contain model weights, training code, raw imagery, or raw annotations.

## Source dataset and citation

The original [Sugar Beets 2016 dataset](https://www.ipb.uni-bonn.de/data/sugarbeets2016/) is distributed by its authors under the [Creative Commons Attribution-ShareAlike 4.0 International license (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/). Its RGB images and semantic annotations are not redistributed here. Image identifiers are retained so that eligible records can be related to the public source dataset.

Please cite the source dataset as:

> Chebrolu, N., Lottes, P., Schaefer, A., Winterhalter, W., Burgard, W., and Stachniss, C. (2017). Agricultural robot dataset for plant classification, localization and mapping on sugar beet fields. *The International Journal of Robotics Research*, 36(10), 1045--1052. [https://doi.org/10.1177/0278364917720510](https://doi.org/10.1177/0278364917720510)

## License

- Files under `scripts/` are licensed under the BSD 3-Clause License; see [`LICENSE-CODE`](LICENSE-CODE).
- The processed CSV and YAML materials under `config/`, `splits/`, and `results/` are licensed under the Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0); see [`LICENSE-DATA`](LICENSE-DATA).

Sugar Beets 2016 is the source dataset and is itself released under CC BY-SA 4.0. The original RGB images and annotations are not redistributed here. The processed materials contain derived evaluation subsets, confusion counts, task-aligned error accounting, crop-fraction records, and date-level summaries.

## Contents

| Path | Contents |
|---|---|
| `config/evaluation_protocol.yaml` | Scientifically relevant label, estimand, error-accounting, uncertainty, date-support, and representative-case rules. |
| `splits/may23_primary_429.csv` | The 429 primary May 23 image identifiers, acquisition date, and model-development split role. |
| `splits/temporal_185.csv` | The 185 date-stratified analysis image identifiers, acquisition dates, generalization roles, date-support flags, and available sequence/frame fields. Fifteen May 23 candidates with model-development training overlap were excluded before this file was formed. |
| `results/per_image_confusion.csv` | Per-image five-class confusion counts for the 429-image primary evaluation, plus probability-functional confusion counts needed to reproduce the reported functional metrics. |
| `results/task_aligned_errors.csv` | Per-image within- and cross-functional errors and the crop false-positive/false-negative decomposition. |
| `results/crop_fraction_records.csv` | Per-image reference, hard, and soft crop fractions and associated errors for the primary evaluation. Sequence and frame fields support the specified bootstrap. |
| `results/date_level_summary.csv` | Ten date-level crop and matched total-vegetation summaries, including sample support and claim-support flags. |
| `scripts/reproduce_tables.py` | Regenerates the numerical content of manuscript Tables 1--3 as portable CSV files. |
| `scripts/reproduce_main_figures.py` | Regenerates the quantitative plots corresponding to manuscript Figures 2, 3, and 5. |

All reported fractions are stored on a 0--1 scale. Multiply by 100 for percentages or percentage points as appropriate. Confusion matrices use reference classes as rows and predicted classes as columns.

## Reproduce tables and figures

Python 3.9 or newer is recommended. The scripts require NumPy, Matplotlib, and PyYAML:

```bash
python -m pip install "numpy>=1.22" "matplotlib>=3.4" "PyYAML>=6"
```

From the repository root, run:

```bash
python scripts/reproduce_tables.py --output-dir reproduced/tables
python scripts/reproduce_main_figures.py --output-dir reproduced/figures
```

The table script writes four CSV files corresponding to Table 1, Table 2, and Parts A and B of Table 3. The figure script writes three PNG files containing the data-driven content of Figures 2, 3, and 5.

Figure 1 is conceptual and is not regenerated from analysis data. Figure 4 contains representative image overlays and is not regenerated because the required RGB images, annotations, and prediction masks are intentionally absent from this public processed-data package.

## Scope

The primary task-aligned numerical analysis is reproduced from processed fixed-model outputs. Date-stratified tables and figures are regenerated from the included date-level summaries in `results/date_level_summary.csv`; they are not recomputed from per-image temporal outputs, which are not included. The package does not reproduce model training or inference and contains no raw data, model weights, inference code, or temporal per-image outputs. Development experiments, private working materials, and unrelated datasets are outside the scope of this repository.
