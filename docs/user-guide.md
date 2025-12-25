# User Guide

This guide explains how to use the Swiggy App Store Review Trend Analysis System for analyzing app reviews and generating trend reports.

## Table of Contents

1. [Command Line Interface (CLI)](#command-line-interface-cli)
2. [Web Dashboard](#web-dashboard)
3. [Understanding the Output](#understanding-the-output)
4. [Common Workflows](#common-workflows)
5. [Advanced Usage](#advanced-usage)

## Command Line Interface (CLI)

The CLI is ideal for automation, scripting, and batch processing.

### Basic Usage

```bash
# Analyze Swiggy reviews for the last 30 days
python main.py
```

This will:
1. Prompt you for app ID (press Enter for Swiggy default)
2. Prompt you for target date (press Enter for today)
3. Scrape reviews from the last 30 days
4. Extract and consolidate topics
5. Generate Excel report in `output/` folder

### Command-Line Arguments

Skip the interactive prompts by providing arguments:

```bash
python main.py --target-date 2024-12-25 --days 30 --app-id in.swiggy.android
```

#### Available Arguments

| Argument | Description | Default | Example |
|----------|-------------|---------|---------|
| `--target-date` | End date for analysis (YYYY-MM-DD) | Today | `2024-12-25` |
| `--days` | Number of days to analyze | 30 | `7`, `14`, `60` |
| `--app-id` | App package ID or Play Store URL | `in.swiggy.android` | `com.application.zomato` |

### Interactive Prompts

If you run without arguments, the system will ask:

```
Enter app package ID (e.g., in.swiggy.android) or Play Store link,
or press Enter for Swiggy:
```

You can:
- **Press Enter**: Use Swiggy app
- **Enter package ID**: e.g., `com.application.zomato`
- **Paste Play Store URL**: e.g., `https://play.google.com/store/apps/details?id=com.application.zomato`

```
Enter target date (YYYY-MM-DD) or press Enter for today:
```

You can:
- **Press Enter**: Use today's date
- **Enter date**: e.g., `2024-12-15`

### Reading the CLI Output

#### Phase 1: Data Collection
```
PHASE 1: Data Collection
----------------------------------------
Scraping reviews from 2024-11-26 to 2024-12-25...

Checking cache...
  ✓ Loaded 5000 cached reviews for in.swiggy.android
    Last updated: 2024-12-25
  Cache is fresh (less than 1 day old)

Filtering reviews for 2024-11-26 to 2024-12-25...
✓ Found 4523 reviews within date range
```

**What this means**:
- System found cached reviews (faster than re-scraping)
- Filtered to your specified date range
- Found 4523 reviews to analyze

#### Phase 2: Topic Extraction
```
PHASE 2: Topic Extraction
----------------------------------------
Extracting topics from reviews (using parallel batch processing)...
  Configuration: 20 reviews/batch, 8 parallel workers
  Total reviews: 4523
  Total batches: 227
  Note: This will take ~85 seconds (API dependent)

    → Processing batch 0 (20 reviews)...
    ✓ Batch 0 complete (87 topics extracted)
  Processed 1000/4523 reviews | Elapsed: 30s | ETA: 105s | Rate: 33/s

✓ Extracted topics from 4523 reviews using ULTRA-FAST parallel processing
  Total time: 135 seconds (2.3 minutes)
  Average rate: 33 reviews/second
```

**What this means**:
- Processing 20 reviews at a time
- Using 8 parallel workers for speed
- Extracted topics from all reviews
- Achieved 33 reviews/second throughput

#### Phase 3: Topic Consolidation
```
PHASE 3: Topic Consolidation
----------------------------------------
Consolidating 342 unique topics...
  After normalization: 187 topic groups
✓ Consolidated to 18 canonical topics

📋 Canonical Topics (18):
  1. Delivery delay (24 variations)
  2. Food temperature issues (12 variations)
  3. Positive feedback (31 variations)
  4. App crashes/freezes (8 variations)
  ...
```

**What this means**:
- Found 342 unique topics across all reviews
- After normalization, grouped to 187
- Final consolidation: 18 canonical topics
- Shows variation count for each topic

#### Phase 4: Trend Analysis
```
PHASE 4: Trend Analysis
----------------------------------------

📊 VALIDATION REPORT:
  Expected canonical topics: 18
  Topics appearing in Excel: 18
  ✅ Perfect match! All topics mapped correctly.
```

**What this means**:
- All extracted topics successfully mapped
- No unmapped or orphaned topics
- Data integrity verified

#### Phase 5: Report Generation
```
PHASE 5: Report Generation
----------------------------------------
Generating trend report for 2024-12-25...
✓ Report saved to output/swiggy_trend_report_2024-12-25.xlsx

==============================================================
✓ Analysis Complete!
==============================================================
Output saved to: output/swiggy_trend_report_2024-12-25.xlsx
```

**What this means**:
- Excel report created successfully
- Located in `output/` folder
- Ready to open in Excel or Google Sheets

### CLI Examples

#### Example 1: Analyze Last 7 Days
```bash
python main.py --days 7
```

Use case: Quick weekly review

#### Example 2: Specific Date Range
```bash
python main.py --target-date 2024-12-15 --days 14
```

Use case: Analyze specific two-week period

#### Example 3: Different App (Zomato)
```bash
python main.py --app-id com.application.zomato
```

Use case: Competitive analysis

#### Example 4: Using Play Store URL
```bash
python main.py --app-id "https://play.google.com/store/apps/details?id=com.application.zomato"
```

Use case: Convenient URL copy-paste

## Web Dashboard

The web dashboard provides an interactive interface with real-time progress tracking and data visualization.

### Starting the Dashboard

```bash
python app.py
```

Expected output:
```
==============================================================
Swiggy App Store Review Trend Analysis - Web Dashboard
==============================================================

🚀 Starting Flask server...
📊 Dashboard: http://localhost:8000
📡 API Docs: http://localhost:8000/api/jobs

 * Running on http://0.0.0.0:8000
```

Open your browser to `http://localhost:8000`

### Dashboard Interface

#### 1. Analysis Form

**Fields**:
- **App Package ID / Play Store URL**:
  - Enter package ID (e.g., `in.swiggy.android`)
  - Or paste Play Store URL
  - Leave blank for Swiggy default

- **Target Date**:
  - Select end date for analysis
  - Defaults to today

- **Number of Days**:
  - Select analysis window (7, 14, 30, 60, or 90 days)
  - Defaults to 30 days

**Button**:
- **Start Analysis**: Begins analysis job

#### 2. Progress Tracking

Once you start an analysis, you'll see:

```
Status: Running
Phase: Topic Extraction
Progress: ████████████░░░░░░░░ 60%
Message: Extracting topics from 3000/5000 reviews...

Metrics:
  Processed: 3000
  Total: 5000
```

**Progress Phases**:
1. **Initializing** (0%)
2. **Data Collection** (10-20%)
3. **Topic Extraction** (30-50%)
4. **Topic Consolidation** (60-75%)
5. **Trend Analysis** (80-85%)
6. **Report Generation** (90-100%)
7. **Complete** (100%)

#### 3. Results Visualization

When analysis completes, you'll see:

**Summary Statistics**:
```
Total Reviews Analyzed: 4,523
Unique Topics Found: 18
Date Range: Nov 26, 2024 - Dec 25, 2024
```

**Line Chart**: Topic trends over time
- Shows top 10 topics
- Interactive (hover for details)
- Multiple colored lines

**Bar Chart**: Top 15 topics by total mentions
- Sorted by frequency
- Shows total count

**Topics Table**: All topics with details
- Topic name
- Total mentions
- Variation count
- Sortable columns

#### 4. Download Report

Click **Download Excel Report** button to get `.xlsx` file

### Web Dashboard Examples

#### Example 1: Quick Analysis

1. Open `http://localhost:8000`
2. Leave all fields default
3. Click "Start Analysis"
4. Wait for completion (~3-5 minutes)
5. View charts and download report

#### Example 2: Custom Date Range

1. Open dashboard
2. Select "Target Date": 2024-12-15
3. Select "Days": 14
4. Click "Start Analysis"
5. View results for Dec 1-15, 2024

#### Example 3: Competitor Analysis

1. Open dashboard
2. Enter "App ID": `com.application.zomato`
3. Click "Start Analysis"
4. Compare results with Swiggy

### API Health Check

Before starting analysis, check LLM status:

Visit `http://localhost:8000/api/health/llm` to see:

```json
{
  "status": "ok",
  "message": "Ollama is ready",
  "provider": "ollama",
  "models": ["qwen2.5:32b", "llama3.1:70b"],
  "extraction_model": "qwen2.5:32b",
  "consolidation_model": "llama3.1:70b"
}
```

**Status Codes**:
- `ok`: Ready to use
- `warning`: Missing models (shows instructions)
- `error`: Cannot connect to LLM

## Understanding the Output

### Excel Report Format

The generated Excel file has the following structure:

```
┌─────────────────────────────┬─────────┬─────────┬─────────┬─────────┐
│ Topic                       │ Nov 26  │ Nov 27  │ ...     │ Dec 25  │
├─────────────────────────────┼─────────┼─────────┼─────────┼─────────┤
│ Delivery delay              │   12    │   15    │   ...   │   18    │
│ Food temperature issues     │    8    │    7    │   ...   │   11    │
│ Positive feedback           │   25    │   28    │   ...   │   30    │
│ App crashes/freezes         │    3    │    5    │   ...   │    4    │
│ Delivery partner unprofessional │  6  │    4    │   ...   │    7    │
└─────────────────────────────┴─────────┴─────────┴─────────┴─────────┘
```

**Column Meanings**:
- **Topic**: Canonical topic name
- **Dates**: Each column represents one day
- **Numbers**: Count of mentions for that topic on that date

**Color Coding**:
- **Blue header**: Column headers
- **Alternating rows**: Light blue for readability
- **Yellow highlight**: Unmapped topics (if any)

### Interpreting Results

#### Identifying Trends

**Rising Issues** (numbers increasing left to right):
```
Delivery delay: 5 → 8 → 12 → 15 → 18
```
Action: Investigate delivery operations

**Declining Issues** (numbers decreasing):
```
App crashes: 15 → 12 → 8 → 5 → 3
```
Indicates: Recent fixes working

**Spike Detection** (sudden jump):
```
Food quality issues: 5 → 5 → 6 → 25 → 24
```
Action: Check what changed around spike date

#### Topic Categories

Topics are categorized as:
- **Issues**: Problems users report (e.g., "delivery delay", "app crashes")
- **Requests**: Features users want (e.g., "24/7 service", "express delivery")
- **Feedback**: General comments (e.g., "positive feedback", "pricing concerns")

#### Validation Warnings

If you see:
```
⚠️ Yellow-highlighted topics are unmapped (not in canonical list)
```

This means some topics weren't consolidated. Review them to decide if they should be merged with existing topics.

### Chart Interpretations

#### Line Chart (Web Dashboard)

**What it shows**: Topic trends over time

**How to read**:
- **X-axis**: Dates
- **Y-axis**: Mention count
- **Lines**: Each line is a topic
- **Hover**: See exact values

**Patterns to look for**:
- **Upward trend**: Growing issue
- **Downward trend**: Improving situation
- **Spikes**: Sudden events
- **Flat lines**: Stable issues

#### Bar Chart (Web Dashboard)

**What it shows**: Top topics by total mentions

**How to read**:
- **X-axis**: Topic names
- **Y-axis**: Total mentions across all days
- **Bars**: Sorted by frequency (highest first)

**Use cases**:
- Identify most common issues
- Prioritize product roadmap
- Allocate support resources

## Common Workflows

### Workflow 1: Weekly Review Meeting

**Goal**: Present weekly trends to team

**Steps**:
1. Monday morning: Run analysis for last 7 days
   ```bash
   python main.py --days 7
   ```
2. Open Excel report
3. Identify top 5 issues
4. Check for trend changes (vs previous week)
5. Present findings in meeting

**Time**: ~5 minutes (plus analysis runtime)

### Workflow 2: Product Feature Prioritization

**Goal**: Decide which features to build based on user requests

**Steps**:
1. Run 30-day analysis
   ```bash
   python main.py --days 30
   ```
2. Filter Excel for "request" category topics
3. Sort by total mentions
4. Review top requests
5. Create product backlog items

**Time**: ~15 minutes

### Workflow 3: Incident Response

**Goal**: Investigate sudden spike in complaints

**Steps**:
1. Run analysis for affected period
   ```bash
   python main.py --target-date 2024-12-20 --days 7
   ```
2. Look for spikes in Excel report
3. Identify specific topic with spike
4. Cross-reference with deployment logs
5. Plan remediation

**Time**: ~10 minutes

### Workflow 4: Competitive Analysis

**Goal**: Compare your app with competitor

**Steps**:
1. Analyze your app (Swiggy)
   ```bash
   python main.py --app-id in.swiggy.android
   ```
2. Analyze competitor (Zomato)
   ```bash
   python main.py --app-id com.application.zomato
   ```
3. Compare Excel reports
4. Identify gaps and opportunities

**Time**: ~20 minutes (two analyses)

### Workflow 5: Monthly Report

**Goal**: Generate monthly trend report for stakeholders

**Steps**:
1. Run 30-day analysis
2. Start web dashboard: `python app.py`
3. Run analysis through web UI
4. Export charts as images (screenshot)
5. Download Excel report
6. Create slide deck with charts + Excel data

**Time**: ~30 minutes

## Advanced Usage

### Custom Date Ranges

Analyze specific periods:

```bash
# Black Friday weekend
python main.py --target-date 2024-11-29 --days 3

# Holiday season
python main.py --target-date 2024-12-31 --days 14

# Quarter analysis
python main.py --days 90
```

### Multiple Apps

Batch analyze multiple apps:

```bash
#!/bin/bash
# analyze_all.sh

apps=(
  "in.swiggy.android"
  "com.application.zomato"
  "com.ubercab.eats"
)

for app in "${apps[@]}"; do
  echo "Analyzing $app..."
  python main.py --app-id "$app" --days 30
done
```

### Automated Scheduling

Set up cron job for daily analysis:

```bash
# Edit crontab
crontab -e

# Add daily 2 AM analysis
0 2 * * * cd /path/to/project && /path/to/venv/bin/python main.py --days 7
```

### Cache Management

Control caching behavior:

```bash
# Force fresh data (delete cache first)
rm -rf cache/in.swiggy.android/
python main.py

# Preserve cache for faster repeat runs
python main.py  # Uses cache if <24 hours old
```

### Export Formats

While the system generates Excel by default, you can convert:

```python
# In Python script
import pandas as pd

# Read Excel
df = pd.read_excel('output/swiggy_trend_report_2024-12-25.xlsx')

# Export to CSV
df.to_csv('output/report.csv', index=False)

# Export to JSON
df.to_json('output/report.json', orient='records')
```

### API Integration

Use the web API programmatically:

```python
import requests
import time

# Start analysis
response = requests.post('http://localhost:8000/api/analyze', json={
    'app_id': 'in.swiggy.android',
    'target_date': '2024-12-25',
    'days': 30
})
job_id = response.json()['job_id']

# Poll status
while True:
    status = requests.get(f'http://localhost:8000/api/status/{job_id}').json()
    if status['status'] == 'completed':
        break
    print(f"Progress: {status['progress_pct']}%")
    time.sleep(5)

# Download report
report = requests.get(f'http://localhost:8000/api/download/{job_id}')
with open('report.xlsx', 'wb') as f:
    f.write(report.content)
```

## Tips & Best Practices

### Performance Tips

1. **Use cache**: Don't delete cache unless necessary
2. **Smaller date ranges**: 7-14 days process faster than 30-90 days
3. **Off-peak analysis**: Run during low-traffic hours
4. **GPU acceleration**: Use GPU-enabled Ollama for 5-10x speedup

### Data Quality Tips

1. **Regular runs**: Weekly analyses capture more data
2. **Consistent dates**: Compare same weekdays (Mon-Sun, not Tue-Mon)
3. **Seasonal awareness**: Account for holidays, sales, events
4. **Validate unmapped**: Review yellow-highlighted topics in Excel

### Troubleshooting Tips

1. **Check LLM status**: Visit `/api/health/llm` before starting
2. **Clear cache**: Delete cache if data looks stale
3. **Check logs**: Read console output for errors
4. **Reduce workers**: Lower from 8 to 4 if API errors occur

## Next Steps

- **Learn the architecture**: See [Architecture](architecture.md)
- **Explore the API**: See [API Reference](api-reference.md)
- **Understand data flow**: See [Data Flow](data-flow.md)
- **Fix issues**: See [Troubleshooting](troubleshooting.md)
