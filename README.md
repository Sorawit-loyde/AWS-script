# AWS Script README

This project contains Python scripts to help you rename .dat files to .csv files and generate a daily connection report from the CSV data.

## What this project does

- Renames .dat files to .csv
- Supports recursive scanning of folders
- Creates a report file in the reports folder
- Supports dry-run mode to preview changes safely

## Files in this project

- report_script.py: Main script that renames files and generates the connection report
- rename_dat_to_csv.py: Standalone helper script for renaming .dat files
- test_file/: Sample folder used for testing
- reports/: Output folder for generated reports

## Requirements

- Python 3.8 or newer
- Windows Command Prompt (cmd) or PowerShell

This project uses only Python standard library modules, so no extra third-party packages are required.

## Step-by-step installation in Windows CMD

1. Open Command Prompt

2. Go to the project folder

```cmd
cd /d C:\Users\User\Desktop\Script Tee\AWS-script
```

3. Check Python version

```cmd
py --version
```

If Python is not installed, install it first from: https://www.python.org/downloads/

4. Create a virtual environment (recommended)

```cmd
py -m venv .venv
```

5. Activate the virtual environment

```cmd
.venv\Scripts\activate
```

6. Upgrade pip

```cmd
python -m pip install --upgrade pip
```

## Run the script

### Option 1: Run the main report script

This will rename .dat files and generate the report.

```cmd
python report_script.py --dir test_file
```

### Option 2: Preview changes without changing files

```cmd
python report_script.py --dir test_file --dry-run
```

### Option 3: Disable recursive search

```cmd
python report_script.py --dir test_file --no-recursive
```

### Option 4: Use the standalone rename helper directly

```cmd
python rename_dat_to_csv.py --dir test_file --recursive
```

## Useful options

- --dir or -d: Choose the folder to scan
- --dry-run: Show what would happen without making changes
- --no-recursive: Search only the top-level folder
- --recursive or -r: Search subfolders as well
- --log-file: Save logs to a file
- --wind-threshold: Set the threshold for wind-related warnings

## Output

After running the main script, the report will be created in:

```cmd
reports\connection_report.csv
```

## Example workflow

```cmd
cd /d C:\Users\User\Desktop\Script Tee\AWS-script
.venv\Scripts\activate
python report_script.py --dir test_file --dry-run
python report_script.py --dir test_file
```

## Notes

- If a target .csv file already exists, the script will skip that file.
- If you want to keep the original files untouched, always use --dry-run first.
- Logs can be written to a file with the --log-file option.
