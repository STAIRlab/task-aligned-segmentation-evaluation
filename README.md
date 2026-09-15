# Task-aligned model selection and measurement validity for segmentation-derived crop canopy fraction

**Fan Hu and Khalid M. Mosalam**

Companion processed-data package for the manuscript of the same title. It supports comparison of seven SegFormer MiT-B5 candidates (M1–M7) under semantic/overlap fidelity, average crop-fraction error, tail sensitivity and directional FP/FN burden. The exact hard-error identity is

`FGCC_hard − FGCC_reference = (FP_crop − FN_crop) / N_valid`.

## What this package reproduces

The scripts export the numerical content of **Tables 1–7** and render the quantitative panels of **Figures 3–6** from the saved results. Stored per-image confusion/count records support inspection of the underlying measurements. The M3 representation, hard/soft estimator and matched total-vegetation checks are a secondary component.

This is a processed-results package, not a training archive. It contains no model weights, raw imagery, raw annotations, population prediction masks or inference environment. Commands below do not train models, infer predictions, calculate new metrics, estimate quantiles/correlations, or rerun bootstrap intervals. Figure 1 is conceptual; the image/mask-based Figures 2 and 7 are not regenerated here. See the [figure/table map and remaining gaps](docs/reproduction_map.md).

## Evaluation populations

| Population | Candidates | Images | Role |
|---|---|---:|---|
| Stage 1 | M1–M7 | 429 | May 23, 2016 development/model-selection population; retrospective comparison |
| Stage 2 | M1–M7 | 180 | Prespecified cross-date confirmation: 20 images on each of nine dates |
| CropAndWeed | M1–M7 | 48 | Prespecified Application cohort, one image per eligible acquisition session |
| M3 secondary temporal checks | M3 | 185 | Same 180 cross-date images plus five May 23 in-domain references |

Stage 1 shares the M3-specific 429-image population; it is not an independent test set. Stage 2 excludes the five in-domain references, and the 15 temporal candidates with known May 23 training overlap remain excluded. April 29 lacks the required sequence/window support and remains descriptive. Acquisition dates are not independent sites or phenological stages.

External selection used the lower-median eligible frame by numeric frame order in each session, fixed before model outputs were examined. The binary reference labels treat source IDs 7–12 as crop and 255 as invalid; no external five-class mIoU is claimed. Dataset-author correspondence confirmed no repeated Application acquisition on the same site or plot (D. Steininger, personal communication, September 2026). This does not establish statistical independence of farms, environments or sampling units.

## Candidate definitions

All candidates use SegFormer MiT-B5 and five output classes: soil/background, crop, weed, dicot and grass. Weed, dicot and grass merge into functional weed; crop membership is preserved.

| Candidate | Epochs | Batch size | Learning rate |
|---|---:|---:|---:|
| M1 | 2 | 2 | 6e-5 |
| M2 | 10 | 2 | 6e-5 |
| M3 | 10 | 1 | 6e-5 |
| M4 | 10 | 2 | 1e-5 |
| M5 | 10 | 1 | 1e-5 |
| M6 | 10 | 2 | 1e-4 |
| M7 | 10 | 1 | 1e-4 |

Numbering is fixed across populations. These configurations are not a controlled factorial ablation or independent training replicates. M3 also supplies the detailed semantic-error and estimator examples. The [protocol](config/evaluation_protocol.yaml) records evaluation geometry, targets and interpretation; it does not supply a training recipe.

## Organization

| Path | Contents |
|---|---|
| `config/` | Candidate definitions, population roles and evaluation protocol |
| `splits/` | Public image/session identifiers for the 429-, 180-, 48- and M3-specific 185-image populations |
| `results/stage1/` | Seven-model profiles, exploratory tails/rank associations, directional summaries and 3,003 model–image records |
| `results/stage2/` | Pooled/date profiles and rankings, confirmation outcomes, date support and 1,260 model–image records |
| `results/external/` | CropAndWeed binary profiles, tails, ranks, directional results and 336 model–image records |
| `results/m3/summary.json` | Saved representation metrics, crop-fraction intervals, total-vegetation MAEs and aggregate confusion counts |
| Existing top-level `results/*.csv` | M3 per-image hard/soft/probability-functional and date-level records retained for secondary checks |
| `scripts/` | Integrity checks, table export and quantitative-panel rendering |
| `docs/` | Data dictionary, manuscript map and concise cleanup manifest |

Each model–image record represents a stored evaluation output, not an independent experimental replicate. Summaries retain unrounded values. Fractions use a 0–1 scale; display scripts multiply by 100 for percentages or percentage points. See the [data dictionary](docs/data_dictionary.md).

## Reproduce tables and quantitative panels

Use Python 3.8 or newer. Table export and integrity checking use the standard library; plots additionally require NumPy and Matplotlib:

```bash
python -m pip install -r requirements.txt
python scripts/verify_package.py
python scripts/reproduce_tables.py --output-dir reproduced/tables
python scripts/reproduce_main_figures.py --output-dir reproduced/figures
```

Plot rendering was checked with Python 3.8.12, NumPy 1.24.3 and Matplotlib 3.4.3; table export was also checked with Python 3.10.

The table command writes 11 CSV components for the seven manuscript tables. The plot command writes 15 PDF panels and matching PNGs for Figures 3–6, using the manuscript plotting functions with portable data paths. It preserves the common candidate colors and final Figure 4 white bold labels with dark strokes. Subcaptions and overall captions remain manuscript composition, so panel files are not complete LaTeX page layouts. Use `--figures 4` to render only Figure 4's four components.

Confidence limits, quantiles, correlations, ranks and confirmation outcomes are read from the stored records. Display rounding and count-to-percentage conversion do not re-estimate those results. Generated files go to the ignored `reproduced/` directory. PDF bytes can differ with fonts/library versions; the numerical inputs are fixed by [checksums.sha256](checksums.sha256).

## Source datasets and licenses

- **Sugar Beets 2016:** obtain RGB images and annotations from the [University of Bonn StachnissLab dataset page](https://www.ipb.uni-bonn.de/data/sugarbeets2016/). The source dataset uses CC BY-SA 4.0. Cite Chebrolu et al. (2017), *Agricultural robot dataset for plant classification, localization and mapping on sugar beet fields*, [doi:10.1177/0278364917720510](https://doi.org/10.1177/0278364917720510).
- **CropAndWeed:** obtain the dataset and download utilities from the [dataset authors' repository](https://github.com/cropandweed/cropandweed-dataset). Cite Steininger et al. (2023), *The CropAndWeed Dataset: A Multi-Modal Learning Approach for Efficient Crop and Weed Manipulation*, WACV, [paper](https://openaccess.thecvf.com/content/WACV2023/html/Steininger_The_CropAndWeed_Dataset_A_Multi-Modal_Learning_Approach_for_Efficient_Crop_WACV_2023_paper.html). Its [license](https://github.com/cropandweed/cropandweed-dataset/blob/main/LICENCE) restricts use to noncommercial purposes and does not permit redistribution of the source dataset. Only abstract counts/statistical results and public identifiers are included here.

Scripts use the BSD 3-Clause license ([LICENSE-CODE](LICENSE-CODE)). Bonn-derived processed materials use CC BY-SA 4.0; CropAndWeed-derived records retain the source's noncommercial conditions and are not relicensed as CC BY-SA. See [LICENSE-DATA](LICENSE-DATA) for the distinct scopes. Raw source data are not redistributed.

## Citation and limitations

Please cite Fan Hu and Khalid M. Mosalam, *Task-aligned model selection and measurement validity for segmentation-derived crop canopy fraction*, and identify the repository commit used. [CITATION.cff](CITATION.cff) supplies repository metadata; no manuscript publication venue or DOI is asserted here.

Stage-1 tails and within-population rank associations are retrospective/exploratory. Stage-2 and external questions were prespecified relative to their evaluations; all six Stage-2 question groups were only partially confirmed. Rank coefficients are descriptive across seven candidates, without p-values. M3 confidence intervals concern its development/selection population, not comparative model uncertainty. Both datasets concern sugar beet; the external target is binary, and its full-frame resizing changes aspect ratio. The package supports neither agronomic/deployment validation nor independent-farm inference.

Private correspondence and author-supplied acquisition timestamps/GPS are excluded. Source training-membership records, private weights and internal submission/audit materials are also excluded. The public cohort identifiers do not contain the later author-supplied metadata.
