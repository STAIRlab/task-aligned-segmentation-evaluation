# Companion-package cleanup

The package was refreshed for the current seven-model manuscript while preserving Git history.

| Action | Files | Reason |
|---|---|---|
| Removed whole files | None | All pre-existing tracked data still support the secondary M3 analyses |
| Replaced superseded contents | `README.md`, `CITATION.cff`, `config/evaluation_protocol.yaml` | Current title, populations, terminology and reproducibility scope |
| Replaced superseded command behavior | `scripts/reproduce_tables.py`, `scripts/reproduce_main_figures.py` | Current Tables 1–7 and Figures 3–6; stored intervals replace automatic bootstrap execution |
| Clarified license scope | `LICENSE-DATA` | Distinguish Bonn-derived materials from noncommercial CropAndWeed-derived records |

Retained files that may appear to describe a narrower analysis:

- `results/per_image_confusion.csv`: M3 five-class and probability-functional counts, needed to inspect the secondary representation checks.
- `results/crop_fraction_records.csv`: M3 hard/soft crop fractions and sequence/frame fields supporting the saved estimator summaries.
- `results/task_aligned_errors.csv`: M3 within-functional and crop-boundary error accounting.
- `results/date_level_summary.csv`: M3 temporal and matched total-vegetation summaries, distinct from the seven-model Stage-2 population.
- `splits/may23_primary_429.csv` and `splits/temporal_185.csv`: original public population identities; the 185-image scope remains valid for the secondary estimand analysis.
- `LICENSE-CODE` and `.gitignore`: still applicable to the current package.

Earlier script implementations remain in Git history. No ambiguous-purpose tracked file was deleted.
