# Processed-record definitions

## Shared conventions

- Candidate IDs are M1–M7 in the fixed order in `config/candidates.csv`. Stored rank vectors are ordered M1 through M7; rank 1 is best.
- Fractions, IoUs and error magnitudes in JSON/per-image CSVs use a 0–1 scale. Display scripts multiply by 100. An IoU becomes a percentage; a crop-fraction error becomes percentage points (pp).
- Confusion matrices use reference rows and predicted columns. `N_valid` is the per-image valid-pixel denominator; `N_valid_pooled` is its population total. External reference label 255 is excluded from every metric.
- Bias, MAE and RMSE are image-weighted. Pooled FP/FN rates are pixel-weighted. They are not interchangeable when image sizes/valid masks differ.
- Quantiles, correlations, ranks, exceedances and intervals are saved results. No release command computes new estimates of them. Undefined external five-class results are absent, not zero.

## Summary JSONs

`results/stage1/summary.json` contains seven `pooled_metrics`, seven exploratory `tail_summary` entries, six `rank_correlations`, seven `directional_summary` entries and stored primary `rankings`. The separate `exploratory_rankings` contains the saved functional-mIoU, median and maximum ranks from the post-Stage-1 records. `quantiles_linear` uses probability-string keys `0.5`, `0.75`, `0.9`, `0.95`, `0.99`; `maximum_absolute_error` is separate. Threshold counts are strictly greater than the stated fraction. Stage-1 tails and associations are retrospective/exploratory.

`results/stage2/summary.json` contains seven pooled profiles, 63 model/date profiles, their stored rankings, six pooled rank associations, seven cross-stage persistence records, six confirmation-question groups and 20 component date-support records. Each support record preserves both the number of supporting dates and the nine original Boolean outcomes. A tied zero exceedance does not satisfy a strict inequality. `absolute_error_quantiles` uses the same probability keys as Stage 1. April 29 remains descriptive.

`results/external/summary.json` contains seven binary crop/noncrop profiles, stored rankings and rank associations, priority costs and prespecified question outcomes. `signed_bias`, `mae` and `rmse` correspond to the Bonn fields `crop_fraction_bias`, `crop_fraction_mae` and `crop_fraction_rmse`. Stored external tails include P50, P90, P95 and maximum, plus counts above 0.5, 1, 5 and 10 pp. External P75/P99 are not invented. `crop_TP`, `crop_FP`, `crop_FN`, `crop_TN` and `N_valid_pooled` are integer pooled counts.

`results/m3/summary.json` contains the three saved semantic representation profiles, M3 hard/soft estimates and their stored 95% confidence limits, the three matched total-vegetation MAEs, the 5×5 global confusion matrix, and the two Figure 7 case identities. M3 intervals use the 429-image population and eight sequences. The total-vegetation estimates use 185 images, including five in-domain references. Representation values retain source CSV precision; blank subclass fields mean not applicable.

## Per-image CSVs

`results/stage1/per_image_records.csv` and `results/stage2/per_image_records.csv` contain one row per candidate/image, with candidate ID, source image ID, public Bonn acquisition date, valid-pixel count, reference/predicted hard crop fraction, signed error, crop FP/FN, and all 25 saved five-class confusion cells. Cell columns have the form `true_crop_pred_soil`. Counts are direct copies of stored integer arrays; model outputs have not been regenerated.

`results/external/per_image_records.csv` contains candidate/image ID, valid pixels, reference/predicted hard crop fractions, signed and absolute errors, and the four binary confusion counts. No GPS, author-supplied timestamps, model paths, checkpoint files or runtime metadata are included.

The existing top-level M3 CSVs retain their original schemas and bytes. `per_image_confusion.csv` additionally contains probability-functional counts; `crop_fraction_records.csv` contains soft estimates and sequence/frame IDs; `task_aligned_errors.csv` preserves the disjoint semantic-error components; `date_level_summary.csv` contains the M3-specific 185-image temporal summaries. They are supplementary processed records for Table 7 and directional interpretation, not a seven-model Stage-2 leaderboard.

## Cohorts and provenance

The Stage-1 IDs are the unchanged `splits/may23_primary_429.csv`. The new `splits/stage2_180.csv` lists exactly the frozen cross-date cohort; it is also the cross-date subset of the existing `splits/temporal_185.csv`. Neither population was selected anew for this release.

`splits/cropandweed_48.csv` lists the frozen public recording-set/session/image identifiers, eligible-frame count, selected lower-median index/frame and native mask dimensions. It comes from the cohort fixed before inference, not the later author-supplied acquisition metadata. No later timestamp, GPS, or year-range crosswalk is included.

Saved data originate from the completed Stage-1, prespecified Stage-2, prespecified external and M3-specific evaluation records. The release preserves the reported values and provides a checksum for each public file. Machine-specific run paths and internal audit histories are not required to use these records and are not distributed.
