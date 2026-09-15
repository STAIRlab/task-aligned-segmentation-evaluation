#!/usr/bin/env python3
"""Export Tables 1-7 from stored results; no metric estimation or resampling."""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_csv(name):
    with (ROOT / name).open(newline='') as f:
        return list(csv.DictReader(f))


def load_summary(population):
    return json.loads((ROOT / 'results' / population / 'summary.json').read_text())


def write_table(output_dir, name, rows):
    with (output_dir / (name + '.csv')).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def displayed(value, digits=4, scale=100):
    return format(float(value) * scale, '.' + str(digits) + 'f')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('reproduced/tables'))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    s1, s2, ext, m3 = [load_summary(name) for name in ['stage1', 'stage2', 'external', 'm3']]
    write_table(args.output_dir, 'table1_candidates', read_csv('config/candidates.csv'))
    write_table(args.output_dir, 'table2_populations', read_csv('config/populations.csv'))
    bonn = []
    columns = [('mIoU_pct', 'five_class_miou'), ('crop_IoU_pct', 'crop_iou'),
               ('functional_mIoU_pct', 'hard_functional_miou'), ('bias_pp', 'crop_fraction_bias'),
               ('MAE_pp', 'crop_fraction_mae'), ('RMSE_pp', 'crop_fraction_rmse'),
               ('median_AE_pp', 'median_absolute_error')]
    for population, data in [('stage1', s1), ('stage2', s2)]:
        for record in data['pooled_metrics']:
            row = {'population': population, 'model_id': record['model_id']}
            row.update({name: displayed(record[key]) for name, key in columns})
            if population == 'stage1':
                tail = next(t for t in s1['tail_summary'] if t['model_id'] == record['model_id'])
                p99 = tail['quantiles_linear']['0.99']
            else:
                p99 = record['absolute_error_quantiles']['0.99']
            row.update(P99_AE_pp=displayed(p99), maximum_AE_pp=displayed(record['maximum_absolute_error']))
            bonn.append(row)
    write_table(args.output_dir, 'table3_bonn_profiles', bonn)

    associations = []
    for a, b in [('five_class_miou', 'crop_iou'), ('five_class_miou', 'crop_fraction_mae'),
                 ('five_class_miou', 'crop_fraction_rmse'), ('crop_iou', 'crop_fraction_mae'),
                 ('crop_iou', 'crop_fraction_rmse'), ('crop_fraction_mae', 'crop_fraction_rmse')]:
        row = {'first_metric': a, 'second_metric': b}
        for population, records in [('stage1', s1['rank_correlations']), ('stage2', s2['pooled_rank_correlations'])]:
            record = next(r for r in records if r['first_metric'] == a and r['second_metric'] == b)
            row[population + '_rho'] = displayed(record['spearman_rho'], 3, 1)
            row[population + '_tau_b'] = displayed(record['kendall_tau_b'], 3, 1)
        rename = {'crop_fraction_mae': 'mae', 'crop_fraction_rmse': 'rmse'}
        matches = [r for r in ext['rank_correlations'] if r['metric_a'] == rename.get(a, a) and r['metric_b'] == rename.get(b, b)]
        for key, field in [('rho', 'spearman_rho'), ('tau_b', 'kendall_tau_b')]:
            row['external_' + key] = displayed(matches[0][field], 3, 1) if matches else 'NA'
        associations.append(row)
    write_table(args.output_dir, 'table4a_rank_associations', associations)
    write_table(args.output_dir, 'table4b_rank_persistence', [
        {'metric': r['metric'], 'rho': displayed(r['spearman_rho'], 3, 1),
         'tau_b': displayed(r['kendall_tau_b'], 3, 1), 'winner_retained': 'Yes' if r['winner_retained'] else 'No'}
        for r in s2['cross_stage_rank_persistence']])
    write_table(args.output_dir, 'table5a_confirmation_outcomes', [
        {'question_id': r['question_id'], 'question': r['question'], 'status': r['status'],
         'recorded_components': json.dumps({k: v for k, v in r.items() if k not in ['question_id', 'question', 'status']}, sort_keys=True)}
        for r in s2['confirmation_questions']])
    write_table(args.output_dir, 'table5b_date_support', [
        {'component': key, 'supporting_dates': record['supporting_dates'], 'of_dates': record['of_dates']}
        for key, record in s2['date_directional_support'].items()])
    ext_columns = [('crop_IoU_pct', 'crop_iou'), ('bias_pp', 'signed_bias'), ('MAE_pp', 'mae'),
                   ('RMSE_pp', 'rmse'), ('median_AE_pp', 'median_absolute_error'),
                   ('P90_AE_pp', 'p90_absolute_error'), ('P95_AE_pp', 'p95_absolute_error'),
                   ('maximum_AE_pp', 'maximum_absolute_error')]
    write_table(args.output_dir, 'table6_external_profiles', [
        {'model_id': r['model_id'], **{name: displayed(r[key]) for name, key in ext_columns}}
        for r in ext['pooled_metrics']])
    sem_columns = [('PA_pct', 'PA_fraction'), ('MPA_pct', 'MPA_fraction'), ('mIoU_pct', 'mIoU_fraction'),
                   ('macro_F1_pct', 'macro_F1_fraction'), ('crop_IoU_pct', 'crop_IoU_fraction'),
                   ('soil_IoU_pct', 'soil_IoU_fraction'), ('functional_weed_IoU_pct', 'functional_weed_IoU_fraction')]
    write_table(args.output_dir, 'table7a_m3_representations', [
        {'representation': r['representation'], **{name: displayed(r[key], 2) if r[key] else 'NA' for name, key in sem_columns}}
        for r in m3['representation_metrics']])
    intervals = []
    for route in ['hard_crop', 'soft_crop']:
        for metric in ['bias', 'mae', 'rmse', 'median_absolute_error']:
            r = m3['crop_fraction_estimates'][route][metric]
            intervals.append({'route': route, 'metric': metric, 'estimate_pp': displayed(r['estimate'], 3),
                              'CI_low_pp': displayed(r['ci_low'], 3), 'CI_high_pp': displayed(r['ci_high'], 3)})
    write_table(args.output_dir, 'table7b_m3_saved_intervals', intervals)
    write_table(args.output_dir, 'table7c_m3_total_vegetation', [
        {'estimator': k, 'n_images': m3['total_vegetation_population_images'], 'MAE_pp': displayed(v, 3)}
        for k, v in m3['total_vegetation_mae'].items()])
    print('Wrote 11 CSV components for manuscript Tables 1-7 to', args.output_dir)
    print('Stored estimates and intervals were formatted; no analysis or bootstrap was run.')


if __name__ == '__main__':
    main()
