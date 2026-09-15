#!/usr/bin/env python3
"""Render quantitative panels for Figures 3-6 from saved manuscript results.

Plot functions reuse the author-approved manuscript renderer. Only data loading
and output paths differ. No inference, metric fitting, quantiles, or resampling.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import MaxNLocator
from matplotlib.transforms import Bbox

ROOT = Path(__file__).resolve().parents[1]
MODELS = ['M' + str(i) for i in range(1, 8)]
COLORS = ['#252525', '#0072b2', '#d55e00', '#009e73', '#cc79a7', '#56a1ba', '#84754e']
MARKERS = ['o', 's', '^', 'D', 'v', 'P', 'X']
SEMANTIC_HEX = ['#b3b3b3', '#009e73', '#0072b2', '#e69f00', '#cc79a7']
CLASS_NAMES = ['Soil/background', 'Crop', 'Weed', 'Dicot', 'Grass']
PALETTE = np.array([[179, 179, 179], [0, 158, 115], [0, 114, 178],
                    [230, 159, 0], [204, 121, 167]], dtype=np.uint8)
TEXT = '#252a30'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8.5,
                     'axes.labelsize': 8.5, 'axes.titlesize': 8.5,
                     'xtick.labelsize': 8, 'ytick.labelsize': 8,
                     'text.color': TEXT, 'axes.labelcolor': TEXT,
                     'pdf.fonttype': 42, 'svg.fonttype': 'none',
                     'axes.spines.top': False, 'axes.spines.right': False})


def summary(population):
    return json.loads((ROOT / 'results' / population / 'summary.json').read_text())


DP, A2, AE, M3 = [summary(p) for p in ['stage1', 'stage2', 'external', 'm3']]
D1, D2, DE = DP['pooled_metrics'], A2['pooled_metrics'], AE['pooled_metrics']
CM = np.array(M3['confusion_5class_global'], dtype=np.int64)


def save(fig, name, evidence=None):
    fig.savefig(OUT / (name + '.pdf'), dpi=600, facecolor='white',
                metadata={'Title': name, 'Creator': 'Stored-result display renderer',
                          'CreationDate': None, 'ModDate': None})
    fig.savefig(OUT / (name + '.png'), dpi=300, facecolor='white')
    plt.close(fig)


def tidy(ax, axis='both'):
    ax.set_axisbelow(True)
    ax.grid(axis=axis, color='#e5e8eb', lw=.5)
    ax.tick_params(length=2.5)

def contrast_text(color):
    """Choose white or the common dark text color by relative contrast."""
    def luminance(rgb):
        linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        return sum(a*b for a, b in zip(linear, [.2126, .7152, .0722]))
    light = luminance(matplotlib.colors.to_rgb(color))
    dark = luminance(matplotlib.colors.to_rgb(TEXT))
    return 'white' if 1.05/(light+.05) > (light+.05)/(dark+.05) else TEXT

def label_points(fig, ax, xs, ys):
    """Use vertical offsets only, at a common spacing; reject visible collisions."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    positions = ax.transData.transform(np.column_stack([xs, ys]))
    scale = fig.dpi / 72
    markers = [Bbox.from_extents(x-4.3*scale, y-4.3*scale, x+4.3*scale, y+4.3*scale)
               for x, y in positions]
    occupied = []
    chosen = []
    # Give the most crowded points first choice of a common offset.
    dist = np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=2)
    np.fill_diagonal(dist, np.inf)
    order = sorted(range(7), key=lambda i: (float(dist[i].min()), i))
    for i in order:
        for dy in [8, -8, 16, -16, 24, -24]:
            ann = ax.annotate(MODELS[i], (xs[i], ys[i]), xytext=(0, dy),
                              textcoords='offset points', ha='center',
                              va='bottom' if dy > 0 else 'top', fontsize=8)
            bb = ann.get_window_extent(renderer).expanded(1.10, 1.10)
            good = (ax.bbox.contains(bb.x0, bb.y0) and ax.bbox.contains(bb.x1, bb.y1)
                    and not any(bb.overlaps(b) for b in occupied + markers))
            if good:
                occupied.append(bb)
                if abs(dy) > 8:
                    ax.annotate('', (xs[i], ys[i]), xytext=(0, dy), textcoords='offset points',
                                arrowprops={'arrowstyle': '-', 'color': '#69737a', 'lw': .55,
                                            'shrinkA': 1, 'shrinkB': 4})
                chosen.append({'model': MODELS[i], 'dx_points': 0, 'dy_points': dy})
                break
            ann.remove()
        else:
            raise RuntimeError('No collision-free vertical label location for ' + MODELS[i])
    return chosen

def figure3():
    for panel, data, xkey, ykey, xname, yname in [
        ('a', D1, 'five_class_miou', 'crop_fraction_mae', 'Semantic mIoU (%)', 'MAE (pp)'),
        ('b', D2, 'five_class_miou', 'crop_fraction_mae', 'Semantic mIoU (%)', 'MAE (pp)'),
        ('c', D1, 'crop_fraction_rmse', 'maximum_absolute_error', 'RMSE (pp)', 'Maximum AE (pp)'),
        ('d', D2, 'crop_fraction_rmse', 'maximum_absolute_error', 'RMSE (pp)', 'Maximum AE (pp)')]:
        fig, ax = plt.subplots(figsize=(3.55, 2.32))
        fig.subplots_adjust(left=.18, right=.985, bottom=.22, top=.98)
        xs = [d[xkey]*100 for d in data]
        ys = [d[ykey]*100 for d in data]
        for i, (x, y) in enumerate(zip(xs, ys)):
            ax.scatter(x, y, s=32, color=COLORS[i], marker=MARKERS[i], zorder=3)
        ax.set(xlabel=xname, ylabel=yname)
        ax.margins(x=.20, y=.29)
        ax.xaxis.set_major_locator(MaxNLocator(5))
        ax.yaxis.set_major_locator(MaxNLocator(5))
        tidy(ax)
        placements = label_points(fig, ax, xs, ys)
        save(fig, 'figure3' + panel, {'x_key': xkey, 'y_key': ykey, 'x_pp_or_percent': xs,
                                    'y_pp': ys, 'labels': placements})

def winners(rankings, key):
    return ['M' + str(r['model_id']).replace('M', '') for r in rankings
            if r['metric'] == key and r['rank'] == 1]

def figure4():
    keys = ['0.5', '0.75', '0.9', '0.95', '0.99']
    norm = matplotlib.colors.LogNorm(vmin=.03, vmax=50)
    cmap = plt.get_cmap('cividis_r')
    for panel, data in [('a', DP['tail_summary']), ('b', D2)]:
        fig, ax = plt.subplots(figsize=(3.55, 2.35))
        fig.subplots_adjust(left=.105, right=.995, top=.985, bottom=.14)
        plotted = []
        for i, d in enumerate(data):
            q = d['quantiles_linear'] if panel == 'a' else d['absolute_error_quantiles']
            vals = [q[k]*100 for k in keys] + [d['maximum_absolute_error']*100]
            plotted.append({'model': MODELS[i], 'values_pp': vals})
        values = np.array([r['values_pp'] for r in plotted])
        best = values == values.min(axis=0)
        ax.imshow(values, norm=norm, cmap=cmap, aspect='auto', interpolation='none')
        for i in range(7):
            for j in range(6):
                ax.text(j, i, f'{values[i,j]:.3f}', ha='center', va='center', fontsize=8,
                        color='white',
                        path_effects=[path_effects.withStroke(linewidth=.65, foreground=TEXT)],
                        fontweight='bold')
                if best[i,j]:
                    ax.add_patch(Rectangle((j-.465, i-.465), .93, .93, fill=False,
                                           edgecolor='black' if panel == 'a' else TEXT, lw=1.05))
        ax.set_xticks(range(6))
        ax.set_xticklabels(['P50', 'P75', 'P90', 'P95', 'P99', 'Max'])
        ax.set_yticks(range(7))
        ax.set_yticklabels(MODELS)
        ax.set_xticks(np.arange(-.5, 6, 1), minor=True)
        ax.set_yticks(np.arange(-.5, 7, 1), minor=True)
        ax.grid(which='minor', color='white', lw=.55)
        ax.tick_params(which='both', length=0, pad=4)
        for spine in ax.spines.values():
            spine.set_visible(False)
        save(fig, 'figure4' + panel, {'quantiles': keys + ['maximum'], 'values': plotted,
                                    'display_decimals_pp': 3, 'column_minimum_models':
                                    [[MODELS[i] for i in range(7) if best[i,j]] for j in range(6)],
                                    'color_scale': 'log', 'color_limits_pp': [.03, 50],
                                    'colormap': 'cividis_r', 'lower_is_better': True})

    fig = plt.figure(figsize=(7.2, .50))
    ax = fig.add_axes([.16, .62, .68, .22])
    cb = fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap), cax=ax, orientation='horizontal')
    cb.set_ticks([.03, .1, .3, 1, 3, 10, 50])
    cb.set_ticklabels(['0.03', '0.1', '0.3', '1', '3', '10', '50'])
    cb.ax.minorticks_off()
    cb.ax.tick_params(length=2, pad=2, labelsize=8)
    cb.outline.set_linewidth(.4)
    fig.text(.5, .01, 'Absolute error (pp; logarithmic color scale) · Lower is better', ha='center', va='bottom', fontsize=8)
    save(fig, 'figure4_colorbar', {'color_limits_pp': [.03, 50], 'colormap': 'cividis_r'})

    dates = sorted({d['acquisition_date'] for d in A2['date_metrics']})
    metrics = ['five_class_miou', 'crop_iou', 'crop_fraction_mae',
               'crop_fraction_rmse', 'maximum_absolute_error']
    cells = [[winners([r for r in A2['date_rankings'] if r['acquisition_date'] == date], k)
              for k in metrics] for date in dates]
    cells.append([winners(A2['pooled_rankings'], k) for k in metrics])
    fig, ax = plt.subplots(figsize=(7.2, 2.83))
    fig.subplots_adjust(left=.17, right=.99, top=.89, bottom=.02)
    ypos = list(range(9)) + [9.55]
    fills = [matplotlib.colors.to_hex(.38*np.array(matplotlib.colors.to_rgb(c))+.62) for c in COLORS]
    for y, row in zip(ypos, cells):
        for x, names in enumerate(row):
            assert names
            for part, model in enumerate(names):
                color = fills[MODELS.index(model)]
                ax.add_patch(Rectangle((x-.49+part*.98/len(names), y-.45),
                                       .98/len(names), .90, facecolor=color, edgecolor='white', lw=.5))
                ax.text(x-.49+(part+.5)*.98/len(names), y, model,
                        ha='center', va='center', color=contrast_text(color), fontsize=8.5,
                        fontweight='bold' if y == ypos[-1] else 'normal')
    ax.set_xlim(-.5, 4.5)
    ax.set_ylim(10.08, -.52)
    ax.set_xticks(range(5))
    ax.set_xticklabels(['mIoU', 'Crop IoU', 'MAE', 'RMSE', 'Maximum AE'])
    ax.xaxis.tick_top()
    ax.set_yticks(ypos)
    ax.set_yticklabels([d[5:]+(' *' if d.endswith('04-29') else '') for d in dates]+['Pooled (180)'])
    ax.set_ylabel('Acquisition date (2016)')
    ax.tick_params(length=0, pad=5)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.axhline(9.02, color='#75828b', lw=.65)
    ax.add_patch(Rectangle((-.5, ypos[-1]-.45), 5, .90, fill=False, edgecolor='#75828b', lw=.8, clip_on=False))
    save(fig, 'figure4c_winners', {'dates': dates+['pooled'], 'metrics': metrics, 'winners': cells,
                                 'candidate_fill_colors': dict(zip(MODELS, fills)),
                                 'candidate_text_colors': {m:contrast_text(c) for m,c in zip(MODELS,fills)}})

def figure5():
    for panel, key, label, limit in [('a', 'crop_iou', 'Crop IoU (%)', 85),
                                     ('b', 'mae', 'MAE (pp)', 3.8),
                                     ('c', 'rmse', 'RMSE (pp)', 7.5),
                                     ('d', 'maximum_absolute_error', 'Maximum AE (pp)', 32.5)]:
        fig, ax = plt.subplots(figsize=(3.55, 2.33))
        fig.subplots_adjust(left=.105, right=.985, top=.98, bottom=.22)
        vals = [d[key]*100 for d in DE]
        best = max(vals) if panel == 'a' else min(vals)
        ax.hlines(range(7), 0, vals, lw=.6, color='#d6dde3')
        for i, v in enumerate(vals):
            ax.scatter(v, i, s=28, color=COLORS[i], marker=MARKERS[i], zorder=3)
            ax.text(v + limit*.026, i, f'{v:.4f}', va='center', fontsize=8)
            if v == best:
                ax.scatter(v, i, s=86, facecolors='none', edgecolors=TEXT, lw=.9, zorder=4)
        ax.set_yticks(range(7))
        ax.set_yticklabels(MODELS)
        ax.set(xlim=(0, limit), ylim=(6.65, -.65), xlabel=label)
        ax.xaxis.set_major_locator(MaxNLocator(5))
        tidy(ax, 'x')
        save(fig, 'figure5' + panel, {'metric': key, 'values_pp_or_percent': vals,
                                    'winner': MODELS[vals.index(best)]})

def figure6():
    pct = 100*CM/CM.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(3.55, 2.50))
    fig.subplots_adjust(left=.20, right=.99, bottom=.21, top=.98)
    ax.imshow(pct, cmap='Blues', vmin=0, vmax=100, aspect='auto')
    names = ['Soil', 'Crop', 'Weed', 'Dicot', 'Grass']
    ax.set_xticks(range(5)); ax.set_yticks(range(5))
    ax.set_xticklabels(names); ax.set_yticklabels(names)
    ax.set(xlabel='Predicted class', ylabel='Reference class')
    ax.tick_params(length=0, pad=4)
    for i in range(5):
        for j in range(5):
            ax.text(j, i, f'{pct[i,j]:.1f}', ha='center', va='center', fontsize=8.5,
                    color='white' if pct[i,j] > 55 else TEXT)
    save(fig, 'figure6a_matrix', {'counts': CM.tolist(), 'row_percent': pct.tolist()})

    fig, ax = plt.subplots(figsize=(3.55, 2.50))
    fig.subplots_adjust(left=.065, right=.97, bottom=.40, top=.96)
    idx = [0, 2, 3, 4]
    fp, fn = CM[idx, 1], CM[1, idx]
    for y, values, label in [(1, fp, 'FP sources'), (0, fn, 'FN destinations')]:
        left = 0
        for k, value in enumerate(values/values.sum()*100):
            ax.barh(y, value, left=left, height=.39, color=PALETTE[idx[k]]/255,
                    edgecolor='white', lw=.45)
            if value > 10:
                ax.text(left+value/2, y, f'{value:.1f}', ha='center', va='center', fontsize=8.5,
                        color=contrast_text(PALETTE[idx[k]]/255))
            left += value
        ax.text(0, y+.28, label, fontsize=8.5, va='bottom')
    ax.set(xlim=(0, 100), ylim=(-.36, 1.60), xlabel='Share within FP or FN (%)')
    ax.set_yticks([])
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.spines['left'].set_visible(False)
    ax.tick_params(length=2.5)
    fig.legend(handles=[Patch(facecolor=PALETTE[i]/255, label=n) for i, n in
                        zip(idx, ['Soil', 'Weed', 'Dicot', 'Grass'])],
               loc='lower center', bbox_to_anchor=(.52, .04), ncol=4, frameon=False,
               fontsize=8, handlelength=.9, columnspacing=1.0, handletextpad=.4)
    save(fig, 'figure6b_composition', {'FP_counts': fp.tolist(), 'FN_counts': fn.tolist(),
                                     'FP_total': int(fp.sum()), 'FN_total': int(fn.sum()),
                                     'FP_percent': (100*fp/fp.sum()).tolist(),
                                     'FN_percent': (100*fn/fn.sum()).tolist(),
                                     'class_colors': {CLASS_NAMES[i]:SEMANTIC_HEX[i] for i in idx}})

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.57))
    fig.subplots_adjust(left=.065, right=.99, top=.89, bottom=.32, wspace=.28)
    evidence = []
    for ax, data, name, den, limit in zip(axes, [D1, D2, DE], ['Stage 1', 'Stage 2', 'External'],
                                         [537080544, 225348480, 100192734], [.85, .16, 3.2]):
        fp = np.array([d['crop_FP'] for d in data])*100/den
        fn = np.array([d['crop_FN'] for d in data])*100/den
        ax.barh(range(7), fp, color='#cd6c35', height=.5)
        ax.barh(range(7), -fn, color='#4888ae', height=.5)
        ax.scatter(fp-fn, range(7), marker='D', s=19, color=TEXT, zorder=4)
        ax.axvline(0, lw=.7, color=TEXT)
        ax.set(ylim=(6.7, -.7), xlim=(-limit, limit), xlabel='Signed contribution (%)')
        ax.set_yticks(range(7)); ax.set_yticklabels(MODELS)
        ax.set_title(name, pad=6)
        ax.xaxis.set_major_locator(MaxNLocator(3))
        tidy(ax, 'x')
        evidence.append({'population': name, 'denominator': den, 'xlim': [-limit, limit],
                         'FP_percent': fp.tolist(), 'FN_percent': fn.tolist(),
                         'net_percent': (fp-fn).tolist()})
    fig.legend(handles=[Patch(color='#cd6c35', label='+FP/N'), Patch(color='#4888ae', label='−FN/N'),
                        Line2D([0], [0], marker='D', color=TEXT, ls='', label='Net (FP−FN)/N')],
               loc='lower center', bbox_to_anchor=(.5, .01), ncol=3, frameon=False,
               fontsize=8.5, handlelength=1, columnspacing=2)
    save(fig, 'figure6c_pooled', {'populations': evidence})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('reproduced/figures'))
    parser.add_argument('--figures', default='3,4,5,6', help='Comma-separated subset of 3,4,5,6')
    args = parser.parse_args()
    requested = args.figures.split(',')
    if not requested or any(n not in ['3', '4', '5', '6'] for n in requested):
        parser.error('Only quantitative Figures 3, 4, 5 and 6 are provided.')
    OUT = args.output_dir
    OUT.mkdir(parents=True, exist_ok=True)
    for number in requested:
        globals()['figure' + number]()
        print('Rendered stored-result panels for Figure', number)
