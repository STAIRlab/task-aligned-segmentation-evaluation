#!/usr/bin/env python3
"""Paired descriptive uncertainty from frozen per-image records; no inference.

Requires Python >=3.9 and NumPy >=1.22. Run from any working directory.
The default reads results/paired_uncertainty/ in this repository and writes to
reproduced/paired_uncertainty/. No private project inputs are required.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform

import numpy as np


SEED = 20260924
N_RESAMPLES = 5000
ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "results/paired_uncertainty"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def metric_values(rows, models, external=False):
    """Compute the original metrics, with pooled counts for external crop IoU."""
    result = {}
    for model in models:
        error = np.array([float(r[f"{model}_signed_error"]) for r in rows], dtype=np.float64)
        require(np.isfinite(error).all(), "Nonfinite signed error")
        values = {"MAE": float(np.mean(np.abs(error))), "RMSE": float(np.sqrt(np.mean(error**2)))}
        if external:
            tp, fp, fn = (sum(int(r[f"{model}_{c}"]) for r in rows) for c in ("TP", "FP", "FN"))
            require(tp + fp + fn > 0, "Undefined pooled crop IoU")
            values = {"crop_IoU": tp / (tp + fp + fn), **values}
        else:
            values["P99_AE"] = float(np.quantile(np.abs(error), 0.99, method="linear"))
        result[model] = values
    return result


def bootstrap(rows, models, group_field, rng, external=False):
    """Sample K whole groups, duplicating all their images, paired across models."""
    group_ids = sorted({r[group_field] for r in rows})
    groups = [[i for i, row in enumerate(rows) if row[group_field] == group] for group in group_ids]
    metrics = tuple(metric_values(rows, models, external)[models[0]])
    draws = np.empty((N_RESAMPLES, len(metrics)), dtype=np.float64)
    n_images = np.empty(N_RESAMPLES, dtype=np.int64)
    for replicate in range(N_RESAMPLES):
        chosen = rng.integers(0, len(groups), size=len(groups))
        indices = [i for group in chosen for i in groups[group]]
        paired_rows = [rows[i] for i in indices]
        values = metric_values(paired_rows, models, external)
        draws[replicate] = [values[models[0]][metric] - values[models[1]][metric] for metric in metrics]
        n_images[replicate] = len(indices)
    return metrics, draws, n_images


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reproduced/paired_uncertainty")
    parser.add_argument("--compact-input-dir", type=Path, default=INPUT_DIR,
                        help="Directory containing the paired input CSVs and analysis_manifest.json")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    require(output != args.compact_input_dir.resolve(), "Choose an output directory separate from the published inputs")
    saved = json.loads((args.compact_input_dir / "analysis_manifest.json").read_text())
    for name in ("paired_inputs_stage1.csv", "paired_inputs_external.csv"):
        require(sha256(args.compact_input_dir / name) == saved["output_sha256"][name], "Compact input hash mismatch")
    stage_rows = read_csv(args.compact_input_dir / "paired_inputs_stage1.csv")
    external_rows = read_csv(args.compact_input_dir / "paired_inputs_external.csv")
    metadata = saved["input_provenance"]

    reference = metadata["frozen_reference_metrics_fraction"]
    streams = np.random.SeedSequence(SEED).spawn(2)
    contrasts, replicates, checks = [], [{"replicate": i + 1} for i in range(N_RESAMPLES)], []
    populations = [("stage1", stage_rows, ("M1", "M4"), "sequence_id", False),
                   ("external", external_rows, ("M1", "M5"), "session_id", True)]
    for stream, (population, rows, models, group_field, external) in zip(streams, populations):
        values = metric_values(rows, models, external)
        for model in models:
            for metric, computed in values[model].items():
                delta = computed - reference[population][model][metric]
                require(abs(delta) < 1e-14, f"Frozen point estimate mismatch: {population}/{model}/{metric}")
                checks.append({"population": population, "model": model, "metric": metric,
                               "computed_minus_frozen_fraction": delta})
        metrics, draws, image_counts = bootstrap(rows, models, group_field,
                                                 np.random.Generator(np.random.PCG64(stream)), external)
        intervals = np.quantile(draws, [0.025, 0.975], axis=0, method="linear")
        for j, metric in enumerate(metrics):
            # Retain the exact frozen point estimates; do not replace their summaries.
            first, second = (reference[population][model][metric] for model in models)
            difference = first - second
            low, high = float(intervals[0, j]), float(intervals[1, j])
            contrasts.append({"population": population, "contrast": f"{models[0]} - {models[1]}",
                              "metric": metric, "model_1_estimate_fraction": first,
                              "model_2_estimate_fraction": second, "observed_difference_fraction": difference,
                              "ci_low_fraction": low, "ci_high_fraction": high,
                              "observed_difference_pp": 100 * difference,
                              "ci_low_pp": 100 * low, "ci_high_pp": 100 * high,
                              "interval_includes_zero": low <= 0 <= high,
                              "resampling_unit": group_field, "n_units": len({r[group_field] for r in rows}),
                              "n_images": len(rows), "n_resamples": N_RESAMPLES, "root_seed": SEED,
                              "stream_spawn_key": str(stream.spawn_key[0])})
        for i, row in enumerate(replicates):
            row[f"{population}_n_images"] = int(image_counts[i])
            for j, metric in enumerate(metrics):
                row[f"{population}_{metric}_difference_fraction"] = float(draws[i, j])

    output.mkdir(parents=True, exist_ok=True)
    outputs = {"paired_inputs_stage1.csv": stage_rows, "paired_inputs_external.csv": external_rows,
               "paired_contrasts.csv": contrasts, "bootstrap_replicates.csv": replicates}
    for name, rows in outputs.items():
        write_csv(output / name, rows)
    manifest = {
        "analysis": "Post-KM-review paired comparative uncertainty; retrospective and descriptive",
        "script_sha256": sha256(Path(__file__)),
        "source_script_sha256": saved["source_script_sha256"],
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "bootstrap": {"replicates_per_population": N_RESAMPLES, "root_seed": SEED,
                      "prng": "numpy.random.Generator(PCG64)",
                      "streams": "SeedSequence(root_seed).spawn(2): stage1=(0,), external=(1,)",
                      "sampling": "Sample K of K lexicographically ordered observed groups with replacement; include every image in each sampled group, including duplicates. Both models receive identical draws.",
                      "aggregation": "Image-weighted MAE/RMSE and linearly interpolated image-error P99; external crop IoU from pooled integer TP/(TP+FP+FN).",
                      "interval": "Two-sided 95% percentile: numpy.quantile at 0.025 and 0.975, method=linear",
                      "units": "Fractions in stored inputs/replicates; both fractions and percentage-point differences in paired_contrasts.csv",
                      "maximum_error": "Frozen descriptive observations only; no bootstrap interval computed."},
        "input_provenance": metadata, "frozen_point_estimate_checks": checks,
        "interpretation": "Conditional on the fixed models and observed acquisition cohort; eight Stage-1 sequences do not undo model-selection reuse. External sessions are not asserted to be statistically independent population sampling units. No p-values or deployment bounds.",
        "output_sha256": {name: sha256(output / name) for name in outputs}}
    (output / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    for row in contrasts:
        print(f"{row['population']} {row['contrast']} {row['metric']}: "
              f"{row['observed_difference_pp']:.15g} pp "
              f"[{row['ci_low_pp']:.15g}, {row['ci_high_pp']:.15g}]")


if __name__ == "__main__":
    main()
