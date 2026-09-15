# Manuscript reproduction map

All commands read stored processed results. They do not refit metrics or repeat scientific experiments.

| Manuscript item | Public source | Reproduction output |
|---|---|---|
| Table 1 | `config/candidates.csv` | `table1_candidates.csv` |
| Table 2 | `config/populations.csv` and `splits/` | `table2_populations.csv` |
| Table 3 | Stage-1/Stage-2 `summary.json` profiles and stored quantiles | `table3_bonn_profiles.csv` |
| Table 4A/B | Stored within-population associations and cross-stage persistence | `table4a_rank_associations.csv`, `table4b_rank_persistence.csv` |
| Table 5A/B | Stage-2 question outcomes and component date support | `table5a_confirmation_outcomes.csv`, `table5b_date_support.csv` |
| Table 6 | External `summary.json` | `table6_external_profiles.csv` |
| Table 7A/B/C | M3 `summary.json` | `table7a_m3_representations.csv`, `table7b_m3_saved_intervals.csv`, `table7c_m3_total_vegetation.csv` |
| Figure 1 | Conceptual definitions in the protocol and manuscript | Not regenerated; integrated conceptual/image illustration |
| Figure 2 | Prespecified frame-188 comparison, described in the protocol | Not regenerated; native RGB, reference and seven prediction maps are not distributed |
| Figure 3 | Stage-1/Stage-2 pooled profiles | `figure3a`–`figure3d` |
| Figure 4 | Stage-1 exploratory tail summary; Stage-2 quantiles and stored date/pooled ranks | `figure4a`, `figure4b`, `figure4_colorbar`, `figure4c_winners` |
| Figure 5 | External pooled profiles | `figure5a`–`figure5d` |
| Figure 6 | M3 global confusion counts and pooled FP/FN in the three populations | `figure6a_matrix`, `figure6b_composition`, `figure6c_pooled` |
| Figure 7 | Prespecified M3 case identities and rules | Not regenerated; RGB, annotation and prediction/error maps are not distributed |

Table files are CSVs, with the displayed precision used in the manuscript. Full precision remains in the JSON records. Table 5 exports the recorded component outcomes, not a new interpretation of partial confirmation. Each plotted panel is exported as PDF and PNG. LaTeX captions and panel assembly are outside these portable renderers.

The Figure 4a tails are retrospective/exploratory; Figure 4b uses the prespecified Stage-2 quantiles. White bold numeric labels and their dark strokes are uniform. Figure 4a winner outlines are black with a common width. Figure 4c reads the stored date rankings and retains ties rather than reranking rounded values.

## Remaining gaps

- The package does not reproduce training or inference. Candidate weights and exact candidate-specific training-membership records are not supplied. Configuration metadata alone do not reconstruct those models.
- Figures 1, 2 and 7 cannot be fully regenerated from this package. Obtain source imagery/annotations from the dataset providers; the corresponding frozen model prediction maps would additionally be required for Figures 2 and 7. The illustrative images do not establish comparative superiority.
- Saved M3 confidence limits are exported directly. No public command regenerates the original 2,000-resample calculation. The previously public M3 sequence/per-image records remain available for inspection.
- Detailed internal freeze/audit histories and private author-supplied acquisition metadata are not public. The cohort IDs and processed results support the reported population definitions, but do not establish independent farms, fields or environmental sampling units.
