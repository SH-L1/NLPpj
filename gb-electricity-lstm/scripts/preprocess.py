"""Verify the NESO snapshot and prepare its continuous half-hour series."""

import csv
import json
from collections import Counter
from datetime import datetime, time, timedelta, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo

from collect_data import META, RAW, ROOT, YEARS, audit, parse_date, write_json

PROCESSED = ROOT / 'data' / 'processed'
OUTPUTS = ROOT / 'reports' / 'outputs'
LONDON = ZoneInfo('Europe/London')
STEP = timedelta(minutes=30)
SPLITS = {2022: 'train', 2023: 'train', 2024: 'validation', 2025: 'test'}
FIELDS = ('settlement_date', 'settlement_period', 'timestamp_utc', 'timestamp_local',
          'nd_mw', 'local_half_hour', 'day_of_week', 'month', 'is_weekend')


@lru_cache(maxsize=None)
def utc_midnight(day):
    return datetime.combine(day, time(), tzinfo=LONDON).astimezone(timezone.utc)


def prepare_year(year):
    path = RAW / f'demanddata_{year}.csv'
    rows, naive_times = [], []
    with path.open(encoding='utf-8-sig', newline='') as stream:
        for raw in csv.DictReader(stream):
            day = parse_date(raw['SETTLEMENT_DATE'].strip())
            period = int(raw['SETTLEMENT_PERIOD'])
            offset = (period - 1) * STEP
            instant = utc_midnight(day) + offset
            local = instant.astimezone(LONDON)
            if local.date() != day:
                raise ValueError(f'{year}: invalid settlement period {day}, {period}')
            naive_times.append(datetime.combine(day, time()) + offset)
            rows.append(dict(zip(FIELDS, (
                day.isoformat(), period, instant.isoformat(), local.isoformat(),
                float(raw['ND']), local.hour * 2 + local.minute // 30,
                local.weekday(), local.month, int(local.weekday() >= 5),
            ))))
    rows.sort(key=lambda row: row['timestamp_utc'])
    naive_counter = Counter(naive_times)
    expected = {min(naive_times) + i * STEP for i in range(len(rows))}
    return rows, {
        'naive_duplicate_slots': sum(count - 1 for count in naive_counter.values()),
        'naive_missing_slots': len(expected - naive_counter.keys()),
    }


def main():
    manifest = json.loads((META / 'download_manifest.json').read_text(encoding='utf-8'))
    expected_hashes = {entry['year']: entry['sha256'] for entry in manifest['files']}
    partitions = {name: [] for name in SPLITS.values()}
    years = []
    for year in YEARS:
        quality = audit(RAW / f'demanddata_{year}.csv', year)
        if quality['sha256'] != expected_hashes[year] or not quality['structural_checks_passed']:
            raise ValueError(f'{year}: original snapshot hash or structural check failed')
        rows, diagnostic = prepare_year(year)
        if len(rows) != quality['rows']:
            raise ValueError(f'{year}: row count changed in preprocessing')
        name = SPLITS[year]
        partitions[name].extend(rows)
        years.append({
            'year': year, 'split': name, 'source_columns': len(quality['columns']),
            'raw_rows': quality['rows'], 'processed_rows': len(rows),
            'missing_by_source_column': quality['missing_by_column'],
            'duplicate_source_keys': quality['duplicate_date_period_rows'],
            'nonpositive_nd': quality['nonpositive_nd_count'],
            'invalid_nd': len(quality['invalid_nd_lines']),
            'clock_change_days': quality['clock_change_days'], **diagnostic,
        })

    instants = [datetime.fromisoformat(row['timestamp_utc'])
                for rows in partitions.values() for row in rows]
    if any(current - previous != STEP for previous, current in zip(instants, instants[1:])):
        raise ValueError('The entire UTC timeline must be unique and contiguous at 30-minute intervals')
    PROCESSED.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    for name, rows in partitions.items():
        destination = PROCESSED / f'{name}.csv'
        temporary = destination.with_suffix('.csv.part')
        with temporary.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        temporary.replace(destination)

    write_json(OUTPUTS / 'preprocessing_audit.json', {
        'source': manifest['source_page'], 'original_hashes_verified': True,
        'timezone': LONDON.key, 'interval_minutes': 30,
        'first_utc': instants[0].isoformat(), 'last_utc': instants[-1].isoformat(),
        'total_rows': len(instants), 'checked_intervals': len(instants) - 1,
        'unexpected_utc_intervals': 0, 'duplicate_utc_timestamps': 0,
        'rows_removed': 0, 'nd_imputed': 0, 'nd_scaled': False,
        'processed_columns': list(FIELDS), 'years': years,
        'splits': {name: len(rows) for name, rows in partitions.items()},
    })
    print(f'Preprocessed {len(instants):,} rows with verified 30-minute UTC continuity.')
    print({name: len(rows) for name, rows in partitions.items()})


if __name__ == '__main__':
    main()
