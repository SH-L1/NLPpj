"""Describe the 2022–2023 training period and save reproducible tables and charts."""

import numpy as np
import pandas as pd
from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors

from collect_data import ROOT, write_json
from preprocess import OUTPUTS, PROCESSED

FIGURES = ROOT / 'reports' / 'figures'
BLUE = colors.HexColor('#245783')
TEAL = colors.HexColor('#168575')
GRAY = colors.HexColor('#506478')
GRID = colors.HexColor('#DFE8EF')
LAGS = {1: '30 min', 2: '1 hour', 12: '6 hours', 24: '12 hours',
        48: '24 hours', 96: '48 hours', 336: '7 days'}


def summarize(values):
    return {
        'n': int(values.size), 'mean_mw': float(values.mean()),
        'std_mw': float(values.std()), 'min_mw': float(values.min()),
        'p25_mw': float(values.quantile(.25)), 'median_mw': float(values.median()),
        'p75_mw': float(values.quantile(.75)), 'max_mw': float(values.max()),
    }


def inspect_extreme(frame, index):
    row = frame.loc[index]
    return {'timestamp_local': row['timestamp_local'], 'nd_mw': float(row['nd_mw']),
            'previous_mw': float(frame.loc[index - 1, 'nd_mw']),
            'next_mw': float(frame.loc[index + 1, 'nd_mw'])}


def chart(title, subtitle, xmin, xmax, ymin, ymax, xticks, yticks, xlabel, ylabel):
    drawing = Drawing(780, 385)
    drawing.add(Rect(0, 0, 780, 385, fillColor=colors.white, strokeColor=None))
    drawing.add(String(28, 350, title, fontName='Helvetica-Bold', fontSize=20, fillColor=BLUE))
    drawing.add(String(28, 329, subtitle, fontSize=10, fillColor=GRAY))
    left, right, bottom, top = 78, 748, 68, 293

    def x(value):
        return left + (value - xmin) * (right - left) / (xmax - xmin)

    def y(value):
        return bottom + (value - ymin) * (top - bottom) / (ymax - ymin)

    for tick, label in yticks:
        drawing.add(Line(left, y(tick), right, y(tick), strokeColor=GRID))
        drawing.add(String(left - 9, y(tick) - 3, label, textAnchor='end', fontSize=9, fillColor=GRAY))
    for tick, label in xticks:
        drawing.add(String(x(tick), bottom - 16, label, textAnchor='middle', fontSize=9, fillColor=GRAY))
    drawing.add(Line(left, bottom, right, bottom, strokeColor=GRAY))
    drawing.add(String(left, top + 19, ylabel, fontSize=9, fillColor=GRAY))
    drawing.add(String((left + right) / 2, 29, xlabel, textAnchor='middle', fontSize=10, fillColor=GRAY))
    return drawing, x, y


def save_charts(values, profiles, monthly, lags):
    counts, edges = np.histogram(values, bins=np.arange(13000, 47001, 1000))
    if int(counts.sum()) != len(values):
        raise ValueError('Histogram bins did not cover all training observations')
    ceiling = int(np.ceil(max(counts) / 500)) * 500
    graph, x, y = chart('Distribution of 30-minute electricity demand',
        f'NESO Great Britain | 2022–2023 | {len(values):,} observations | 1,000 MW bins',
        edges[0], edges[-1], 0, ceiling,
        [(v, f'{v:,}') for v in range(15000, 45001, 5000)],
        [(v, f'{v:,}') for v in range(0, ceiling + 1, 500)], 'National Demand (MW)', 'Observations')
    for low, high, count in zip(edges[:-1], edges[1:], counts):
        graph.add(Rect(x(low)+1, y(0), x(high)-x(low)-2, y(count)-y(0), fillColor=TEAL, strokeColor=None))
    renderSVG.drawToFile(graph, str(FIGURES / 'nd_distribution.svg'))

    graph, x, y = chart('Daily demand profile by day type',
        'NESO Great Britain | Mean National Demand, 2022–2023 | 48 local clock slots',
        0, 47, 15000, 40000, [(i * 6, f'{i * 3:02d}:00') for i in range(8)] + [(47, '23:30')],
        [(v, f'{v:,}') for v in range(15000, 40001, 5000)], 'Local clock time (Europe/London)', 'Mean ND (MW)')
    for key, title, color, start in [(0, 'Weekdays', BLUE, 493), (1, 'Weekends', TEAL, 620)]:
        profile = profiles.xs(key, level='is_weekend')
        graph.add(PolyLine([(x(slot), y(row['mean_mw'])) for slot, row in profile.iterrows()],
                           strokeColor=color, strokeWidth=2.5))
        graph.add(Line(start, 313, start + 21, 313, strokeColor=color, strokeWidth=2.5))
        graph.add(String(start + 27, 310, title, fontSize=9, fillColor=GRAY))
    renderSVG.drawToFile(graph, str(FIGURES / 'nd_daily_profiles.svg'))

    graph, x, y = chart('Monthly mean electricity demand',
        'NESO Great Britain | Local settlement month, January 2022 through December 2023',
        0, 23, 18000, 38000, [(i, str(label)) for i, label in enumerate(monthly.index) if i % 3 == 0 or i == 23],
        [(v, f'{v:,}') for v in range(18000, 38001, 5000)], 'Settlement month', 'Mean ND (MW)')
    graph.add(PolyLine([(x(i), y(value)) for i, value in enumerate(monthly['mean_mw'])],
                       strokeColor=TEAL, strokeWidth=2.5))
    renderSVG.drawToFile(graph, str(FIGURES / 'nd_monthly.svg'))

    graph, x, y = chart('Relationship between current and past demand',
        f'NESO Great Britain | Pearson r | Same {lags[0]["n"]:,} target timestamps at all lags',
        -.55, len(lags) - .45, -1, 1, [(i, row['label']) for i, row in enumerate(lags)],
        [(v, f'{v:g}') for v in (-1, -.5, 0, .5, 1)], 'Elapsed time before the target (UTC)', 'Pearson r')
    for i, row in enumerate(lags):
        value = row['pearson_r']
        graph.add(Rect(x(i)-18, min(y(0), y(value)), 36, abs(y(value)-y(0)),
                       fillColor=TEAL if value >= 0 else BLUE, strokeColor=None))
        graph.add(String(x(i), y(value) + (6 if value >= 0 else -13), f'{value:.3f}',
                         textAnchor='middle', fontSize=9, fillColor=GRAY))
    renderSVG.drawToFile(graph, str(FIGURES / 'nd_lag_relationship.svg'))


def main():
    frame = pd.read_csv(PROCESSED / 'train.csv', dtype={'settlement_date': str})
    if set(frame['settlement_date'].str[:4]) != {'2022', '2023'}:
        raise ValueError('EDA input must contain only the 2022–2023 training period')
    instants = pd.to_datetime(frame['timestamp_utc'], utc=True)
    if not instants.diff().iloc[1:].eq(pd.Timedelta(minutes=30)).all():
        raise ValueError('EDA input must be contiguous at 30 minutes')
    values = frame['nd_mw']
    raw_summary = summarize(values)
    spread = raw_summary['p75_mw'] - raw_summary['p25_mw']
    lower = raw_summary['p25_mw'] - 1.5 * spread
    upper = raw_summary['p75_mw'] + 1.5 * spread
    high = values.gt(upper)
    high_runs = (high & ~high.shift(fill_value=False)).cumsum()
    high_run_lengths = high[high].groupby(high_runs[high]).size()
    types = []
    for kind, group in frame.groupby('is_weekend'):
        entry = summarize(group['nd_mw'])
        types.append({'group': 'weekend' if kind else 'weekday', **entry,
                      'share_percent': 100 * len(group) / len(frame)})

    profiles = frame.groupby(['is_weekend', 'local_half_hour'])['nd_mw'].agg(n='count', mean_mw='mean', median_mw='median')
    monthly = frame.groupby(frame['settlement_date'].str[:7].rename('month'))['nd_mw'].agg(n='count', mean_mw='mean', median_mw='median')
    sample = frame.iloc[max(LAGS):]
    lags = []
    for steps, label in LAGS.items():
        past = values.shift(steps).loc[sample.index]
        now = sample['nd_mw']
        lags.append({'steps': steps, 'label': label, 'n': len(now), 'pearson_r': float(now.corr(past)),
                     'mean_absolute_difference_mw': float((now - past).abs().mean())})

    # The error of reusing the immediately preceding value equals the observed change.
    changes = values.diff()
    abs_change = changes.abs().dropna()
    threshold = float(abs_change.quantile(.99))
    above = abs_change[abs_change >= threshold]
    extreme_indices = [int(values.idxmin()), int(values.idxmax())]
    ramp_examples = [{
        'timestamp_local': frame.loc[index, 'timestamp_local'],
        'previous_mw': float(values.loc[index - 1]), 'nd_mw': float(values.loc[index]),
        'change_mw': float(changes.loc[index]),
    } for index in (changes.idxmax(), changes.idxmin())]
    peaks = []
    for kind in (0, 1):
        profile = profiles.xs(kind, level='is_weekend')['mean_mw']
        for name, slot in [('minimum', profile.idxmin()), ('maximum', profile.idxmax())]:
            peaks.append({'group': 'weekend' if kind else 'weekday', 'type': name,
                          'local_time': f'{slot // 2:02d}:{30 * (slot % 2):02d}',
                          'mean_mw': float(profile.loc[slot])})

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    profiles.to_csv(OUTPUTS / 'eda_daily_profiles.csv', float_format='%.6f')
    monthly.to_csv(OUTPUTS / 'eda_monthly.csv', float_format='%.6f')
    pd.DataFrame(lags).to_csv(OUTPUTS / 'eda_lags.csv', index=False, float_format='%.6f')
    write_json(OUTPUTS / 'eda_summary.json', {
        'scope': '2022–2023 training period only', 'nd': raw_summary, 'groups': types,
        'profiles_min_max': peaks,
        'iqr_screen': {'lower_mw': lower, 'upper_mw': upper,
                       'below_count': int((values < lower).sum()), 'above_count': int(high.sum()),
                       'high_run_count': int(len(high_run_lengths)),
                       'isolated_high_count': int(high_run_lengths.eq(1).sum()),
                       'longest_high_run': int(high_run_lengths.max()) if len(high_run_lengths) else 0,
                       'observed_extremes': [inspect_extreme(frame, index) for index in extreme_indices]},
        'monthly_min': {'month': str(monthly['mean_mw'].idxmin()), 'mean_mw': float(monthly['mean_mw'].min())},
        'monthly_max': {'month': str(monthly['mean_mw'].idxmax()), 'mean_mw': float(monthly['mean_mw'].max())},
        'lags': lags,
        'ramp_diagnostic': {'n': len(abs_change), 'median_abs_change_mw': float(abs_change.median()),
                            'p99_abs_change_mw': threshold, 'above_or_equal_count': len(above),
                            'mean_abs_change_mw': float(abs_change.mean()),
                            'tail_mean_abs_change_mw': float(above.mean()), 'largest_rises_and_falls': ramp_examples},
    })
    save_charts(values, profiles, monthly, lags)
    print(f'Analyzed {len(frame):,} training records. Wrote summaries and four figures.')


if __name__ == '__main__':
    main()
