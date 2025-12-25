# Getting Started

This guide will help you set up and run the Swiggy App Store Review Trend Analysis System.

## Prerequisites

### Required Software

1. **Python 3.8+**
   ```bash
   # Check your Python version
   python --version  # or python3 --version
   ```

2. **pip** (Python package manager)
   ```bash
   # Usually comes with Python, verify:
   pip --version
   ```

3. **Git** (optional, for cloning)
   ```bash
   git --version
   ```

### LLM Provider (Choose One)

#### Option 1: Ollama (Recommended - Free, Local)

**Pros**: Free, private, no API limits
**Cons**: Requires powerful hardware (16GB+ RAM for 70B models)

1. Install Ollama from [https://ollama.com/download](https://ollama.com/download)
2. Pull required models:
   ```bash
   ollama pull qwen2.5:32b      # Extraction model
   ollama pull llama3.1:70b     # Consolidation model
   ```
3. Verify Ollama is running:
   ```bash
   ollama list  # Should show installed models
   ```

#### Option 2: Anthropic Claude (Cloud, Paid)

**Pros**: No local hardware requirements, high quality
**Cons**: Costs money, requires API key

1. Sign up at [https://console.anthropic.com](https://console.anthropic.com)
2. Get your API key from the dashboard
3. Note: Estimated cost ~$2-5 for 30 days of Swiggy reviews

#### Option 3: Groq (Cloud, Free Tier)

**Pros**: Fast inference, free tier available
**Cons**: Rate limits on free tier

1. Sign up at [https://console.groq.com](https://console.groq.com)
2. Get your API key
3. Free tier includes 14,400 requests/day

## Installation

### Step 1: Get the Project

```bash
# If you have the ZIP file:
unzip aiengineerassignment.zip
cd aiengineerassignment

# Or clone from repository:
git clone <repository-url>
cd aiengineerassignment
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# If using Anthropic Claude, also install:
pip install anthropic

# If using Groq, also install:
pip install groq
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the template (if exists)
cp .env.example .env

# Or create new .env file
touch .env
```

Edit `.env` with your configuration:

```bash
# ============================================
# LLM Provider Configuration
# ============================================

# Choose one: ollama, anthropic, groq
LLM_PROVIDER=ollama

# ============================================
# Ollama Configuration (if using Ollama)
# ============================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EXTRACTION_MODEL=qwen2.5:32b
OLLAMA_CONSOLIDATION_MODEL=llama3.1:70b

# ============================================
# Anthropic Configuration (if using Claude)
# ============================================
# ANTHROPIC_API_KEY=your_api_key_here

# ============================================
# Groq Configuration (if using Groq)
# ============================================
# GROQ_API_KEY=your_api_key_here
# GROQ_MODEL=llama-3.1-70b-versatile
```

## Verify Installation

### Test LLM Connection

```bash
# For Ollama users:
python -c "from config.llm_client import get_llm_client; client = get_llm_client(); print(client.chat('Say hello', max_tokens=10))"

# For cloud providers (Claude/Groq):
# Make sure your API key is in .env first
python -c "from config.llm_client import get_llm_client; client = get_llm_client(); print('Connected successfully')"
```

### Test Basic Functionality

```bash
# Run a quick test with mock data
python main.py --days 7
```

This should:
1. Generate mock reviews (since no real reviews for recent dates)
2. Extract topics
3. Consolidate topics
4. Create an Excel report in `output/` folder

## First Run

### CLI (Command Line Interface)

Run your first analysis:

```bash
# Basic run (30 days, Swiggy app, ending today)
python main.py

# Custom date range
python main.py --target-date 2024-12-25 --days 14

# Different app (e.g., Zomato)
python main.py --app-id com.application.zomato
```

Expected output:
```
==============================================================
App Store Review Trend Analysis
==============================================================
Analysis Period: 2024-11-26 to 2024-12-25

PHASE 1: Data Collection
----------------------------------------
Scraping reviews from 2024-11-26 to 2024-12-25...
  ✓ Loaded 5000 cached reviews

PHASE 2: Topic Extraction
----------------------------------------
Extracting topics...
  Processed 1000/5000 reviews | Elapsed: 30s | ETA: 120s

PHASE 3: Topic Consolidation
----------------------------------------
Consolidating 342 unique topics...
  ✓ Consolidated to 18 canonical topics

PHASE 4: Trend Analysis
----------------------------------------
Analyzing trends...

PHASE 5: Report Generation
----------------------------------------
✓ Report saved to output/swiggy_trend_report_2024-12-25.xlsx

==============================================================
✓ Analysis Complete!
==============================================================
```

### Web Dashboard

Start the web interface:

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

Open your browser to `http://localhost:8000` and:
1. Enter app ID or Play Store URL
2. Select date range
3. Click "Start Analysis"
4. Watch real-time progress
5. View results and download Excel report

## Directory Structure After Installation

```
aiengineerassignment/
├── .env                       # Your configuration (create this)
├── .venv/                     # Virtual environment (if created)
├── main.py                    # CLI entry point
├── app.py                     # Web UI entry point
├── requirements.txt           # Python dependencies
├── config/
│   ├── __init__.py
│   └── llm_client.py         # LLM abstraction layer
├── cache/                     # Review cache (auto-created)
│   └── in.swiggy.android/
│       └── reviews_cache.json
├── output/                    # Generated reports (auto-created)
│   └── swiggy_trend_report_2024-12-25.xlsx
├── data/                      # Additional data (auto-created)
├── static/                    # Web UI assets
├── templates/                 # Web UI templates
│   └── index.html
└── docs/                      # Documentation
    ├── index.md
    ├── getting-started.md    # You are here!
    └── ...
```

## Common Installation Issues

### "Module not found" errors

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Ollama connection errors

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start Ollama app
# macOS: Open Ollama from Applications
# Linux: systemctl start ollama
# Windows: Open Ollama from Start Menu

# Verify models are installed
ollama list
```

### API key errors (Cloud providers)

```bash
# Verify .env file exists
ls -la .env

# Check API key is set
cat .env | grep API_KEY

# Test API key
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('ANTHROPIC_API_KEY', 'Not set'))"
```

### Permission errors

```bash
# Make sure you have write permissions
chmod +w output/
chmod +w cache/

# Or run with appropriate permissions
```

## Next Steps

Now that you're set up:

1. **Read the [User Guide](user-guide.md)** to learn how to use the system
2. **Review [Architecture](architecture.md)** to understand how it works
3. **Check [API Reference](api-reference.md)** if you want to extend the code
4. **See [Troubleshooting](troubleshooting.md)** if you encounter issues

## Quick Reference

### Common Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run CLI analysis
python main.py

# Run with custom parameters
python main.py --target-date 2024-12-15 --days 30 --app-id in.swiggy.android

# Start web dashboard
python app.py

# Deactivate virtual environment
deactivate
```

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LLM_PROVIDER` | LLM provider (ollama/anthropic/groq) | `ollama` | No |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` | No |
| `OLLAMA_EXTRACTION_MODEL` | Model for topic extraction | `qwen2.5:32b` | No |
| `OLLAMA_CONSOLIDATION_MODEL` | Model for consolidation | `llama3.1:70b` | No |
| `ANTHROPIC_API_KEY` | Anthropic API key | - | Yes (if using Claude) |
| `GROQ_API_KEY` | Groq API key | - | Yes (if using Groq) |
| `GROQ_MODEL` | Groq model name | `llama-3.1-70b-versatile` | No |

### File Locations

- **Configuration**: `.env`
- **Cache**: `cache/<app-id>/reviews_cache.json`
- **Output**: `output/<app>_trend_report_<date>.xlsx`
- **Logs**: Console output (stderr/stdout)

## Support

If you encounter issues:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Verify your Python version: `python --version`
3. Ensure all dependencies are installed: `pip list`
4. Check LLM provider status (Ollama running / API keys valid)
5. Look for error messages in console output
