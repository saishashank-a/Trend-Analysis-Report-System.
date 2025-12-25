# Troubleshooting Guide

This guide helps you diagnose and fix common issues with the Swiggy App Store Review Trend Analysis System.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [LLM Provider Issues](#llm-provider-issues)
3. [Data Collection Issues](#data-collection-issues)
4. [Processing Issues](#processing-issues)
5. [Output Issues](#output-issues)
6. [Web Dashboard Issues](#web-dashboard-issues)
7. [Performance Issues](#performance-issues)

---

## Installation Issues

### "Module not found" errors

**Symptom**:
```bash
ModuleNotFoundError: No module named 'pandas'
```

**Cause**: Dependencies not installed

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep pandas
```

---

### "Python version not supported"

**Symptom**:
```bash
ERROR: This package requires Python >=3.8
```

**Cause**: Python version too old

**Solution**:
```bash
# Check Python version
python --version

# If <3.8, upgrade Python or use newer version
python3 --version
python3.9 --version

# Create venv with specific version
python3.9 -m venv venv
```

---

### Virtual environment activation fails

**Symptom** (Windows):
```bash
venv\Scripts\activate : cannot be loaded because running scripts is disabled
```

**Cause**: PowerShell execution policy

**Solution**:
```powershell
# Open PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate
venv\Scripts\activate
```

---

## LLM Provider Issues

### Ollama: "Could not connect"

**Symptom**:
```
Exception: Could not connect to Ollama. Make sure Ollama is running
```

**Diagnosis**:
```bash
# Test Ollama connection
curl http://localhost:11434/api/tags
```

**Solutions**:

1. **Ollama not running**:
   ```bash
   # macOS: Open Ollama app from Applications
   # Linux: Start service
   systemctl start ollama

   # Windows: Open Ollama from Start Menu
   ```

2. **Wrong URL**:
   ```bash
   # Check .env file
   OLLAMA_BASE_URL=http://localhost:11434

   # If running on different port/host, update:
   OLLAMA_BASE_URL=http://192.168.1.100:11434
   ```

3. **Firewall blocking**:
   ```bash
   # Allow Ollama through firewall (port 11434)
   # macOS: System Preferences → Security → Firewall
   # Windows: Windows Defender Firewall → Allow an app
   ```

---

### Ollama: "Missing models"

**Symptom**:
```json
{
  "status": "warning",
  "message": "Missing models: qwen2.5:32b, llama3.1:70b"
}
```

**Diagnosis**:
```bash
# List installed models
ollama list
```

**Solution**:
```bash
# Pull required models
ollama pull qwen2.5:32b
ollama pull llama3.1:70b

# Verify installation
ollama list
```

**Alternative**: Use different models
```bash
# Edit .env
OLLAMA_EXTRACTION_MODEL=llama3.1:8b  # Smaller, faster
OLLAMA_CONSOLIDATION_MODEL=llama3.1:70b
```

---

### Anthropic: "API Key not found"

**Symptom**:
```
ValueError: ANTHROPIC_API_KEY not found in environment
```

**Diagnosis**:
```bash
# Check .env file exists
ls -la .env

# Check API key is set
cat .env | grep ANTHROPIC_API_KEY
```

**Solutions**:

1. **Create .env file**:
   ```bash
   touch .env
   echo "LLM_PROVIDER=anthropic" >> .env
   echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
   ```

2. **Verify API key**:
   ```bash
   # Test in Python
   python -c "
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print(os.getenv('ANTHROPIC_API_KEY', 'Not set'))
   "
   ```

3. **Install Anthropic SDK**:
   ```bash
   pip install anthropic
   ```

---

### Anthropic: "Rate limit exceeded"

**Symptom**:
```
RateLimitError: Rate limit exceeded for requests
```

**Cause**: Too many API requests in short time

**Solutions**:

1. **Reduce parallel workers**:
   ```python
   # In main.py, line 507
   MAX_WORKERS = 4  # Reduce from 8 to 4
   ```

2. **Increase batch size**:
   ```python
   # In main.py, line 506
   BATCH_SIZE = 30  # Increase from 20 to 30
   ```

3. **Upgrade API tier**:
   - Visit Anthropic console
   - Upgrade to higher tier for more requests/minute

---

### Groq: "API Key invalid"

**Symptom**:
```
AuthenticationError: Invalid API key
```

**Diagnosis**:
```bash
# Test API key manually
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"
```

**Solution**:
```bash
# Get new API key from console.groq.com
# Update .env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
```

---

## Data Collection Issues

### "No reviews found"

**Symptom**:
```
No reviews found for 2024-12-15 to 2024-12-25
Using mock data for demonstration...
```

**Causes & Solutions**:

1. **Date range too recent**:
   ```bash
   # Play Store may not have reviews for very recent dates
   # Try older date range
   python main.py --target-date 2024-12-01
   ```

2. **App ID incorrect**:
   ```bash
   # Verify app ID
   python -c "
   from google_play_scraper import app
   result = app('in.swiggy.android')
   print(result['title'])
   "
   # Should print: Swiggy
   ```

3. **Network issues**:
   ```bash
   # Test internet connection
   ping play.google.com

   # Test Play Store API
   python -c "
   from google_play_scraper import reviews, Sort
   result, _ = reviews('in.swiggy.android', count=5)
   print(f'Fetched {len(result)} reviews')
   "
   ```

---

### "Cache loading error"

**Symptom**:
```
Warning: Could not load cache: Expecting value: line 1 column 1 (char 0)
```

**Cause**: Corrupted cache file

**Solution**:
```bash
# Delete corrupted cache
rm cache/in.swiggy.android/reviews_cache.json

# Re-run to fetch fresh data
python main.py
```

---

### Play Store scraping slow

**Symptom**: Taking >10 minutes to fetch reviews

**Causes & Solutions**:

1. **No cache**:
   ```bash
   # First run is always slow (fetching from Play Store)
   # Subsequent runs use cache and are fast

   # Force use of cache if exists
   # (Don't delete cache unless necessary)
   ```

2. **Large date range**:
   ```bash
   # Reduce date range
   python main.py --days 7  # Instead of 30
   ```

3. **Network slow**:
   ```bash
   # Check download speed
   speedtest-cli

   # Use mock data for testing
   # (Delete cache to trigger mock data generation)
   rm -rf cache/in.swiggy.android/
   python main.py
   ```

---

## Processing Issues

### "Topic extraction failed"

**Symptom**:
```
Exception: Could not parse JSON from response
```

**Cause**: LLM returned malformed JSON

**Solutions**:

1. **Check LLM health**:
   ```bash
   # For Ollama
   curl http://localhost:11434/api/tags

   # For cloud providers
   python -c "from config.llm_client import check_llm_status; print(check_llm_status())"
   ```

2. **Reduce batch size** (less complex prompts):
   ```python
   # In main.py, line 506
   BATCH_SIZE = 10  # Reduce from 20
   ```

3. **Use heuristic fallback**:
   The system automatically falls back to rule-based extraction if LLM fails.
   Check console output for "Warning" messages.

---

### "Consolidation too aggressive"

**Symptom**: Only 5-10 topics in final report (expected 15-25)

**Cause**: Consolidation prompt too aggressive

**Solution**:

1. **Adjust prompt** in [main.py:73](../main.py#L73):
   ```python
   # Change target from 15-25 to 20-30
   CONSOLIDATION_PROMPT = """...
   TARGET: 20-30 CANONICAL TOPICS MAXIMUM.
   ...
   ```

2. **Use different model**:
   ```bash
   # Use larger model for better nuance
   OLLAMA_CONSOLIDATION_MODEL=llama3.1:70b  # Instead of smaller model
   ```

---

### "Too many topics" (fragmentation)

**Symptom**: 100+ topics in final report

**Cause**: Consolidation not working

**Solutions**:

1. **Check consolidation phase**:
   ```bash
   # Look for this in console output:
   # "✓ Consolidated to 18 canonical topics"

   # If not present, consolidation failed
   ```

2. **Verify LLM response**:
   ```python
   # Add debug logging in main.py, line 650
   print(f"Consolidation response: {response_text[:500]}")
   ```

3. **Use heuristic consolidation**:
   If LLM consolidation fails, the system uses rule-based consolidation.
   Check if you see: "Warning: Consolidation error"

---

### "Processing stuck"

**Symptom**: Process hangs at "Processing batch X"

**Causes & Solutions**:

1. **LLM timeout**:
   ```python
   # In config/llm_client.py, line 94
   timeout=300  # Increase from 300 to 600 seconds
   ```

2. **Deadlock in parallel processing**:
   ```bash
   # Reduce workers
   # In main.py, line 507
   MAX_WORKERS = 2  # Reduce from 8
   ```

3. **Kill and restart**:
   ```bash
   # Press Ctrl+C to kill
   # Check for zombie processes
   ps aux | grep python

   # Kill if needed
   kill -9 <PID>

   # Restart
   python main.py
   ```

---

## Output Issues

### "Excel file not generated"

**Symptom**: No .xlsx file in output/ folder

**Diagnosis**:
```bash
# Check if output directory exists
ls -la output/

# Check for error messages in console
```

**Solutions**:

1. **Create output directory**:
   ```bash
   mkdir -p output
   ```

2. **Check permissions**:
   ```bash
   # Ensure write permissions
   chmod +w output/
   ```

3. **Verify openpyxl installed**:
   ```bash
   pip install openpyxl --upgrade
   ```

4. **Check disk space**:
   ```bash
   df -h  # macOS/Linux
   # Ensure sufficient space (>100 MB)
   ```

---

### "Excel file corrupted"

**Symptom**: Excel says "file is corrupted" when opening

**Cause**: Process interrupted during write

**Solution**:
```bash
# Delete corrupted file
rm output/swiggy_trend_report_*.xlsx

# Re-run analysis
python main.py
```

---

### "Unmapped topics in Excel"

**Symptom**: Yellow-highlighted topics in Excel

**Cause**: Topics not in canonical mapping

**Solutions**:

1. **Review unmapped topics**:
   ```bash
   # Check console output:
   # "⚠️ Found 5 unmapped topics:"
   #   - 'xyz' (suggested: 'ABC')
   ```

2. **Improve consolidation**:
   - Use better LLM model for consolidation
   - Adjust consolidation prompt
   - Add custom rules in `consolidate_topics_heuristic()`

3. **Manual mapping** (for production):
   ```python
   # Add to consolidation_rules in main.py, line 683
   "Custom topic name": ["variation1", "variation2", ...]
   ```

---

### "Empty Excel cells"

**Symptom**: Many 0 values in Excel

**Cause**: Not an issue - topics not mentioned on those days

**Explanation**:
```
If a topic wasn't mentioned on a particular day, the count is 0.
This is expected behavior for trend analysis.

Example:
  "App crashes": 5, 0, 0, 12, 0, ...

  Interpretation: App crashed on 2 days only during the period
```

---

## Web Dashboard Issues

### "Dashboard not loading"

**Symptom**: Browser shows "Can't connect" at localhost:8000

**Diagnosis**:
```bash
# Check if Flask is running
curl http://localhost:8000
```

**Solutions**:

1. **Start Flask server**:
   ```bash
   python app.py
   ```

2. **Check port availability**:
   ```bash
   # See if port 8000 is in use
   lsof -i :8000  # macOS/Linux
   netstat -ano | findstr :8000  # Windows

   # Use different port if occupied
   PORT=8080 python app.py
   ```

3. **Check firewall**:
   ```bash
   # Ensure firewall allows port 8000
   # macOS: System Preferences → Security → Firewall
   # Windows: Windows Defender Firewall
   ```

---

### "Job stuck at 0%"

**Symptom**: Progress bar doesn't move

**Causes & Solutions**:

1. **Background thread died**:
   ```bash
   # Check Flask console for errors
   # Look for Python exceptions
   ```

2. **LLM provider down**:
   ```bash
   # Check LLM health
   curl http://localhost:8000/api/health/llm
   ```

3. **Restart job**:
   ```bash
   # Refresh page
   # Start new analysis
   ```

---

### "Can't download report"

**Symptom**: Download button doesn't work

**Diagnosis**:
```bash
# Check API response
curl http://localhost:8000/api/download/<job_id>
```

**Solutions**:

1. **Job not completed**:
   ```bash
   # Wait for job to reach 100%
   # Status should be "completed"
   ```

2. **File deleted**:
   ```bash
   # Check if file exists
   ls -la output/

   # Re-run analysis if needed
   ```

3. **Browser cache**:
   ```bash
   # Clear browser cache
   # Try different browser
   ```

---

### "Charts not displaying"

**Symptom**: Empty chart areas in web dashboard

**Causes & Solutions**:

1. **JavaScript error**:
   ```bash
   # Open browser console (F12)
   # Look for errors
   ```

2. **No data**:
   ```bash
   # Check if job completed successfully
   # Verify results_data exists in job
   curl http://localhost:8000/api/results/<job_id>
   ```

3. **Chart.js not loaded**:
   ```bash
   # Check network tab in browser (F12)
   # Ensure Chart.js loads from CDN
   ```

---

## Performance Issues

### "Analysis too slow"

**Symptom**: Taking >30 minutes for 30-day analysis

**Solutions**:

1. **Enable caching**:
   ```bash
   # Don't delete cache unless necessary
   # Cache makes subsequent runs 100x faster
   ```

2. **Use GPU for Ollama**:
   ```bash
   # If you have NVIDIA GPU
   # Ollama automatically uses GPU if available
   # 5-10x speedup
   ```

3. **Reduce data size**:
   ```bash
   # Analyze fewer days
   python main.py --days 7

   # Or use mock data for testing
   rm -rf cache/
   python main.py
   ```

4. **Increase parallel workers** (if you have good hardware):
   ```python
   # In main.py, line 507
   MAX_WORKERS = 16  # Increase from 8
   ```

5. **Use faster models**:
   ```bash
   # Edit .env
   OLLAMA_EXTRACTION_MODEL=llama3.1:8b  # Smaller, faster
   ```

---

### "High memory usage"

**Symptom**: System slowing down, swap usage high

**Causes & Solutions**:

1. **Large cache**:
   ```bash
   # Check cache size
   du -sh cache/

   # Delete old caches if needed
   rm -rf cache/old-app-id/
   ```

2. **Too many parallel workers**:
   ```python
   # Reduce workers
   MAX_WORKERS = 4  # In main.py, line 507
   ```

3. **Large LLM models**:
   ```bash
   # Use smaller models
   OLLAMA_EXTRACTION_MODEL=qwen2.5:14b  # Instead of 32b
   OLLAMA_CONSOLIDATION_MODEL=llama3.1:8b  # Instead of 70b
   ```

---

### "Ollama using too much RAM"

**Symptom**: Ollama using >20GB RAM

**Cause**: Large models loaded in memory

**Solutions**:

1. **Unload unused models**:
   ```bash
   # Stop Ollama
   # Restart Ollama (models unload)
   ```

2. **Use smaller models**:
   ```bash
   ollama pull qwen2.5:14b  # 14B instead of 32B
   ```

3. **Limit Ollama memory**:
   ```bash
   # Set environment variable before starting Ollama
   OLLAMA_NUM_GPU_LAYERS=20  # Reduce GPU layers
   ```

---

## General Debugging Tips

### Enable verbose logging

Add debug prints to code:

```python
# In main.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Or add print statements
print(f"Debug: reviews_by_date = {reviews_by_date.keys()}")
```

---

### Check system health

```bash
# Python version
python --version

# Package versions
pip list

# Disk space
df -h

# Memory
free -h  # Linux
vm_stat  # macOS

# Network
ping google.com
```

---

### Test individual components

```python
# Test LLM client
from config.llm_client import get_llm_client
client = get_llm_client()
print(client.chat("Say hello", max_tokens=10))

# Test scraping
from google_play_scraper import reviews
result, _ = reviews('in.swiggy.android', count=5)
print(f"Fetched {len(result)} reviews")

# Test Excel writing
from openpyxl import Workbook
wb = Workbook()
wb.save("test.xlsx")
print("Excel test passed")
```

---

### Clean slate

When all else fails, start fresh:

```bash
# Delete virtual environment
rm -rf venv/

# Delete cache
rm -rf cache/

# Delete output
rm -rf output/*.xlsx

# Recreate environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run again
python main.py
```

---

## Getting Help

If issues persist:

1. **Check documentation**:
   - [Getting Started](getting-started.md)
   - [User Guide](user-guide.md)
   - [Architecture](architecture.md)

2. **Review logs**:
   - Console output
   - Flask logs (if using web dashboard)
   - System logs

3. **Test with mock data**:
   ```bash
   # Delete cache to trigger mock data
   rm -rf cache/in.swiggy.android/
   python main.py --days 7
   ```

4. **Isolate the issue**:
   - Does it work with mock data?
   - Does it work with different app ID?
   - Does it work with fewer days?

5. **Document the issue**:
   - Error messages (full traceback)
   - Steps to reproduce
   - Environment (OS, Python version, etc.)
   - What you've tried

---

## Common Error Messages

### "Connection refused"
- **Cause**: Service not running (Ollama, Flask)
- **Fix**: Start the service

### "Permission denied"
- **Cause**: No write permissions
- **Fix**: `chmod +w directory/`

### "Command not found"
- **Cause**: Package not installed or not in PATH
- **Fix**: Install package or activate venv

### "Killed"
- **Cause**: Out of memory
- **Fix**: Reduce workers, use smaller models

### "Timeout"
- **Cause**: Operation taking too long
- **Fix**: Increase timeout or reduce data size

---

## Quick Fixes Checklist

Before asking for help, try these:

- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] .env file configured
- [ ] LLM provider running (check `/api/health/llm`)
- [ ] Sufficient disk space (>500 MB)
- [ ] Sufficient RAM (>4 GB available)
- [ ] Internet connection working
- [ ] Tried with mock data
- [ ] Deleted and recreated cache
- [ ] Restarted Python/Ollama/Flask

---

## See Also

- [Getting Started](getting-started.md) - Initial setup
- [User Guide](user-guide.md) - Usage instructions
- [Architecture](architecture.md) - System design
- [API Reference](api-reference.md) - Code documentation
