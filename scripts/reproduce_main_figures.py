#!/usr/bin/env python3
"""Reproduce the manuscript's quantitative analysis figures from public CSVs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
FIVE_LABELS = ("soil_background", "crop", "weed", "dicot", "grass")
FIVE_DISPLAY = ("soil/background", "crop", "weed", "dicot", "grass")
FUNCTIONAL_LABELS = ("soil", "crop", "functional_weed")
BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
PURPLE = "#7A5195"
GRAY = "#6B7378"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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
    denominator = true_positive + false_positive + false_negative
    iou = np.divide(
        true_positive,
        denominator,
        out=np.full(true_positive.shape, np.nan),
        where=denominator > 0,
    )
    return {
        "miou": float(np.nanmean(iou)),
        "crop_iou": float(iou[1]),
    }


def save_figure(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def figure2(confusion_rows: list[dict[str, str]], output_dir: Path) -> None:
    per_image, _ = confusion_arrays(confusion_rows)
    counts = per_image.sum(axis=0, dtype=np.int64)
    row_totals = counts.sum(axis=1, keepdims=True)
    percentages = 100.0 * counts / row_totals
    figure, axis = plt.subplots(figsize=(6.3, 5.2))
    image = axis.imshow(percentages, cmap="cividis", vmin=0.0, vmax=100.0)
    axis.set_xticks(np.arange(5))
    axis.set_xticklabels(FIVE_DISPLAY, rotation=28, ha="right")
    axis.set_yticks(np.arange(5))
    axis.set_yticklabels(FIVE_DISPLAY)
    axis.set_xlabel("Predicted class")
    axis.set_ylabel("Reference class")
    colorbar = figure.colorbar(image, ax=axis, fraction=0.047, pad=0.04)
    colorbar.set_label("Row-normalized share (%)")
    for true_index in range(5):
        for predicted_index in range(5):
            value = percentages[true_index, predicted_index]
            axis.text(
                predicted_index,
                true_index,
                f"{value:.2f}%",
                ha="center",
                va="center",
                color="black" if value >= 55.0 else "white",
                fontweight="bold" if true_index == predicted_index else "normal",
                fontsize=8.5,
            )
    for boundary in (0.5, 1.5):
        axis.axhline(boundary, color="white", linewidth=1.4)
        axis.axvline(boundary, color="white", linewidth=1.4)
        axis.axhline(boundary, color="#333333", linewidth=0.35)
        axis.axvline(boundary, color="#333333", linewidth=0.35)
    figure.tight_layout()
    save_figure(figure, output_dir / "figure2_directional_confusion.png")


def figure3(
    confusion_rows: list[dict[str, str]],
    task_rows: list[dict[str, str]],
    output_dir: Path,
) -> None:
    five_per_image, probability_per_image = confusion_arrays(confusion_rows)
    five = five_per_image.sum(axis=0, dtype=np.int64)
    hard = hard_functional_confusion(five)
    probability = probability_per_image.sum(axis=0, dtype=np.int64)
    metrics = [metric_bundle(matrix) for matrix in (five, hard, probability)]

    ids = [row["image_id"] for row in task_rows]
    if len(task_rows) != 429 or ids != [row["image_id"] for row in confusion_rows]:
        raise RuntimeError("Task-aligned and confusion records do not align")
    totals = {
        field: sum(int(row[field]) for row in task_rows)
        for field in (
            "total_error_count",
            "within_functional_count",
            "crop_weed_functional_count",
            "crop_soil_count",
            "weedfunctional_soil_count",
            "crop_fp_total",
            "crop_fn_total",
            "crop_fp_from_soil",
            "crop_fp_from_weed",
            "crop_fp_from_dicot",
            "crop_fp_from_grass",
            "crop_fn_to_soil",
            "crop_fn_to_weed",
            "crop_fn_to_dicot",
            "crop_fn_to_grass",
        )
    }
    composition_fields = (
        "within_functional_count",
        "crop_weed_functional_count",
        "crop_soil_count",
        "weedfunctional_soil_count",
    )
    if sum(totals[field] for field in composition_fields) != totals["total_error_count"]:
        raise RuntimeError("Task-aligned categories do not partition all errors")
    if sum(totals[field] for field in ("crop_fp_from_soil", "crop_fp_from_weed", "crop_fp_from_dicot", "crop_fp_from_grass")) != totals["crop_fp_total"]:
        raise RuntimeError("Crop false-positive sources do not sum to the total")
    if sum(totals[field] for field in ("crop_fn_to_soil", "crop_fn_to_weed", "crop_fn_to_dicot", "crop_fn_to_grass")) != totals["crop_fn_total"]:
        raise RuntimeError("Crop false-negative destinations do not sum to the total")

    figure, axes = plt.subplots(2, 2, figsize=(11.2, 7.4))
    representations = ("Five class", "Hard functional", "Probability functional")
    x = np.arange(2)
    width = 0.24
    colors = (GRAY, BLUE, GREEN)
    for index, (label, color, bundle) in enumerate(zip(representations, colors, metrics)):
        values = 100.0 * np.asarray([bundle["miou"], bundle["crop_iou"]])
        axes[0, 0].bar(x + (index - 1) * width, values, width, label=label, color=color)
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(("mIoU", "Crop IoU"))
    axes[0, 0].set_ylabel("Metric (%)")
    axes[0, 0].set_ylim(0, 105)
    axes[0, 0].legend(frameon=False, fontsize=8)
    axes[0, 0].set_title("A  Global semantic metrics", loc="left", fontweight="bold")

    composition_labels = (
        "within functional",
        "crop↔functional weed",
        "crop↔soil",
        "functional weed↔soil",
    )
    composition_colors = ("#E6B85C", PURPLE, "#C94920", "#4C8F8B")
    left = 0.0
    for label, color, field in zip(composition_labels, composition_colors, composition_fields):
        share = 100.0 * totals[field] / totals["total_error_count"]
        axes[0, 1].barh([0], [share], left=[left], color=color, label=f"{label}: {share:.3f}%")
        left += share
    axes[0, 1].set_xlim(0, 100)
    axes[0, 1].set_yticks([])
    axes[0, 1].set_xlabel("Share of five-class off-diagonal pixels (%)")
    axes[0, 1].legend(frameon=False, fontsize=8, loc="lower center", bbox_to_anchor=(0.5, -0.55))
    axes[0, 1].set_title("B  Off-diagonal error composition", loc="left", fontweight="bold")

    fp_fields = ("crop_fp_from_soil", "crop_fp_from_weed", "crop_fp_from_dicot", "crop_fp_from_grass")
    fp_labels = ("soil→crop", "weed→crop", "dicot→crop", "grass→crop")
    fp_values = [100.0 * totals[field] / totals["crop_fp_total"] for field in fp_fields]
    axes[1, 0].barh(fp_labels, fp_values, color=(GRAY, GREEN, PURPLE, ORANGE))
    axes[1, 0].invert_yaxis()
    axes[1, 0].set_xlabel("Share of crop false positives (%)")
    axes[1, 0].set_title("C  Crop false-positive sources", loc="left", fontweight="bold")

    fn_fields = ("crop_fn_to_soil", "crop_fn_to_weed", "crop_fn_to_dicot", "crop_fn_to_grass")
    fn_labels = ("crop→soil", "crop→weed", "crop→dicot", "crop→grass")
    fn_values = [100.0 * totals[field] / totals["crop_fn_total"] for field in fn_fields]
    axes[1, 1].barh(fn_labels, fn_values, color=(GRAY, GREEN, PURPLE, ORANGE))
    axes[1, 1].invert_yaxis()
    axes[1, 1].set_xlabel("Share of crop false negatives (%)")
    axes[1, 1].set_title("D  Crop false-negative destinations", loc="left", fontweight="bold")
    figure.tight_layout()
    save_figure(figure, output_dir / "figure3_task_aligned_error_accounting.png")


def supported_marker(axis: plt.Axes, x: float, y: float, supported: bool, square: bool) -> None:
    axis.scatter(
        [x],
        [y],
        marker="s" if square else "o",
        facecolor=BLUE if supported else "white",
        edgecolor=BLUE,
        linewidth=1.2,
        s=42,
        zorder=3,
    )


def figure5(
    crop_rows: list[dict[str, str]],
    date_rows: list[dict[str, str]],
    output_dir: Path,
) -> None:
    if len(crop_rows) != 429 or len(date_rows) != 10:
        raise RuntimeError("Expected 429 crop records and 10 date summaries")
    reference = 100.0 * np.asarray(
        [float(row["reference_crop_fraction"]) for row in crop_rows], dtype=np.float64
    )
    hard = 100.0 * np.asarray(
        [float(row["hard_crop_fraction"]) for row in crop_rows], dtype=np.float64
    )
    residual = hard - reference

    figure = plt.figure(figsize=(11.5, 7.8), constrained_layout=True)
    grid = figure.add_gridspec(2, 2)
    axis_a = figure.add_subplot(grid[0, 0])
    axis_b = figure.add_subplot(grid[0, 1])
    date_grid = grid[1, 0].subgridspec(2, 1, hspace=0.08)
    axis_c1 = figure.add_subplot(date_grid[0, 0])
    axis_c2 = figure.add_subplot(date_grid[1, 0], sharex=axis_c1)
    axis_d = figure.add_subplot(grid[1, 1])

    axis_a.scatter(reference, hard, s=12, alpha=0.45, color="#365D6D", edgecolors="none")
    limit = max(27.0, float(np.ceil(max(reference.max(), hard.max()))))
    axis_a.plot([0, limit], [0, limit], linestyle="--", color=GRAY, linewidth=1)
    axis_a.set_xlim(0, limit)
    axis_a.set_ylim(0, limit)
    axis_a.set_xlabel("Reference crop fraction (%)")
    axis_a.set_ylabel("Hard predicted crop fraction (%)")
    axis_a.set_title("A  May 23 hard crop-fraction estimates", loc="left", fontweight="bold")

    axis_b.scatter(reference, residual, s=12, alpha=0.45, color="#365D6D", edgecolors="none")
    axis_b.axhline(0.0, linestyle="--", color=GRAY, linewidth=1)
    axis_b.set_xlabel("Reference crop fraction (%)")
    axis_b.set_ylabel("Predicted − reference (percentage points)")
    axis_b.set_title("B  Signed hard residual", loc="left", fontweight="bold")

    positions = np.arange(len(date_rows), dtype=float)
    date_labels = [row["acquisition_date"][5:] for row in date_rows]
    for position, row in zip(positions, date_rows):
        supported = row["date_specific_generalization_claim_supported"] == "true"
        square = row["generalization_role"] == "in_domain_reference"
        supported_marker(axis_c1, position, 100.0 * float(row["crop_iou"]), supported, square)
        supported_marker(axis_c2, position, 100.0 * float(row["hard_crop_mae"]), supported, square)
    axis_c1.set_ylabel("Crop IoU (%)")
    axis_c1.set_title("C  Date-stratified crop IoU and hard MAE", loc="left", fontweight="bold")
    axis_c1.tick_params(labelbottom=False)
    axis_c2.set_ylabel("Hard MAE (pp)")
    axis_c2.set_xticks(positions)
    axis_c2.set_xticklabels(date_labels, rotation=45, ha="right")
    axis_c2.set_xlabel("Acquisition date (2016)")

    hard_vegetation = 100.0 * np.asarray(
        [float(row["hard_total_vegetation_mae"]) for row in date_rows], dtype=np.float64
    )
    canopeo = 100.0 * np.asarray(
        [float(row["canopeo_total_vegetation_mae"]) for row in date_rows], dtype=np.float64
    )
    axis_d.scatter(positions - 0.10, hard_vegetation, marker="o", color=BLUE, label="hard nonsoil")
    axis_d.scatter(positions + 0.10, canopeo, marker="^", color=ORANGE, label="Canopeo")
    axis_d.set_xticks(positions)
    axis_d.set_xticklabels(date_labels, rotation=45, ha="right")
    axis_d.set_xlabel("Acquisition date (2016)")
    axis_d.set_ylabel("Total-vegetation MAE (pp)")
    axis_d.legend(frameon=False)
    axis_d.set_title("D  Matched total-vegetation MAE", loc="left", fontweight="bold")
    save_figure(figure, output_dir / "figure5_crop_fraction_and_dates.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reproduced/figures"),
        help="Directory for regenerated PNG figures (default: reproduced/figures)",
    )
    args = parser.parse_args()
    confusion_rows = read_rows(ROOT / "results" / "per_image_confusion.csv")
    task_rows = read_rows(ROOT / "results" / "task_aligned_errors.csv")
    crop_rows = read_rows(ROOT / "results" / "crop_fraction_records.csv")
    date_rows = read_rows(ROOT / "results" / "date_level_summary.csv")
    figure2(confusion_rows, args.output_dir)
    figure3(confusion_rows, task_rows, args.output_dir)
    figure5(crop_rows, date_rows, args.output_dir)
    print(f"Wrote three reproduced figure files to {args.output_dir}")


if __name__ == "__main__":
    main()
