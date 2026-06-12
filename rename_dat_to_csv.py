from pathlib import Path
import argparse
import sys


def rename_dat_to_csv(dir_path: Path, recursive: bool = False, dry_run: bool = False):
    if not dir_path.exists() or not dir_path.is_dir():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    pattern = "**/*.dat" if recursive else "*.dat"
    files = list(dir_path.glob(pattern))

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
    parser = argparse.ArgumentParser(description='Rename .dat files to .csv in a folder')
    parser.add_argument('--dir', '-d', default='test_file', help='Directory containing .dat files')
    parser.add_argument('--recursive', '-r', action='store_true', help='Rename files recursively')
    parser.add_argument('--dry-run', action='store_true', help="Show what would be renamed without changing files")

    args = parser.parse_args(argv)
    dir_path = Path(args.dir)

    try:
        renamed, skipped = rename_dat_to_csv(dir_path, recursive=args.recursive, dry_run=args.dry_run)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(2)

    if renamed:
        print('Renamed files:')
        for src, dst in renamed:
            print(f'  {src} -> {dst}')
    else:
        print('No .dat files found to rename.')

    if skipped:
        print('\nSkipped (target exists):')
        for src, dst in skipped:
            print(f'  {src} -> {dst}')

    print(f'\nSummary: {len(renamed)} renamed, {len(skipped)} skipped.')


if __name__ == '__main__':
    main()
