# AWS Script Usage Guide

This project uses Python scripts to rename .dat files into .csv files and generate a connection report from the data.

## What you need to install

This script does not require any third-party packages or libraries.

You only need:
- Python 3.8 or newer
- pip (usually installed automatically with Python)

The scripts use only Python built-in modules such as:
- argparse
- csv
- datetime
- logging
- pathlib
- sys

## Install Python

If Python is not installed yet, download it from:
https://www.python.org/downloads/

After installation, verify it with:

```cmd
py --version
```

## Create and activate a virtual environment (recommended)

Open Command Prompt and go to the project folder:

```cmd
cd "your porject folder"
```

Create a virtual environment:

```cmd
py -m venv .venv
```

Activate it:

```cmd
.venv\Scripts\activate
```

## Install required packages and libraries

No extra package installation is required for this project.

However, make sure pip is available and up to date:

```cmd
python -m pip install --upgrade pip
```

If you want to check installed packages, you can run:

```cmd
python -m pip list
```

## Run the script

### 1. Preview changes without changing files

```cmd
python report_script.py --dir test_file --dry-run
```

### 2. Run the script for real

```cmd
python report_script.py --dir test_file
```

### 3. Use the standalone rename helper

```cmd
python rename_dat_to_csv.py --dir test_file --recursive
```

## Useful options

- --dir or -d: choose the folder to scan
- --dry-run: preview changes without renaming files
- --no-recursive: search only the selected folder
- --recursive or -r: search subfolders as well
- --log-file: save log output to a file
- --wind-threshold: change the wind warning threshold

## Output file

After running the main script, the report will be created here:

```cmd
reports\connection_report.csv
```

The report is written with a UTF-8 BOM so Excel on Windows opens Thai text correctly.

## Notes

- If a target .csv file already exists, the script will skip that file.
- It is recommended to run with --dry-run first before making real changes.
