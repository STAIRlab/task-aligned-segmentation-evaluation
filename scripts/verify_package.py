#!/usr/bin/env python3
"""Check release hashes, schema, cohort counts and stored candidate identities."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ['M' + str(i) for i in range(1, 8)]


def rows(path):
    with (ROOT / path).open(newline='') as f:
        return list(csv.DictReader(f))


def main():
    checked = 0
    for line in (ROOT / 'checksums.sha256').read_text().splitlines():
        expected, name = line.split('  ', 1)
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
        checked += 1
    assert [r['model_id'] for r in rows('config/candidates.csv')] == MODELS
    cohort_names = {'stage1': ('may23_primary_429.csv', 'image_id'),
                    'stage2': ('stage2_180.csv', 'image_id'),
                    'external': ('cropandweed_48.csv', 'selected_image_id')}
    for population, count in [('stage1', 429), ('stage2', 180), ('external', 48)]:
        data = json.loads((ROOT / 'results' / population / 'summary.json').read_text())
        assert [r['model_id'] for r in data['pooled_metrics']] == MODELS
        # Compare recorded sizes and identifiers, not recomputed scientific metrics.
        assert all(r['n_images'] == count for r in data['pooled_metrics'])
        records = rows('results/' + population + '/per_image_records.csv')
        assert Counter(r['model_id'] for r in records) == dict.fromkeys(MODELS, count)
        split_name, id_field = cohort_names[population]
        cohort = rows('splits/' + split_name)
        expected_ids = [r[id_field] for r in cohort]
        assert len(expected_ids) == len(set(expected_ids)) == count
        for model in MODELS:
            assert [r['image_id'] for r in records if r['model_id'] == model] == expected_ids
    temporal = rows('splits/temporal_185.csv')
    assert len(temporal) == 185
    assert Counter(r['generalization_role'] for r in temporal) == {'cross_date': 180, 'in_domain_reference': 5}
    s2 = json.loads((ROOT / 'results/stage2/summary.json').read_text())
    assert len(s2['confirmation_questions']) == 6
    assert {r['status'] for r in s2['confirmation_questions']} == {'PARTIALLY CONFIRMED'}
    assert len(s2['date_metrics']) == 63
    assert len({r['acquisition_date'] for r in s2['date_metrics']}) == 9
    assert all(r['n_images'] == 20 for r in s2['date_metrics'])
    m3 = json.loads((ROOT / 'results/m3/summary.json').read_text())
    assert m3['crop_fraction_estimates']['n_images'] == 429
    assert m3['crop_fraction_estimates']['n_sequences'] == 8
    assert m3['total_vegetation_population_images'] == 185
    assert len(rows('splits/cropandweed_48.csv')) == len({r['session_id'] for r in rows('splits/cropandweed_48.csv')}) == 48
    print('PASS:', checked, 'public file hashes; M1-M7 identities; 429/180/48 cohorts; M3 185-image secondary scope.')
    print('No scientific results were recomputed.')


if __name__ == '__main__':
    main()
