# Trade File Organizer

A simple Python tool to organize, validate, and save your trade CSV files into daily, weekly, or monthly grouped files.  
Ideal for traders who want to automate sorting and managing trade exports.

---

## Features

- Combine multiple raw trade CSV files from a folder
- Validate required fields are present and complete
- Group trades by day, week, or month
- Save grouped trades as separate CSV files
- Ignore incomplete or malformed rows
- Organize output files into a dedicated folder

---

## Getting Started

### Prerequisites

- Python 3.8 or higher installed
- (Optional) Virtual environment recommended

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/trade-file-organizer.git
   cd trade-file-organizer
   ```

### Usage

1. Place your raw trade CSV files in a folder (e.g., Downloads/).

2. Modify the script to set your input and output directories:

```
DOWNLOADS_DIR = "/path/to/your/raw/trades"
TRADES_DIR = "/path/to/save/organized/trades"
```

3. Run the script:
   ```
   python file_organizer.py
   ```
   The script will:

- Combine CSVs

- Validate and filter rows

- Group trades by day, week, or month

- Save organized CSV files in the output folder
