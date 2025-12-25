# Web Dashboard UI - User Guide

## Overview

This web dashboard provides a modern, interactive interface for the Swiggy App Store Review Trend Analysis tool. Built with **Flask**, **Tailwind CSS**, and **Chart.js**, it offers real-time progress tracking and beautiful data visualizations.

## Features

### 🎨 Modern UI
- **Single-page dashboard** with clean, gradient design
- **Responsive layout** - works on desktop, tablet, and mobile
- **Real-time progress tracking** with phase-by-phase updates
- **Interactive charts** - line charts and bar charts for trend visualization
- **Searchable data table** - filter topics on the fly

### 📊 Visualizations
1. **Topic Trends Line Chart** - Top 10 topics tracked over time
2. **Top Topics Bar Chart** - Top 15 topics by total mentions (horizontal bars)
3. **Topics Data Table** - All topics with search/filter capability
4. **Summary Cards** - Quick stats (total reviews, topics, date range)

### 💾 Export
- **Download Excel Report** - One-click download of complete trend analysis

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask (web framework)
- Flask-CORS (cross-origin support)
- All existing dependencies (Anthropic, pandas, etc.)

### 2. Set Up Environment

Make sure your `.env` file has the Anthropic API key:

```bash
ANTHROPIC_API_KEY=your_api_key_here
```

## Running the Dashboard

### Start the Server

```bash
python app.py
```

You should see:
```
============================================================
Swiggy App Store Review Trend Analysis - Web Dashboard
============================================================

🚀 Starting Flask server...
📊 Dashboard: http://localhost:5000
📡 API Docs: http://localhost:5000/api/jobs
```

### Access the Dashboard

Open your browser and navigate to:
```
http://localhost:5000
```

## How to Use

### Step 1: Configure Analysis
1. **App Package ID** - Enter a Google Play Store app ID (e.g., `in.swiggy.android`) or paste a Play Store link
2. **Target Date** - Select the end date for analysis (defaults to today)
3. **Analysis Period** - Choose how many days to analyze (7, 14, 30, 60, or 90 days)

### Step 2: Start Analysis
Click the **"Start Analysis"** button. The dashboard will:
1. Show the **Progress Tracker** section
2. Update progress in real-time through 5 phases:
   - Phase 1: Data Collection
   - Phase 2: Topic Extraction
   - Phase 3: Topic Consolidation
   - Phase 4: Trend Analysis
   - Phase 5: Report Generation

### Step 3: View Results
Once complete, you'll see:
1. **Summary Cards** - Total reviews, topics identified, and date range
2. **Topic Trends Chart** - Line graph showing how top topics changed over time
3. **Top Topics Chart** - Horizontal bar chart of most frequent topics
4. **Topics Table** - Complete list of all topics with search functionality

### Step 4: Download Excel
Click the **"Download Excel"** button to get the complete report as an `.xlsx` file.

## Architecture

### Backend (Flask API)

**File:** `app.py`

**Endpoints:**
- `GET /` - Serve main dashboard HTML
- `POST /api/analyze` - Start analysis job
- `GET /api/status/<job_id>` - Get job progress
- `GET /api/results/<job_id>` - Get visualization data (JSON)
- `GET /api/download/<job_id>` - Download Excel file
- `GET /api/jobs` - List all jobs (debug endpoint)

**How It Works:**
- Wraps existing `main.py` functionality
- Runs analysis in background thread
- Stores job state in memory (use Redis for production)
- Provides real-time progress updates

### Frontend (HTML + JavaScript)

**Files:**
- `templates/index.html` - Main dashboard UI
- `static/js/dashboard.js` - Frontend logic
- `static/css/styles.css` - Custom styles (minimal)

**How It Works:**
- Form submission triggers API call to `/api/analyze`
- JavaScript polls `/api/status` every 2 seconds for progress
- When complete, fetches `/api/results` and renders charts
- Chart.js renders interactive visualizations
- Tailwind CSS provides responsive styling

## Technology Stack

| Component | Technology | Why? |
|-----------|-----------|------|
| Backend | Flask | Simple, lightweight, perfect for this use case |
| Frontend Framework | Vanilla JS | No overhead, simple state management |
| CSS | Tailwind CSS (CDN) | Rapid development, professional look |
| Charts | Chart.js | Beautiful, interactive charts with minimal code |
| WebGL? | ❌ No | Overkill for 2D time-series data |

## Why No WebGL?

WebGL was considered but rejected because:
- **Data type**: 2D time-series (topics × dates)
- **Dataset size**: ~25 topics × 30 days = 750 data points
- **Complexity**: WebGL adds 10x development time
- **Better alternative**: Chart.js provides smooth, professional visualizations with CSS transitions

**Verdict**: WebGL is only useful for:
- 3D visualizations
- Massive datasets (10,000+ points)
- Complex particle systems

For this project, Chart.js + CSS is the optimal choice.

## Project Structure

```
aiengineerassignment-master/
├── app.py                    # Flask backend API
├── main.py                   # Original CLI tool (unchanged)
├── requirements.txt          # Updated with Flask deps
├── templates/
│   └── index.html           # Dashboard UI
├── static/
│   ├── js/
│   │   └── dashboard.js     # Frontend logic
│   └── css/
│       └── styles.css       # Custom styles
├── output/                   # Generated Excel reports
├── cache/                    # Cached reviews
└── data/                     # Raw data
```

## API Reference

### POST /api/analyze

Start a new analysis job.

**Request:**
```json
{
  "app_id": "in.swiggy.android",
  "target_date": "2025-12-24",
  "days": 30
}
```

**Response:**
```json
{
  "job_id": "abc-123-def-456",
  "status": "started",
  "message": "Analysis job started successfully"
}
```

### GET /api/status/{job_id}

Get job progress.

**Response:**
```json
{
  "job_id": "abc-123",
  "status": "running",
  "phase": "Topic Extraction",
  "progress_pct": 50,
  "message": "Extracted 750/1500 topics",
  "updated_at": "2025-12-24T10:30:00"
}
```

**Status values:**
- `started` - Job created
- `running` - In progress
- `completed` - Finished successfully
- `failed` - Error occurred

### GET /api/results/{job_id}

Get visualization data.

**Response:**
```json
{
  "line_chart": { /* Chart.js data */ },
  "bar_chart": { /* Chart.js data */ },
  "topics_table": [ /* Array of topics */ ],
  "summary": {
    "total_reviews": 1500,
    "total_topics": 25,
    "date_range": "Nov 24, 2025 - Dec 24, 2025"
  }
}
```

### GET /api/download/{job_id}

Download Excel file.

**Response:** Binary file download (`.xlsx`)

## Troubleshooting

### Server won't start
```bash
# Check if port 5000 is in use
lsof -i :5000

# Kill process if needed
kill -9 <PID>

# Try different port
python -c "from app import app; app.run(port=8000)"
```

### "Module not found" errors
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or manually
pip install flask flask-cors
```

### Analysis stuck at 0%
- Check server console for errors
- Verify Anthropic API key is set
- Check network connectivity
- Look at browser console (F12) for JavaScript errors

### Charts not rendering
- Open browser console (F12)
- Check for JavaScript errors
- Verify Chart.js CDN loaded correctly
- Try refreshing the page

### Excel download fails
- Check if `output/` folder exists
- Verify file was generated (check server logs)
- Check browser download permissions

## Production Deployment

For production use, consider:

### 1. Use Production Server
Replace Flask dev server with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 2. Add Redis for Job State
Replace in-memory `jobs` dict with Redis:
```python
import redis
r = redis.Redis(host='localhost', port=6379)
```

### 3. Add Authentication
Protect API endpoints with authentication.

### 4. Use Environment Variables
Never hardcode API keys - use `.env` file.

### 5. Add Rate Limiting
Prevent API abuse with Flask-Limiter.

### 6. Enable HTTPS
Use nginx/Apache as reverse proxy with SSL.

## Command Line vs Web UI

Both interfaces are available:

### CLI (Original)
```bash
python main.py --target-date 2025-12-24 --days 30
```

### Web UI (New)
```bash
python app.py
# Then open http://localhost:5000
```

The CLI and Web UI use the same analysis engine - choose based on your preference!

## License

Educational project - Pulsegen Technologies AI Engineer Assignment

## Support

For issues or questions, check:
1. Server console logs
2. Browser console (F12)
3. `output/` folder for generated files
4. Original README.md for analysis details
