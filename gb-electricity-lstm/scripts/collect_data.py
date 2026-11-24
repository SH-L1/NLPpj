"""Download unchanged NESO CSVs and audit their contents using only Python's standard library."""

import argparse
import calendar
import csv
import hashlib
import io
import json
import math
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
META = ROOT / 'data' / 'metadata'
YEARS = (2022, 2023, 2024, 2025)
API = 'https://api.neso.energy/api/3/action/package_show?id=historic-demand-data'


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'GB-electricity-course-project/1.0'})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def parse_date(value):
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%b-%Y', '%d-%b-%y', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError(f'Unknown settlement date: {value!r}')


def expected_periods(day):
    # GB settlement days have 46/50 periods at the spring/autumn clock changes.
    for month, periods in ((3, 46), (10, 50)):
        last = date(day.year, month, calendar.monthrange(day.year, month)[1])
        last_sunday = last - timedelta(days=(last.weekday() + 1) % 7)
        if day == last_sunday:
            return periods
    return 48


def audit(path, year):
    payload = path.read_bytes()
    reader = csv.DictReader(io.StringIO(payload.decode('utf-8-sig'), newline=''))
    columns = reader.fieldnames
    if not columns or not {'SETTLEMENT_DATE', 'SETTLEMENT_PERIOD', 'ND'} <= set(columns):
        raise ValueError(f'{path.name}: required columns missing; got {columns}')
    missing = Counter({column: 0 for column in columns})
    keys = Counter()
    per_day = Counter()
    periods_by_day = {}
    values = []
    invalid_nd = []
    invalid_rows = []
    for line, row in enumerate(reader, start=2):
        if None in row:
            raise ValueError(f'{path.name}:{line}: extra CSV fields')
        for column in columns:
            if row[column] is None or row[column].strip().lower() in ('', 'na', 'nan', 'null', 'n/a'):
                missing[column] += 1
        try:
            day = parse_date(row['SETTLEMENT_DATE'].strip())
            period = int(row['SETTLEMENT_PERIOD'])
        except (ValueError, AttributeError, TypeError) as error:
            invalid_rows.append({'line': line, 'error': str(error)})
            continue
        keys[(day, period)] += 1
        per_day[day] += 1
        periods_by_day.setdefault(day, set()).add(period)
        try:
            value = float(row['ND'])
            if not math.isfinite(value):
                raise ValueError('non-finite ND')
            values.append(value)
        except (ValueError, TypeError):
            invalid_nd.append(line)
    start, end = date(year, 1, 1), date(year, 12, 31)
    expected_days = {start + timedelta(days=i) for i in range((end-start).days + 1)}
    period_issues = [str(day) for day in sorted(per_day)
                     if per_day[day] != expected_periods(day)
                     or periods_by_day[day] != set(range(1, expected_periods(day) + 1))]
    duplicates = sum(count - 1 for count in keys.values())
    missing_days = sorted(str(day) for day in expected_days - set(per_day))
    extra_days = sorted(str(day) for day in set(per_day) - expected_days)
    passed = not (duplicates or missing_days or extra_days or period_issues or invalid_nd or invalid_rows
                  or any(value <= 0 for value in values))
    return {
        'year': year, 'file': path.relative_to(ROOT).as_posix(),
        'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(),
        'rows': sum(per_day.values()) + len(invalid_rows), 'columns': columns,
        'first_settlement_date': str(min(per_day)) if per_day else None,
        'last_settlement_date': str(max(per_day)) if per_day else None,
        'unique_days': len(per_day), 'missing_by_column': dict(missing),
        'duplicate_date_period_rows': duplicates, 'missing_days': missing_days,
        'out_of_year_days': extra_days, 'invalid_rows': invalid_rows,
        'invalid_nd_lines': invalid_nd, 'nonpositive_nd_count': sum(v <= 0 for v in values),
        'nd_min_mw': min(values) if values else None, 'nd_max_mw': max(values) if values else None,
        'period_count_distribution': dict(sorted(Counter(per_day.values()).items())),
        'clock_change_days': {str(day): count for day, count in sorted(per_day.items()) if count != 48},
        'unexpected_period_days': period_issues, 'structural_checks_passed': passed,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true', help='Verify local files without network access')
    parser.add_argument('--resume', action='store_true', help='Retry an interrupted download; existing CSV bytes must match the server')
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    manifest_path = META / 'download_manifest.json'
    if args.offline:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    else:
        package = json.loads(fetch(API))
        if not package.get('success'):
            raise RuntimeError('NESO metadata request failed')
        resources = package['result']['resources']
        write_json(META / 'source_package.json', package)
        selected = []
        for year in YEARS:
            matches = [r for r in resources if r['name'] == f'Historic Demand Data {year}' and r['format'].upper() == 'CSV']
            if len(matches) != 1:
                raise ValueError(f'{year}: expected exactly one CSV resource, got {len(matches)}')
            selected.append((year, matches[0]))
        if not args.resume and any((RAW / f'demanddata_{year}.csv').exists() for year in YEARS):
            raise FileExistsError('Raw snapshot already exists. Use --offline to verify it; do not overwrite the snapshot.')

        def download(item):
            year, resource = item
            payload = fetch(resource['url'])
            path = RAW / f'demanddata_{year}.csv'
            if path.exists() and path.read_bytes() != payload:
                raise ValueError(f'{year}: server data differ from the local snapshot; existing CSV has been preserved')
            # Validate a temporary file before publishing it as the original CSV.
            temporary = path.with_suffix('.csv.part')
            temporary.write_bytes(payload)
            check = audit(temporary, year)
            if not check['structural_checks_passed']:
                write_json(META / f'failed_audit_{year}.json', check)
                raise ValueError(f'{year}: downloaded CSV failed validation; see data/metadata/failed_audit_{year}.json')
            temporary.replace(path)
            return {'year': year, 'resource_id': resource['id'], 'source_url': resource['url'],
                    'source_last_modified': resource.get('last_modified'),
                    'downloaded_at_utc': datetime.now(timezone.utc).isoformat(),
                    'sha256': check['sha256'], 'bytes': len(payload)}

        with ThreadPoolExecutor(max_workers=4) as executor:
            downloads = list(executor.map(download, selected))
        manifest = {'provider': 'NESO', 'dataset': 'Historic Demand Data', 'metadata_url': API,
                    'source_page': 'https://www.neso.energy/data-portal/historic-demand-data',
                    'license_title': package['result'].get('license_title'),
                    'license_url': package['result'].get('license_url'), 'files': downloads}
        write_json(META / 'source_package.json', package)
        write_json(manifest_path, manifest)
    audits = [audit(RAW / f'demanddata_{year}.csv', year) for year in YEARS]
    for check, record in zip(audits, manifest['files']):
        if record['year'] != check['year'] or record['sha256'] != check['sha256']:
            raise ValueError(f"Snapshot hash mismatch: {check['year']}")
    same_schema = all(check['columns'] == audits[0]['columns'] for check in audits)
    result = {'audited_at_utc': datetime.now(timezone.utc).isoformat(),
              'same_schema_all_years': same_schema, 'total_rows': sum(c['rows'] for c in audits),
              'all_checks_passed': all(c['structural_checks_passed'] for c in audits),
              'files': audits}
    write_json(META / 'collection_audit.json', result)
    print(json.dumps({key: value for key, value in result.items() if key != 'files'}, indent=2))
    for check in audits:
        print(json.dumps({key: check[key] for key in ('year', 'rows', 'first_settlement_date',
                         'last_settlement_date', 'bytes', 'structural_checks_passed')}, indent=2))
    if not result['all_checks_passed']:
        raise SystemExit('Data audit failed; inspect collection_audit.json')


if __name__ == '__main__':
    main()
