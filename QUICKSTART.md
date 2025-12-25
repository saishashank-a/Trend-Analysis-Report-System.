# 🚀 Quick Start Guide - Web Dashboard

## Step 1: Install Dependencies (if not done already)

```bash
pip install -r requirements.txt
```

This installs:
- Flask & Flask-CORS (web framework)
- All existing dependencies (Anthropic, pandas, openpyxl, etc.)

## Step 2: Start the Server

```bash
python app.py
```

You'll see:
```
============================================================
Swiggy App Store Review Trend Analysis - Web Dashboard
============================================================

🚀 Starting Flask server...
📊 Dashboard: http://localhost:5000
📡 API Docs: http://localhost:5000/api/jobs

 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.x.x:5000
```

## Step 3: Open the Dashboard

Open your browser and go to:
```
http://localhost:5000
```

## Step 4: Run Your First Analysis

1. **Enter App Info** (or use the default Swiggy app)
   - App Package ID: `in.swiggy.android`

2. **Set Date Range**
   - Target Date: Today (default)
   - Days: 30 (default)

3. **Click "Start Analysis"**

4. **Watch Progress** in real-time through 5 phases

5. **View Results** with interactive charts

6. **Download Excel** report

## 🎨 What You'll See

### Configuration Panel
- Clean form to input app ID, date, and analysis period
- Default values pre-filled for quick testing

### Progress Tracker
- Real-time progress bar (0-100%)
- Phase-by-phase checklist with checkmarks
- Current status messages

### Results Dashboard
- **Summary Cards**: Total reviews, topics, date range
- **Line Chart**: Top 10 topics over time
- **Bar Chart**: Top 15 topics by frequency
- **Data Table**: All topics with search functionality
- **Download Button**: Get Excel report

## 🛠️ Troubleshooting

### Port Already in Use?
```bash
# Use a different port
python -c "from app import app; app.run(port=8000)"
# Then open http://localhost:8000
```

### Missing Flask?
```bash
pip install flask flask-cors
```

### API Key Issues?
Make sure `.env` file exists with:
```
ANTHROPIC_API_KEY=your_key_here
```

## 📚 Full Documentation

See [UI_README.md](UI_README.md) for complete documentation including:
- API reference
- Architecture details
- Production deployment
- Advanced configuration

## 🎯 Technology Used

- **Backend**: Flask (Python web framework)
- **Frontend**: HTML + Tailwind CSS + Vanilla JavaScript
- **Charts**: Chart.js
- **No WebGL**: Intentionally skipped (overkill for 2D data)

## ✅ Why No WebGL?

You asked about WebGL - here's why we skipped it:

**WebGL is great for:**
- 3D visualizations
- Particle systems
- Complex animations
- 10,000+ data points

**Our use case:**
- 2D time-series data (topics × dates)
- ~750 data points (25 topics × 30 days)
- Simple line/bar charts

**Verdict**: Chart.js + CSS transitions provide smooth, professional visuals without the complexity of WebGL. It's the right tool for the job!

## 🎨 UI Features

✅ Modern gradient design
✅ Responsive (mobile-friendly)
✅ Real-time progress updates
✅ Interactive charts (hover, zoom)
✅ Searchable data table
✅ One-click Excel download
✅ Error handling with friendly messages
✅ Loading states & animations

Enjoy your beautiful new dashboard! 🎉
