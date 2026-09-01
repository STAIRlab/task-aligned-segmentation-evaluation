#!/usr/bin/env python3
"""Reproduce the numerical content of manuscript Tables 1--3."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[1]
FIVE_LABELS = ("soil_background", "crop", "weed", "dicot", "grass")
FUNCTIONAL_LABELS = ("soil", "crop", "functional_weed")
MAY23_SPLIT_FIELDS = (
    "image_id",
    "acquisition_date",
    "model_development_split",
)
TEMPORAL_SPLIT_FIELDS = (
    "image_id",
    "acquisition_date",
    "generalization_role",
    "date_specific_generalization_claim_supported",
    "sequence_id",
    "frame_index",
)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require_fields(
    rows: list[dict[str, str]], expected: tuple[str, ...], *, label: str
) -> None:
    if not rows:
        raise RuntimeError(f"{label} is empty")
    actual = tuple(rows[0])
    if actual != expected:
        raise RuntimeError(f"{label} fields differ from the public schema: {actual}")


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def number(value: float) -> str:
    return format(float(value), ".17g")


def load_protocol() -> dict:
    with (ROOT / "config" / "evaluation_protocol.yaml").open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def confusion_arrays(rows: list[dict[str, str]]) -> tuple[np.ndarray, np.ndarray]:
    five = np.asarray(
        [
            [
                [int(row[f"true_{truth}_pred_{prediction}_count"]) for prediction in FIVE_LABELS]
                for truth in FIVE_LABELS
            ]
            for row in rows
        ],
        dtype=np.int64,
    )
    probability = np.asarray(
        [
            [
                [
                    int(row[f"prob_functional_true_{truth}_pred_{prediction}_count"])
                    for prediction in FUNCTIONAL_LABELS
                ]
                for truth in FUNCTIONAL_LABELS
            ]
            for row in rows
        ],
        dtype=np.int64,
    )
    n_valid = np.asarray([int(row["n_valid_pixels"]) for row in rows], dtype=np.int64)
    if not np.array_equal(five.sum(axis=(1, 2)), n_valid):
        raise RuntimeError("Five-class confusion totals do not match n_valid_pixels")
    if not np.array_equal(probability.sum(axis=(1, 2)), n_valid):
        raise RuntimeError("Probability-functional confusion totals do not match n_valid_pixels")
    return five, probability


def hard_functional_confusion(five: np.ndarray) -> np.ndarray:
    mapping = np.asarray([0, 1, 2, 2, 2], dtype=np.int64)
    result = np.zeros((3, 3), dtype=np.int64)
    for true_index in range(5):
        for predicted_index in range(5):
            result[mapping[true_index], mapping[predicted_index]] += five[
                true_index, predicted_index
            ]
    return result


def metric_bundle(confusion: np.ndarray) -> dict[str, object]:
    matrix = np.asarray(confusion, dtype=np.int64)
    true_total = matrix.sum(axis=1, dtype=np.int64)
    predicted_total = matrix.sum(axis=0, dtype=np.int64)
    true_positive = np.diag(matrix).astype(np.float64)
    false_negative = true_total - true_positive
    false_positive = predicted_total - true_positive
    iou_denominator = true_positive + false_positive + false_negative
    f1_denominator = 2.0 * true_positive + false_positive + false_negative
    iou = np.divide(
        true_positive,
        iou_denominator,
        out=np.full(true_positive.shape, np.nan),
        where=iou_denominator > 0,
    )
    recall = np.divide(
        true_positive,
        true_total,
        out=np.full(true_positive.shape, np.nan),
        where=true_total > 0,
    )
    f1 = np.divide(
        2.0 * true_positive,
        f1_denominator,
        out=np.full(true_positive.shape, np.nan),
        where=f1_denominator > 0,
    )
    return {
        "pa": float(true_positive.sum() / matrix.sum()),
        "mpa": float(np.nanmean(recall)),
        "miou": float(np.nanmean(iou)),
        "macro_f1": float(np.nanmean(f1)),
        "class_iou": iou,
        "n_valid": int(matrix.sum()),
    }


def summary_metrics(reference: np.ndarray, prediction: np.ndarray) -> dict[str, float]:
    signed = prediction - reference
    absolute = np.abs(signed)
    return {
        "bias": float(np.mean(signed, dtype=np.float64)),
        "mae": float(np.mean(absolute, dtype=np.float64)),
        "rmse": float(np.sqrt(np.mean(np.square(signed), dtype=np.float64))),
        "median_absolute_error": float(np.median(absolute)),
    }


def cluster_bootstrap(
    reference: np.ndarray,
    prediction: np.ndarray,
    sequence_ids: np.ndarray,
    *,
    resamples: int,
    seed: int,
    random_number_generator: str,
) -> dict[str, tuple[float, float, float]]:
    unique_sequences = np.unique(sequence_ids)
    if unique_sequences.size < 2 or np.any(sequence_ids == ""):
        raise RuntimeError("The primary analysis requires complete sequence-cluster support")
    if random_number_generator != "PCG64":
        raise RuntimeError("This release reproducer requires the declared PCG64 generator")
    generator = np.random.Generator(np.random.PCG64(seed))
    samples = {
        name: np.empty(resamples, dtype=np.float64)
        for name in ("bias", "mae", "rmse", "median_absolute_error")
    }
    for draw_index in range(resamples):
        selected_sequences = generator.choice(
            unique_sequences, size=unique_sequences.size, replace=True
        )
        selected = np.concatenate(
            [np.flatnonzero(sequence_ids == sequence) for sequence in selected_sequences]
        )
        values = summary_metrics(reference[selected], prediction[selected])
        for name, value in values.items():
            samples[name][draw_index] = value
    point = summary_metrics(reference, prediction)
    output: dict[str, tuple[float, float, float]] = {}
    for name, values in samples.items():
        try:
            low, high = np.quantile(values, (0.025, 0.975), method="linear")
        except TypeError:
            low, high = np.quantile(values, (0.025, 0.975), interpolation="linear")
        output[name] = (point[name], float(low), float(high))
    return output


def reproduce_table1(protocol: dict, output_dir: Path) -> None:
    may23 = read_rows(ROOT / "splits" / "may23_primary_429.csv")
    temporal = read_rows(ROOT / "splits" / "temporal_185.csv")
    require_fields(may23, MAY23_SPLIT_FIELDS, label="May 23 split")
    require_fields(temporal, TEMPORAL_SPLIT_FIELDS, label="Temporal split")
    population = protocol["population"]
    may23_config = population["may23_model_development"]
    temporal_config = population["date_stratified_analysis"]
    if len(may23) != may23_config["primary_evaluation_images"]:
        raise RuntimeError("May 23 split count differs from the protocol")
    if len(temporal) != temporal_config["analysis_images"]:
        raise RuntimeError("Temporal split count differs from the protocol")
    if any(
        row["model_development_split"] != "heldout_model_selection" for row in may23
    ):
        raise RuntimeError("May 23 split contains an unexpected model-development role")
    by_date = Counter(row["acquisition_date"] for row in temporal)
    ordered_dates = [
        value.isoformat() if hasattr(value, "isoformat") else str(value)
        for value in temporal_config["prespecified_dates"]
    ]
    date_counts = "; ".join(f"{date}: {by_date[date]}" for date in ordered_dates)
    rows = [
        {"section": "Dataset", "item": "Source dataset", "value": "2016 Sugar Beets Dataset, Bonn, Germany", "unit": "definition"},
        {"section": "May 23 population", "item": "Model-development total", "value": may23_config["total_images"], "unit": "images"},
        {"section": "May 23 population", "item": "Training", "value": may23_config["training_images"], "unit": "images"},
        {"section": "May 23 population", "item": "Held-out/model-selection", "value": may23_config["heldout_model_selection_images"], "unit": "images"},
        {"section": "May 23 population", "item": "Primary evaluation subset", "value": len(may23), "unit": "images"},
        {"section": "Temporal population", "item": "Date-stratified analysis total", "value": len(temporal), "unit": "images"},
        {"section": "Temporal population", "item": "Eligible unique images by date", "value": date_counts, "unit": "images"},
        {"section": "Temporal population", "item": "Known May 23 training-overlap exclusions", "value": temporal_config["may23_training_overlap_excluded"], "unit": "images"},
        {"section": "Evaluation", "item": "Evaluation grid width", "value": protocol["evaluation_grid"]["width_pixels"], "unit": "pixels"},
        {"section": "Evaluation", "item": "Evaluation grid height", "value": protocol["evaluation_grid"]["height_pixels"], "unit": "pixels"},
        {"section": "Uncertainty", "item": "Bootstrap resamples", "value": protocol["bootstrap"]["resamples"], "unit": "resamples"},
    ]
    write_rows(output_dir / "table1_dataset_evaluation.csv", ["section", "item", "value", "unit"], rows)


def reproduce_table2(output_dir: Path) -> None:
    rows = read_rows(ROOT / "results" / "per_image_confusion.csv")
    if len(rows) != 429:
        raise RuntimeError("Expected 429 per-image confusion rows")
    five_per_image, probability_per_image = confusion_arrays(rows)
    five = five_per_image.sum(axis=0, dtype=np.int64)
    hard = hard_functional_confusion(five)
    probability = probability_per_image.sum(axis=0, dtype=np.int64)
    metrics = {
        "five_class": metric_bundle(five),
        "hard_functional": metric_bundle(hard),
        "probability_functional": metric_bundle(probability),
    }
    output_rows: list[dict[str, object]] = []
    for name in ("five_class", "hard_functional", "probability_functional"):
        bundle = metrics[name]
        iou = np.asarray(bundle["class_iou"], dtype=np.float64)
        output_rows.append(
            {
                "representation": name,
                "pa_fraction": number(bundle["pa"]),
                "mpa_fraction": number(bundle["mpa"]),
                "miou_fraction": number(bundle["miou"]),
                "macro_f1_fraction": number(bundle["macro_f1"]),
                "crop_iou_fraction": number(iou[1]),
                "soil_iou_fraction": number(iou[0]),
                "weed_iou_fraction": number(iou[2]) if name == "five_class" else "",
                "dicot_iou_fraction": number(iou[3]) if name == "five_class" else "",
                "grass_iou_fraction": number(iou[4]) if name == "five_class" else "",
                "functional_weed_iou_fraction": number(iou[2]) if name != "five_class" else "",
                "n_valid_pixels": bundle["n_valid"],
            }
        )
    write_rows(
        output_dir / "table2_semantic_performance.csv",
        list(output_rows[0]),
        output_rows,
    )


def reproduce_table3(protocol: dict, output_dir: Path) -> None:
    crop_rows = read_rows(ROOT / "results" / "crop_fraction_records.csv")
    date_rows = read_rows(ROOT / "results" / "date_level_summary.csv")
    if len(crop_rows) != 429 or len(date_rows) != 10:
        raise RuntimeError("Expected 429 primary rows and 10 date summaries")
    reference = np.asarray(
        [float(row["reference_crop_fraction"]) for row in crop_rows], dtype=np.float64
    )
    sequence_ids = np.asarray([row["sequence_id"] for row in crop_rows], dtype=str)
    bootstrap = protocol["bootstrap"]
    part_a: list[dict[str, object]] = []
    for method, field in (("hard", "hard_crop_fraction"), ("soft", "soft_crop_fraction")):
        prediction = np.asarray([float(row[field]) for row in crop_rows], dtype=np.float64)
        summary = cluster_bootstrap(
            reference,
            prediction,
            sequence_ids,
            resamples=int(bootstrap["resamples"]),
            seed=int(bootstrap["random_seed"]),
            random_number_generator=str(bootstrap["random_number_generator"]),
        )
        row: dict[str, object] = {
            "method": method,
            "n_images": len(crop_rows),
            "n_sequences": len(np.unique(sequence_ids)),
        }
        for metric in ("bias", "mae", "rmse", "median_absolute_error"):
            estimate, low, high = summary[metric]
            row[f"{metric}_fraction"] = number(estimate)
            row[f"{metric}_ci_low_fraction"] = number(low)
            row[f"{metric}_ci_high_fraction"] = number(high)
        part_a.append(row)
    write_rows(output_dir / "table3a_may23_crop_fraction.csv", list(part_a[0]), part_a)

    part_b_fields = [
        "acquisition_date",
        "n_images",
        "mean_reference_crop_fraction",
        "crop_iou_fraction",
        "hard_bias_fraction",
        "hard_mae_fraction",
        "hard_rmse_fraction",
        "date_specific_generalization_claim_supported",
    ]
    part_b = [
        {
            "acquisition_date": row["acquisition_date"],
            "n_images": row["eligible_image_count"],
            "mean_reference_crop_fraction": row["mean_reference_crop_fraction"],
            "crop_iou_fraction": row["crop_iou"],
            "hard_bias_fraction": row["hard_crop_bias"],
            "hard_mae_fraction": row["hard_crop_mae"],
            "hard_rmse_fraction": row["hard_crop_rmse"],
            "date_specific_generalization_claim_supported": row[
                "date_specific_generalization_claim_supported"
            ],
        }
        for row in date_rows
    ]
    write_rows(output_dir / "table3b_date_stratified.csv", part_b_fields, part_b)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reproduced/tables"),
        help="Directory for regenerated CSV tables (default: reproduced/tables)",
    )
    args = parser.parse_args()
    protocol = load_protocol()
    reproduce_table1(protocol, args.output_dir)
    reproduce_table2(args.output_dir)
    reproduce_table3(protocol, args.output_dir)
    print(f"Wrote four reproduced table files to {args.output_dir}")


if __name__ == "__main__":
    main()
