from pathlib import Path
import argparse
import datetime
import logging
import sys


def setup_logging(log_file: str | None = None, level=logging.INFO):
	handlers = [logging.StreamHandler(sys.stdout)]
	logging.basicConfig(level=level, format='%(asctime)s %(levelname)s %(message)s', handlers=handlers)
	if log_file:
		fh = logging.FileHandler(log_file)
		fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
		logging.getLogger().addHandler(fh)


# Prefer importing the standalone renamer if available, otherwise provide a fallback.
try:
	from rename_dat_to_csv import rename_dat_to_csv as _rename_func
except Exception:
	def _rename_func(dir_path: Path, recursive: bool = False, dry_run: bool = False):
		if not Path(dir_path).exists() or not Path(dir_path).is_dir():
			raise FileNotFoundError(f"Directory not found: {dir_path}")
		pattern = "**/*.dat" if recursive else "*.dat"
		files = list(Path(dir_path).glob(pattern))
		renamed = []
		skipped = []
		for f in files:
			if not f.is_file():
				continue
			target = f.with_suffix('.csv')
			if target.exists():
				skipped.append((f, target))
				continue
			if not dry_run:
				f.rename(target)
			renamed.append((f, target))
		return renamed, skipped


def main(argv=None):
	parser = argparse.ArgumentParser(description='Report script — first step: rename .dat to .csv')
	parser.add_argument('--dir', '-d', default='test_file', help='Directory containing .dat files')
	parser.add_argument('--dry-run', action='store_true', help='Show changes without renaming files')
	parser.add_argument('--no-recursive', action='store_true', help='Disable recursive search (default: recursive)')
	parser.add_argument('--log-file', help='Optional log file path')
	parser.add_argument('--wind-threshold', type=int, default=12, help='Number of consecutive zero-wind rows needed to flag sensor ลมเสีย')

	args = parser.parse_args(argv)
	setup_logging(args.log_file)

	dir_path = Path(args.dir)
	if not dir_path.exists() or not dir_path.is_dir():
		logging.error('Directory not found: %s', dir_path)
		sys.exit(2)

	recursive = not args.no_recursive

	logging.info('Starting rename step — dir=%s recursive=%s dry_run=%s', dir_path, recursive, args.dry_run)

	try:
		renamed, skipped = _rename_func(dir_path, recursive=recursive, dry_run=args.dry_run)
	except FileNotFoundError as e:
		logging.error(str(e))
		sys.exit(2)

	for src, dst in renamed:
		logging.info('Renamed: %s -> %s', src, dst)

	for src, dst in skipped:
		logging.warning('Skipped (target exists): %s -> %s', src, dst)

	logging.info('Summary: %d renamed, %d skipped', len(renamed), len(skipped))
	if args.dry_run:
		logging.info('Dry-run mode: no files were changed')

	# Generate status report for each file.
	generate_daily_report(dir_path, out_dir=Path('reports'), wind_threshold=args.wind_threshold)


def _find_header_row(lines):
	for i, line in enumerate(lines[:10]):
		if 'TIMESTAMP' in line or 'Timestamp' in line:
			return i
	return None


def _parse_csv_dicts(path: Path):
	import csv

	for encoding in ('utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'cp1252'):
		try:
			with path.open('r', newline='', encoding=encoding) as fh:
				lines = fh.readlines()
			break
		except UnicodeDecodeError:
			continue
	else:
		raise UnicodeDecodeError('utf-8', b'', 0, 1, 'Unable to decode file')

	if not lines:
		return

	header_row_index = _find_header_row(lines)
	if header_row_index is None or header_row_index >= len(lines) - 1:
		return

	header_line = lines[header_row_index].lstrip('\ufeff')
	hdr = next(csv.reader([header_line]))
	data_lines = lines[header_row_index + 1:]
	reader = csv.DictReader(data_lines, fieldnames=hdr)
	for row in reader:
		yield row


def _safe_float(x):
	try:
		if x is None:
			return None
		s = str(x).strip()
		if s == '':
			return None
		return float(s)
	except Exception:
		return None


def generate_daily_report(dir_path: Path, out_dir: Path = Path('reports'), wind_threshold: int = 30):
	out_dir.mkdir(parents=True, exist_ok=True)
	rows = []

	csv_files = sorted(dir_path.glob('*.csv'))
	if not csv_files:
		logging.warning('No CSV files found in %s to report on', dir_path)
		return

	today = datetime.date.today().isoformat()

	for f in csv_files:
		name = f.stem.split('_')[0]
		parsed = list(_parse_csv_dicts(f))

		# Determine latest valid day in the file
		import re
		valid_dates = [
			(r.get('TIMESTAMP') or r.get('Timestamp') or r.get('TOA5') or '').split(' ')[0]
			for r in parsed
		]
		valid_dates = [d for d in valid_dates if re.match(r'^\d{4}-\d{2}-\d{2}$', d)]
		latest_day = max(valid_dates) if valid_dates else None

		connection = 'FAIL'
		remark = ''
		if latest_day is None:
			connection = 'FAIL'
			remark = ''
		elif latest_day == today:
			connection = 'OK'
			# build remark list for today's data
			problems = []
			day_rows = [r for r in parsed if (r.get('TIMESTAMP') or r.get('Timestamp') or r.get('TOA5') or '').startswith(latest_day)]

			batt_low = False
			rh_bad_count = 0
			airtc_bad_count = 0
			wind_bad = False
			wind_zero_run = 0
			bp_bad = False

			batt_key = next((k for k in parsed[0].keys() if 'BatteryVolts' in k or k == 'Volts' or 'Volts' in k), None) if parsed else None
			airtc_key = next((k for k in parsed[0].keys() if 'AirTC' in k or 'PTemp' in k or 'AirT' in k), None) if parsed else None
			rh_key = next((k for k in parsed[0].keys() if k.strip().lower().startswith('rh') or 'RH' in k), None) if parsed else None
			bp_key = next((k for k in parsed[0].keys() if 'BP_mmHg' in k or 'BP' in k), None) if parsed else None
			w1_key = next((k for k in parsed[0].keys() if 'WVc(1)' in k or ('WVc' in k and '(1)' in k)), None) if parsed else None
			w2_key = next((k for k in parsed[0].keys() if 'WVc(2)' in k or ('WVc' in k and '(2)' in k)), None) if parsed else None
			wmax_key = next((k for k in parsed[0].keys() if 'Max' in k and ('WS' in k or 'ws' in k)), None) if parsed else None

			for row in day_rows:
				ts = (row.get('TIMESTAMP') or row.get('Timestamp') or row.get('TOA5') or '').strip()
				if not ts:
					continue
				parts = ts.split(' ')
				if len(parts) < 2:
					time_part = ''
				else:
					time_part = parts[1]
				hour = None
				if time_part:
					try:
						hour = int(time_part.split(':')[0])
					except Exception:
						hour = None

				batt_val = _safe_float(row.get(batt_key)) if batt_key else None
				if hour is not None and 7 <= hour < 17 and batt_val is not None and batt_val < 10:
					batt_low = True

				rh_val = _safe_float(row.get(rh_key)) if rh_key else None
				if rh_val is not None and (rh_val == 0 or 99 <= rh_val <= 100):
					rh_bad_count += 1

				bp_val = _safe_float(row.get(bp_key)) if bp_key else None
				if bp_val is not None and bp_val < 500:
					bp_bad = True

				airtc_val = _safe_float(row.get(airtc_key)) if airtc_key else None
				if airtc_val is not None and airtc_val < 0:
					airtc_bad_count += 1

				w1_val = _safe_float(row.get(w1_key)) if w1_key else None
				w2_val = _safe_float(row.get(w2_key)) if w2_key else None
				wmax_val = _safe_float(row.get(wmax_key)) if wmax_key else None
				if w1_val == 0 and w2_val == 0 and wmax_val == 0 and w1_val is not None and w2_val is not None and wmax_val is not None:
					wind_zero_run += 1
				else:
					wind_zero_run = 0
				if wind_zero_run >= wind_threshold:
					wind_bad = True

			# Determine remarks
			if batt_low:
				problems.append('Batterry Low')
			if rh_bad_count * 10 >= 360:
				problems.append('RH เสีย')
			if bp_bad:
				problems.append('ความกด เสีย')
			if airtc_bad_count * 10 >= 60:
				problems.append('AirTC_Avg เสีย')
			if wind_bad:
				problems.append('sensor ลมเสีย')

			remark = ', '.join(problems)
		else:
			connection = 'FAIL'
			remark = latest_day or ''

		rows.append({'Name': name, 'Connection': connection, 'Remark': remark})

	out_csv = out_dir / 'connection_report.csv'
	import csv
	fieldnames = ['Name', 'Connection', 'Remark']
	with out_csv.open('w', newline='', encoding='utf-8-sig') as fh:
		writer = csv.DictWriter(fh, fieldnames=fieldnames)
		writer.writeheader()
		for r in rows:
			writer.writerow(r)

	logging.info('Wrote report: %s', out_csv)


if __name__ == '__main__':
	main()

