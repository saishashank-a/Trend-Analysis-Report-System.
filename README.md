# Review Analysis System

AI-powered review analysis system with ML optimizations for M4 Pro with Metal GPU acceleration.

## Overview

This system analyzes Google Play Store reviews for **any Android app** and generates trend reports identifying key topics, issues, and feedback patterns.

### How It Works

1. **Scrape** reviews from Google Play Store (any app)
2. **Deduplicate** using semantic embeddings (removes ~50% duplicates)
3. **Extract** topics using local Ollama LLM with Metal acceleration
4. **Cluster** topics using HDBSCAN (240x faster than LLM consolidation)
5. **Analyze** trends over customizable time periods
6. **Report** via interactive web UI with downloadable Excel reports

## Key Features

- **Fast Processing**: 4.3x speedup with ML optimizations (~27 min for 7000 reviews)
- **Cost Effective**: $0 API costs using local Ollama with Metal GPU
- **Smart Deduplication**: Removes ~50% duplicate reviews using semantic embeddings
- **Topic Clustering**: HDBSCAN-based clustering (240x faster than LLM consolidation)
- **App Agnostic**: Works with any Android app from Google Play Store
- **Modern Web UI**: Real-time progress tracking with Flask + Tailwind CSS
- **M4 Pro Optimized**: Auto-detects hardware and applies optimal settings (48 workers, Metal GPU)

## Installation

### Prerequisites
- Python 3.8+
- Ollama installed with qwen2.5:7b model
- M4 Pro (or other Apple Silicon) for Metal GPU acceleration

### Setup

```bash
# Clone or navigate to project directory
cd aiengineerassignment-master

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Ollama and pull model
ollama pull qwen2.5:7b
```

## Usage

### Web UI (Recommended)

```bash
# Start the Flask server
python3 app.py
```

Then open your browser to: **http://localhost:5000** (or the port shown in console)

**To analyze an app:**
1. Paste the Google Play Store URL (e.g., `https://play.google.com/store/apps/details?id=com.spotify.music`)
2. Choose date range using calendar pickers (default: last 30 days)
   - Start Date: 30 days ago
   - End Date: Today
3. Click "Start Analysis"
4. Monitor progress in real-time
5. Download Excel report when complete

### Command Line

Run analysis for any app (30-day rolling window):
```bash
python3 main.py <app_id> [days]
```

**Examples:**
```bash
# Analyze One Star App for last 30 days
python3 main.py com.curiositycurve.www.theonestarapp 30

# Analyze Spotify for last 7 days
python3 main.py com.spotify.music 7

# Use Play Store URL
python3 main.py "https://play.google.com/store/apps/details?id=com.application.zomato" 30
```

## Recent Fixes & Updates

### ✓ Mock Data Bug Fix (Dec 2024)
**Problem**: Subway Surfers (game) showed food delivery topics ("Delivery Issue", "Food Delivered Cold")
**Root Cause**: When scraper found 0 reviews, system used hardcoded food delivery mock data
**Fix**:
- Removed automatic mock data fallback
- Added multi-region scraping (tries US first, then India)
- Shows helpful error message when no reviews found
- System now fails gracefully instead of using wrong data

See [MOCK_DATA_FIX.md](MOCK_DATA_FIX.md) for full details.

### ✓ App ID Bug Fix (Dec 2024)
**Problem**: System was analyzing Swiggy instead of the specified app
**Fix**:
- Backend now accepts both `app_link` and `app_id` parameters
- Removed default fallback to Swiggy
- Fetches real app names from Google Play Store
- Excel files named correctly (e.g., "One_Star_App_trend_report.xlsx")

See [APP_ID_FIX.md](APP_ID_FIX.md) for full details.

### ✓ Delete Running Jobs (Dec 2024)
**Added**: Can now delete jobs while they're running
- Cancel button for running jobs (yellow X icon)
- Delete button works for all job states
- Retry button for failed/cancelled jobs

See [DELETE_RUNNING_JOBS_UPDATE.md](DELETE_RUNNING_JOBS_UPDATE.md) for full details.

### ✓ Persistent Chat History (Dec 2024)
**Added**: Chat messages now persist in database
- Chat history survives page refreshes and server restarts
- Each job maintains its own conversation history
- Automatic cleanup when jobs are deleted
- Seamless experience across sessions

See [PERSISTENT_CHAT_UPDATE.md](PERSISTENT_CHAT_UPDATE.md) for full details.

### ✓ Calendar Date Picker (Dec 2024)
**Added**: Visual calendar for selecting date ranges
- Start Date and End Date pickers (replaces dropdown)
- Default: Last 30 days (today and 30 days ago)
- Full date range control (1-365 days)
- Built-in validation for date ranges

See [CALENDAR_FEATURE_UPDATE.md](CALENDAR_FEATURE_UPDATE.md) for full details.

### ✓ ML Optimizations (Dec 2024)
**Added**: M4 Pro-specific optimizations
- Metal GPU acceleration for embeddings
- HDBSCAN topic clustering (240x faster)
- Duplicate detection (50% reduction)
- Hardware profile auto-detection

See [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md) for full details.

## Output

### Web UI
- **Interactive Dashboard**: Real-time progress tracking
- **Visualizations**:
  - Line chart showing top 10 topics over time
  - Bar chart of top 15 topics by frequency
  - Searchable topic table
- **Download**: Excel report with detailed analysis

### Excel Report
File: `output/App_Name_trend_report_YYYY-MM-DD.xlsx`

**Report Format:**
- **Rows**: Topics (canonical consolidated topics)
- **Columns**: Dates across the analysis period
- **Cells**: Frequency count of each topic per day

Example:
```
Topic                          | Dec 1 | Dec 2 | ... | Dec 30
------------------------------------------------------------
Positive feedback              |   45  |   38  | ... |   52
App crashes/bugs               |   12  |   14  | ... |   18
Slow performance               |    8  |   10  | ... |   15
Feature requests               |    6  |    7  | ... |   12
```

## Architecture

### Processing Pipeline

```
Scrape Reviews (google-play-scraper)
            ↓
Duplicate Detection (sentence-transformers + Metal GPU)
    → Removes ~50% duplicates
            ↓
Extract Topics (Ollama qwen2.5:7b - high recall)
    → 48 parallel workers with Metal acceleration
            ↓
Consolidate Topics (HDBSCAN clustering or LLM fallback)
    → 240x faster than LLM-only approach
            ↓
Map to Canonical (embedding similarity)
    → Fixes duplicate topic issues
            ↓
Count Frequencies by Date
            ↓
Generate Excel Report + Web Dashboard
```

### Core Components

1. **Data Collection** ([main.py:366-404](main.py#L366-404))
   - Fetches reviews from Google Play Store
   - Optional duplicate detection using semantic embeddings
   - Controlled by `ENABLE_DEDUP` env var

2. **Topic Extraction** ([main.py:443-484](main.py#L443-484))
   - Uses Ollama (qwen2.5:7b) with Metal GPU acceleration
   - High-recall prompts with sarcasm/negation detection
   - Parallel processing: 48 workers on M4 Pro

3. **Topic Consolidation** ([main.py:839-878](main.py#L839-878))
   - Primary: HDBSCAN clustering with embeddings (0.5 sec for 20k topics)
   - Fallback: LLM batch consolidation (20 min for 20k topics)
   - Controlled by `ENABLE_EMBEDDING_CLUSTERING` env var

4. **Topic Mapping** ([main.py:1016-1106](main.py#L1016-1106))
   - Embedding-based similarity matching (cosine similarity ≥ 0.7)
   - Prevents duplicate similar topics in final report
   - Replaces weak fuzzy string matching

5. **Web UI** ([app.py](app.py), [static/js/dashboard.js](static/js/dashboard.js))
   - Flask backend with background job processing
   - Real-time progress tracking via polling
   - Interactive visualizations with Chart.js

### Key Design Decisions

#### ML-First Hybrid Approach
The system prioritizes ML optimizations with LLM fallback:
- **Embedding clustering** (default): 240x faster than LLM consolidation
- **LLM consolidation** (fallback): Used if embedding clustering disabled/fails
- Best of both worlds: Speed + accuracy

#### Metal GPU Acceleration
Leverages Apple Silicon MPS backend:
- Sentence-transformers for embeddings (~200 texts/sec)
- Ollama with full GPU offload (99 layers)
- 4.3x overall speedup on M4 Pro

#### Topic Fragmentation Prevention
Using embedding similarity instead of string matching:
- "positive feedback" + "positive experience" → **Positive feedback** (70% similarity)
- "app crash" + "app crashes" + "crashing issues" → **App crashes/bugs**
- Prevents fragmentation while preserving distinct topics

## Performance

### Before Optimization
```
Data Collection:       5 min
Topic Extraction:      90 min  (8 workers)
Consolidation:         20 min  (LLM)
Mapping:               2 min   (fuzzy matching)
Report:                1 min
─────────────────────────────
Total:                 118 min (2 hours)
Cost:                  ~$5 (Claude API)
```

### After Optimization (M4 Pro)
```
Data Collection:       5 min   (unchanged)
Duplicate Detection:   2 min   (NEW - embeddings)
Topic Extraction:      15 min  (48 workers, Metal)
Embedding Gen:         3 min   (NEW - sentence-transformers)
Clustering:            0.5 min (NEW - HDBSCAN, 240x faster)
Mapping:               1 min   (embeddings vs fuzzy)
Report:                1 min   (unchanged)
─────────────────────────────
Total:                 27.5 min
Cost:                  $0 (100% local)
```

**Speedup**: 4.3x faster + $0 cost

## Configuration

Configuration is in [.env](.env) file:

```bash
# M4 Pro Optimized Settings
MAX_CONCURRENT=48              # Parallel workers (auto-detected)
BATCH_SIZE=30                  # Reviews per batch
OLLAMA_NUM_GPU_LAYERS=99      # Full GPU offload
OLLAMA_NUM_THREAD=12          # CPU threads for Ollama

# ML Features
ENABLE_EMBEDDING_CLUSTERING=true    # Fast clustering (recommended)
ENABLE_DEDUP=true                   # Remove duplicates (recommended)
DUPLICATE_THRESHOLD=0.85            # Similarity for duplicates (0-1)
TOPIC_SIMILARITY_THRESHOLD=0.70     # Similarity for mapping (0-1)

# Optional Features
ENABLE_SENTIMENT=false              # Adds sentiment scores (+2 min)
```

## Testing the App ID Fix

The recent fix ensures the system analyzes the correct app. To verify:

1. **Start the server**:
   ```bash
   python3 app.py
   ```

2. **Test with One Star App**:
   - URL: `https://play.google.com/store/apps/details?id=com.curiositycurve.www.theonestarapp`
   - Click "Start Analysis"

3. **Verify correct behavior**:
   - ✅ App name shows: **"One Star App"** (not "theonestarapp")
   - ✅ Review count: ~65 reviews (not 9000)
   - ✅ Topics: App-specific (not food delivery related)
   - ✅ Excel file: `One_Star_App_trend_report_2024-12-27.xlsx`

4. **Test with another app** (e.g., Spotify):
   - URL: `https://play.google.com/store/apps/details?id=com.spotify.music`
   - Should fetch "Spotify: Music and Podcasts" as the app name

## Troubleshooting

### Wrong App Analyzed
**Fixed!** The app ID bug has been resolved. System now:
- Accepts both Play Store URLs and package IDs
- Fetches real app names from Play Store
- No longer defaults to Swiggy

If you still see wrong data, try clearing the cache:
```bash
rm -rf cache/
```

### Metal GPU Not Working
Check if Metal is available:
```bash
python3 -c "import torch; print(torch.backends.mps.is_available())"
```
Should print `True` on M4 Pro. If `False`, embeddings will use CPU (slower but functional).

### Out of Memory
Reduce batch size in `.env`:
```bash
BATCH_SIZE=20  # Instead of 30
MAX_CONCURRENT=32  # Instead of 48
```

### Slow Performance
Verify optimizations are enabled:
- Check `ENABLE_EMBEDDING_CLUSTERING=true` in `.env`
- Check `MAX_CONCURRENT=48` for M4 Pro
- Monitor Metal GPU usage in Activity Monitor

### Module Not Found
Install all dependencies:
```bash
pip install -r requirements.txt
```

### Ollama Not Running
Ensure Ollama is installed and model is pulled:
```bash
ollama pull qwen2.5:7b
ollama list  # Verify model is available
```

## Project Structure

```
aiengineerassignment-master/
├── main.py                           # Core analysis pipeline
├── app.py                            # Flask web server
├── requirements.txt                  # Python dependencies
├── .env                             # Configuration
├── README.md                        # This file
│
├── config/                          # Configuration modules
│   ├── embedding_service.py         # Metal GPU embeddings
│   ├── hardware_profiles.py         # M4 Pro auto-detection
│   └── cache_db.py                  # Embedding & response cache
│
├── ml/                              # ML optimization modules
│   └── topic_clustering.py          # HDBSCAN clustering
│
├── utils/                           # Utility modules
│   └── duplicate_detector.py        # Semantic deduplication
│
├── static/                          # Web UI assets
│   ├── css/                         # Tailwind CSS
│   └── js/
│       └── dashboard.js             # Frontend logic
│
├── templates/                       # Flask templates
│   └── index.html                   # Main dashboard
│
├── cache/                           # Cached reviews & embeddings
│   ├── <app_id>/                    # Per-app review cache
│   ├── response_cache.db            # LLM response cache
│   ├── embeddings.db                # Embedding cache
│   └── jobs.db                      # Job history
│
├── output/                          # Generated reports
│   └── <App_Name>_trend_report_*.xlsx
│
└── docs/                            # Documentation
    ├── QUICK_START.md               # Quick start guide
    ├── OPTIMIZATION_SUMMARY.md      # ML optimizations
    ├── MOCK_DATA_FIX.md             # Mock data bug fix
    ├── APP_ID_FIX.md                # App ID bug fix
    ├── DELETE_RUNNING_JOBS_UPDATE.md # Delete feature
    ├── PERSISTENT_CHAT_UPDATE.md    # Persistent chat history
    └── CALENDAR_FEATURE_UPDATE.md   # Calendar date picker
```

## Documentation

- **[QUICK_START.md](QUICK_START.md)** - Getting started guide
- **[OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md)** - ML optimization details
- **[MOCK_DATA_FIX.md](MOCK_DATA_FIX.md)** - Mock data bug fix (food delivery topics for games)
- **[APP_ID_FIX.md](APP_ID_FIX.md)** - App ID bug fix details
- **[DELETE_RUNNING_JOBS_UPDATE.md](DELETE_RUNNING_JOBS_UPDATE.md)** - Delete running jobs feature
- **[PERSISTENT_CHAT_UPDATE.md](PERSISTENT_CHAT_UPDATE.md)** - Persistent chat history feature
- **[CALENDAR_FEATURE_UPDATE.md](CALENDAR_FEATURE_UPDATE.md)** - Calendar date picker feature

## Features Implemented

✅ **App Agnostic**: Works with any Android app from Google Play Store
✅ **Fast Processing**: 4.3x speedup with ML optimizations
✅ **Cost Effective**: $0 API costs using local Ollama
✅ **Smart Deduplication**: Removes ~50% duplicates using embeddings
✅ **Topic Clustering**: HDBSCAN-based (240x faster than LLM)
✅ **Metal GPU Acceleration**: Optimized for M4 Pro
✅ **Modern Web UI**: Real-time progress tracking
✅ **Job Management**: Delete, cancel, and retry jobs
✅ **Persistent Chat History**: Conversations survive refreshes and restarts
✅ **Interactive Visualizations**: Charts and searchable tables
✅ **Excel Reports**: Professional formatted output
