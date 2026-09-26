"""Narrow checks of pairing, whole-cluster multiplicity, and pooled crop IoU."""

import unittest

import numpy as np

import analyze_paired_uncertainty as analysis


class PairedUncertaintyTests(unittest.TestCase):
    def setUp(self):
        self.original_replicates = analysis.N_RESAMPLES
        analysis.N_RESAMPLES = 32

    def tearDown(self):
        analysis.N_RESAMPLES = self.original_replicates

    def test_external_iou_is_pooled_not_mean_image_iou(self):
        rows = [
            {"M1_TP": 1, "M1_FP": 0, "M1_FN": 0, "M1_signed_error": 0.0},
            {"M1_TP": 0, "M1_FP": 99, "M1_FN": 0, "M1_signed_error": 1.0},
        ]
        result = analysis.metric_values(rows, ("M1",), external=True)["M1"]
        self.assertEqual(result["crop_IoU"], 0.01)
        self.assertNotEqual(result["crop_IoU"], 0.5)

    def test_repeated_cluster_carries_every_image_and_its_multiplicity(self):
        class RepeatedFirstCluster:
            def integers(self, low, high, size):
                return np.zeros(size, dtype=int)

        rows = [
            {"sequence_id": "A", "M1_signed_error": 0.0, "M4_signed_error": 0.2},
            {"sequence_id": "A", "M1_signed_error": 0.4, "M4_signed_error": 0.2},
            {"sequence_id": "B", "M1_signed_error": 0.9, "M4_signed_error": 0.1},
        ]
        _, draws, n_images = analysis.bootstrap(rows, ("M1", "M4"), "sequence_id", RepeatedFirstCluster())
        self.assertTrue(np.all(n_images == 4))  # A,A yields two copies of each A image.
        expected = [0.0, np.sqrt(0.08) - 0.2, 0.2]
        np.testing.assert_allclose(draws, np.tile(expected, (32, 1)), atol=1e-15, rtol=0)

    def test_identical_predictions_cancel_and_swapping_models_reverses_each_draw(self):
        rows = [
            {"sequence_id": "A", "M1_signed_error": 0.1, "M4_signed_error": -0.3},
            {"sequence_id": "A", "M1_signed_error": 0.4, "M4_signed_error": 0.2},
            {"sequence_id": "B", "M1_signed_error": -0.6, "M4_signed_error": 0.1},
        ]
        _, forward, counts = analysis.bootstrap(rows, ("M1", "M4"), "sequence_id", np.random.default_rng(11))
        _, reverse, reversed_counts = analysis.bootstrap(rows, ("M4", "M1"), "sequence_id", np.random.default_rng(11))
        np.testing.assert_array_equal(forward, -reverse)
        np.testing.assert_array_equal(counts, reversed_counts)
        for row in rows:
            row["M4_signed_error"] = row["M1_signed_error"]
        _, zero, _ = analysis.bootstrap(rows, ("M1", "M4"), "sequence_id", np.random.default_rng(11))
        np.testing.assert_array_equal(zero, np.zeros_like(zero))


if __name__ == "__main__":
    unittest.main()
