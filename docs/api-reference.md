# API Reference

This document provides comprehensive documentation for all code modules, functions, and REST API endpoints in the system.

## Table of Contents

1. [Python API (main.py)](#python-api-mainpy)
2. [LLM Client API (config/llm_client.py)](#llm-client-api-configllm_clientpy)
3. [REST API Endpoints (app.py)](#rest-api-endpoints-apppy)
4. [Data Structures](#data-structures)

---

## Python API (main.py)

### Core Functions

#### `scrape_reviews(app_id, start_date, end_date)`

Scrape reviews from Google Play Store with intelligent caching.

**Parameters**:
- `app_id` (str): App package ID (e.g., `"in.swiggy.android"`)
- `start_date` (datetime): Start of analysis period
- `end_date` (datetime): End of analysis period

**Returns**:
- `Dict[str, List[dict]]`: Reviews organized by date string

**Example**:
```python
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=29)

reviews = scrape_reviews("in.swiggy.android", start_date, end_date)
# Returns: {"2024-12-25": [review1, review2, ...], ...}
```

**Behavior**:
- Checks cache first (returns cached if <24 hours old)
- Uses smart stopping (stops when past start_date)
- Falls back to mock data if scraping fails
- Saves fetched reviews to cache

**Location**: [main.py:188](../main.py#L188)

---

#### `extract_all_topics(reviews_by_date, progress_callback=None)`

Extract topics from all reviews using parallel batch processing.

**Parameters**:
- `reviews_by_date` (Dict[str, List[dict]]): Reviews organized by date
- `progress_callback` (Optional[Callable]): Callback function `(processed: int, total: int) -> None`

**Returns**:
- `Dict[str, List[str]]`: Topics organized by date

**Example**:
```python
def on_progress(processed, total):
    print(f"Progress: {processed}/{total}")

topics = extract_all_topics(reviews_by_date, progress_callback=on_progress)
# Returns: {"2024-12-25": ["delivery delay", "food cold", ...], ...}
```

**Configuration**:
- Batch size: 20 reviews per API call
- Parallel workers: 8
- Progress updates every 50 reviews

**Location**: [main.py:491](../main.py#L491)

---

#### `consolidate_topics(all_topics)`

Consolidate similar topics using LLM-based semantic grouping.

**Parameters**:
- `all_topics` (List[str]): All extracted topics from all reviews

**Returns**:
- `Dict[str, List[str]]`: Canonical topic → variations mapping

**Example**:
```python
all_topics = ["delivery delay", "late delivery", "food cold", "cold food"]

canonical = consolidate_topics(all_topics)
# Returns: {
#   "Delivery delay": ["delivery delay", "late delivery"],
#   "Food temperature issues": ["food cold", "cold food"]
# }
```

**Behavior**:
- Normalizes text (removes articles, tenses, etc.)
- Uses LLM for semantic grouping
- Targets 15-25 canonical topics
- Falls back to heuristic consolidation on error

**Location**: [main.py:612](../main.py#L612)

---

#### `map_topics_to_canonical(topics_by_date, canonical_mapping)`

Map extracted topics to canonical versions and count frequencies.

**Parameters**:
- `topics_by_date` (Dict[str, List[str]]): Topics by date
- `canonical_mapping` (Dict[str, List[str]]): Canonical → variations mapping

**Returns**:
- `Tuple[Dict[str, Dict[str, int]], Dict[str, str]]`:
  - Canonical counts by date
  - Unmapped topics → suggested canonical mapping

**Example**:
```python
topics_by_date = {"2024-12-25": ["delivery delay", "late delivery"]}
canonical_mapping = {"Delivery delay": ["delivery delay", "late delivery"]}

counts, unmapped = map_topics_to_canonical(topics_by_date, canonical_mapping)
# counts: {"2024-12-25": {"Delivery delay": 2}}
# unmapped: {} (all mapped)
```

**Location**: [main.py:747](../main.py#L747)

---

#### `generate_trend_report(canonical_counts, target_date, output_file, canonical_mapping, unmapped_topics)`

Generate Excel trend report with formatting.

**Parameters**:
- `canonical_counts` (Dict[str, Dict[str, int]]): Counts by date
- `target_date` (datetime): End date of analysis
- `output_file` (str): Path to output Excel file
- `canonical_mapping` (Dict[str, List[str]]): Canonical mapping
- `unmapped_topics` (Dict[str, str]): Unmapped topics

**Returns**:
- None (writes Excel file)

**Example**:
```python
generate_trend_report(
    canonical_counts,
    datetime(2024, 12, 25),
    "output/report.xlsx",
    canonical_mapping,
    unmapped_topics
)
# Creates Excel file at specified path
```

**Excel Features**:
- Blue header with topic and dates
- Alternating row colors
- Yellow highlight for unmapped topics
- Auto-sized columns
- Validation warnings

**Location**: [main.py:834](../main.py#L834)

---

### Helper Functions

#### `extract_app_id_from_link(link)`

Extract app package ID from Play Store URL.

**Parameters**:
- `link` (str): Package ID or Play Store URL

**Returns**:
- `str`: Package ID

**Example**:
```python
# From URL
app_id = extract_app_id_from_link(
    "https://play.google.com/store/apps/details?id=in.swiggy.android"
)
# Returns: "in.swiggy.android"

# From package ID
app_id = extract_app_id_from_link("in.swiggy.android")
# Returns: "in.swiggy.android"
```

**Location**: [main.py:816](../main.py#L816)

---

#### `normalize_topic(topic)`

Normalize topic text for better matching.

**Parameters**:
- `topic` (str): Original topic text

**Returns**:
- `str`: Normalized topic text

**Example**:
```python
normalized = normalize_topic("The delivery guy was very rude")
# Returns: "delivery partner rude"
```

**Normalization Steps**:
1. Lowercase
2. Remove extra whitespace
3. Remove "to be" verbs (is, are, was, were)
4. Remove articles (a, an, the)
5. Remove intensifiers (very, extremely, really)
6. Normalize common terms (delivery guy → delivery partner)

**Location**: [main.py:580](../main.py#L580)

---

#### `extract_topics_batch(reviews_batch)`

Extract topics from a batch of reviews in a single LLM call.

**Parameters**:
- `reviews_batch` (List[dict]): List of review dictionaries

**Returns**:
- `Dict[int, List[dict]]`: Index → topics mapping

**Example**:
```python
batch = [
    {"content": "Delivery was late"},
    {"content": "Food was cold"}
]

topics = extract_topics_batch(batch)
# Returns: {
#   0: [{"topic": "delivery delay", "category": "issue"}],
#   1: [{"topic": "food cold", "category": "issue"}]
# }
```

**Location**: [main.py:386](../main.py#L386)

---

### Cache Functions

#### `load_cached_reviews(app_id)`

Load cached reviews for an app.

**Parameters**:
- `app_id` (str): App package ID

**Returns**:
- `Tuple[list, datetime]`: Reviews list and last update time

**Example**:
```python
reviews, last_update = load_cached_reviews("in.swiggy.android")
if reviews:
    print(f"Loaded {len(reviews)} reviews from {last_update}")
```

**Location**: [main.py:121](../main.py#L121)

---

#### `save_cached_reviews(app_id, reviews)`

Save reviews to cache.

**Parameters**:
- `app_id` (str): App package ID
- `reviews` (list): List of review dictionaries

**Returns**:
- None

**Example**:
```python
save_cached_reviews("in.swiggy.android", reviews)
# Saves to cache/in.swiggy.android/reviews_cache.json
```

**Location**: [main.py:156](../main.py#L156)

---

### Mock Data Functions

#### `generate_mock_reviews(start_date, end_date)`

Generate mock reviews for testing.

**Parameters**:
- `start_date` (datetime): Start date
- `end_date` (datetime): End date

**Returns**:
- `Dict[str, List[dict]]`: Mock reviews by date

**Example**:
```python
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=6)

mock_reviews = generate_mock_reviews(start_date, end_date)
# Returns 7 days of mock review data
```

**Location**: [main.py:314](../main.py#L314)

---

## LLM Client API (config/llm_client.py)

### Base Class

#### `BaseLLMClient`

Abstract base class for LLM clients.

**Methods**:

##### `chat(prompt, max_tokens=500, temperature=0.1)`

Send chat request to LLM.

**Parameters**:
- `prompt` (str): User prompt
- `max_tokens` (int): Maximum response tokens
- `temperature` (float): Sampling temperature (0.0-1.0)

**Returns**:
- `str`: LLM response text

**Example**:
```python
client = get_llm_client()
response = client.chat("Extract topics from: 'Food was cold'", max_tokens=100)
```

---

##### `extract_json(response_text)`

Extract JSON from LLM response, handling markdown wrappers.

**Parameters**:
- `response_text` (str): LLM response with JSON

**Returns**:
- `dict`: Parsed JSON object

**Example**:
```python
response = "```json\n{\"topics\": [\"food cold\"]}\n```"
data = client.extract_json(response)
# Returns: {"topics": ["food cold"]}
```

---

### Ollama Client

#### `OllamaClient(base_url, extraction_model, consolidation_model)`

Local LLM client using Ollama.

**Parameters**:
- `base_url` (str): Ollama server URL (default: `http://localhost:11434`)
- `extraction_model` (str): Model for extraction (default: `qwen2.5:32b`)
- `consolidation_model` (str): Model for consolidation (default: `llama3.1:70b`)

**Methods**:

##### `set_extraction_mode()`
Switch to extraction model (fast, bulk processing).

##### `set_consolidation_mode()`
Switch to consolidation model (high quality).

##### `check_health()`
Check Ollama server health and model availability.

**Returns**:
- `Dict[str, Any]`: Health status

**Example**:
```python
client = OllamaClient()
health = client.check_health()
# Returns: {
#   "status": "ok",
#   "models": ["qwen2.5:32b", "llama3.1:70b"],
#   ...
# }
```

**Location**: [config/llm_client.py:58](../config/llm_client.py#L58)

---

### Anthropic Client

#### `AnthropicClient(api_key=None)`

Anthropic Claude API client.

**Parameters**:
- `api_key` (Optional[str]): API key (defaults to `ANTHROPIC_API_KEY` env var)

**Example**:
```python
client = AnthropicClient(api_key="sk-ant-...")
response = client.chat("Hello", max_tokens=50)
```

**Location**: [config/llm_client.py:154](../config/llm_client.py#L154)

---

### Groq Client

#### `GroqClient(api_key=None)`

Groq cloud inference client.

**Parameters**:
- `api_key` (Optional[str]): API key (defaults to `GROQ_API_KEY` env var)

**Example**:
```python
client = GroqClient(api_key="gsk_...")
response = client.chat("Hello", max_tokens=50)
```

**Location**: [config/llm_client.py:179](../config/llm_client.py#L179)

---

### Factory Functions

#### `get_llm_client()`

Get LLM client based on environment configuration.

**Returns**:
- `BaseLLMClient`: Configured LLM client

**Example**:
```python
# Uses LLM_PROVIDER env var
client = get_llm_client()
```

**Supported Providers**:
- `ollama` (default)
- `anthropic`
- `groq`

**Location**: [config/llm_client.py:205](../config/llm_client.py#L205)

---

#### `check_llm_status()`

Check configured LLM provider status.

**Returns**:
- `Dict[str, Any]`: Status information

**Example**:
```python
status = check_llm_status()
# Returns: {"status": "ok", "provider": "ollama", ...}
```

**Location**: [config/llm_client.py:236](../config/llm_client.py#L236)

---

## REST API Endpoints (app.py)

### Base URL

```
http://localhost:8000
```

### Endpoints

#### `GET /`

Serve the main dashboard HTML page.

**Response**:
- HTML page

**Example**:
```bash
curl http://localhost:8000
```

---

#### `POST /api/analyze`

Start a new analysis job.

**Request Body**:
```json
{
  "app_id": "in.swiggy.android",
  "target_date": "2024-12-25",
  "days": 30
}
```

**Parameters**:
- `app_id` (string, optional): App package ID or Play Store URL (default: Swiggy)
- `target_date` (string, optional): End date in YYYY-MM-DD format (default: today)
- `days` (integer, optional): Number of days to analyze, 1-90 (default: 30)

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started",
  "message": "Analysis job started successfully"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"app_id": "in.swiggy.android", "days": 7}'
```

**Location**: [app.py:272](../app.py#L272)

---

#### `GET /api/status/<job_id>`

Get current status of an analysis job.

**Response**:
```json
{
  "job_id": "550e8400-...",
  "status": "running",
  "phase": "Topic Extraction",
  "progress_pct": 45,
  "message": "Extracting topics from 2250/5000 reviews...",
  "metrics": {
    "processed": 2250,
    "total": 5000
  },
  "updated_at": "2024-12-25T14:30:00"
}
```

**Status Values**:
- `started`: Job initiated
- `running`: Processing in progress
- `completed`: Job finished successfully
- `failed`: Job encountered an error

**Example**:
```bash
curl http://localhost:8000/api/status/550e8400-e29b-41d4-a716-446655440000
```

**Location**: [app.py:337](../app.py#L337)

---

#### `GET /api/results/<job_id>`

Get analysis results for charts (only for completed jobs).

**Response**:
```json
{
  "line_chart": {
    "labels": ["Dec 1", "Dec 2", ...],
    "datasets": [
      {
        "label": "Delivery delay",
        "data": [12, 15, 18, ...],
        "borderColor": "rgb(59, 130, 246)"
      }
    ]
  },
  "bar_chart": {
    "labels": ["Delivery delay", "Food issues", ...],
    "datasets": [
      {
        "label": "Total Mentions",
        "data": [450, 320, ...]
      }
    ]
  },
  "topics_table": [
    {
      "topic": "Delivery delay",
      "total_count": 450,
      "variation_count": 12
    }
  ],
  "summary": {
    "total_reviews": 5000,
    "total_topics": 18,
    "date_range": "Nov 26, 2024 - Dec 25, 2024"
  }
}
```

**Example**:
```bash
curl http://localhost:8000/api/results/550e8400-e29b-41d4-a716-446655440000
```

**Location**: [app.py:352](../app.py#L352)

---

#### `GET /api/download/<job_id>`

Download Excel report for a completed job.

**Response**:
- Excel file (`.xlsx`)
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

**Example**:
```bash
curl http://localhost:8000/api/download/550e8400-... -o report.xlsx
```

**Location**: [app.py:370](../app.py#L370)

---

#### `GET /api/jobs`

List all jobs (debugging/admin).

**Response**:
```json
{
  "jobs": [
    {
      "job_id": "550e8400-...",
      "status": "completed",
      "created_at": "2024-12-25T14:00:00",
      ...
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8000/api/jobs
```

**Location**: [app.py:398](../app.py#L398)

---

#### `GET /api/health/llm`

Check LLM provider health.

**Response**:
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

**Status Values**:
- `ok`: Ready to use
- `warning`: Issues but may work (e.g., missing models)
- `error`: Cannot use (e.g., server down)

**Example**:
```bash
curl http://localhost:8000/api/health/llm
```

**Location**: [app.py:413](../app.py#L413)

---

## Data Structures

### Review Object

```python
{
  "reviewId": str,           # Unique review ID
  "userName": str,           # Reviewer name
  "userImage": str,          # Profile image URL
  "content": str,            # Review text
  "score": int,              # Rating (1-5)
  "thumbsUpCount": int,      # Helpful votes
  "reviewCreatedVersion": str | None,  # App version
  "at": datetime,            # Review date/time
  "replyContent": str | None,          # Developer reply
  "repliedAt": datetime | None         # Reply date/time
}
```

### Topic Object

```python
{
  "topic": str,        # Topic description (e.g., "delivery delay")
  "category": str      # "issue", "request", or "feedback"
}
```

### Job State Object

```python
{
  "job_id": str,              # UUID
  "status": str,              # "started", "running", "completed", "failed"
  "phase": str,               # Current phase name
  "progress_pct": int,        # 0-100
  "message": str,             # Status message
  "metrics": {                # Optional progress metrics
    "processed": int,
    "total": int
  },
  "app_id": str,              # App being analyzed
  "target_date": str,         # ISO date
  "days": int,                # Analysis window
  "created_at": str,          # ISO datetime
  "updated_at": str,          # ISO datetime
  "completed_at": str | None, # ISO datetime (if completed)
  "failed_at": str | None,    # ISO datetime (if failed)
  "result_file": str | None,  # Path to Excel file (if completed)
  "results_data": dict | None,# Chart data (if completed)
  "error": str | None         # Error message (if failed)
}
```

### Cache File Structure

```json
{
  "app_id": "in.swiggy.android",
  "last_update": "2024-12-25T14:30:00",
  "total_reviews": 5000,
  "reviews": [
    {
      "reviewId": "abc123",
      "content": "...",
      "at": "2024-12-25T14:30:00",
      ...
    }
  ]
}
```

---

## Error Handling

### Python Exceptions

```python
try:
    reviews = scrape_reviews(app_id, start, end)
except Exception as e:
    # Falls back to mock data
    reviews = generate_mock_reviews(start, end)
```

### HTTP Error Responses

```json
{
  "error": "Job not found"
}
```

**Status Codes**:
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (job doesn't exist)
- `500`: Internal Server Error
- `503`: Service Unavailable (LLM provider down)

---

## Code Examples

### Complete Analysis Pipeline

```python
from datetime import datetime, timedelta
from main import (
    scrape_reviews,
    extract_all_topics,
    consolidate_topics,
    map_topics_to_canonical,
    generate_trend_report
)

# Setup
end_date = datetime.now()
start_date = end_date - timedelta(days=29)
app_id = "in.swiggy.android"

# Phase 1: Scrape
reviews = scrape_reviews(app_id, start_date, end_date)

# Phase 2: Extract
topics = extract_all_topics(reviews)

# Phase 3: Consolidate
all_topics = [t for topics_list in topics.values() for t in topics_list]
canonical = consolidate_topics(all_topics)

# Phase 4: Map
counts, unmapped = map_topics_to_canonical(topics, canonical)

# Phase 5: Generate
generate_trend_report(
    counts, end_date, "output/report.xlsx", canonical, unmapped
)
```

### Custom LLM Integration

```python
from config.llm_client import BaseLLMClient

class CustomLLMClient(BaseLLMClient):
    def chat(self, prompt, max_tokens=500, temperature=0.1):
        # Your custom LLM API call here
        return response_text

# Use it
import os
os.environ['LLM_PROVIDER'] = 'custom'

# Modify get_llm_client() to support 'custom'
```

### API Client

```python
import requests

class AnalysisClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def start_analysis(self, app_id, days=30):
        response = requests.post(
            f"{self.base_url}/api/analyze",
            json={"app_id": app_id, "days": days}
        )
        return response.json()["job_id"]

    def wait_for_completion(self, job_id):
        while True:
            status = self.get_status(job_id)
            if status["status"] == "completed":
                return True
            elif status["status"] == "failed":
                raise Exception(status.get("error"))
            time.sleep(5)

    def get_status(self, job_id):
        response = requests.get(f"{self.base_url}/api/status/{job_id}")
        return response.json()

    def download_report(self, job_id, output_path):
        response = requests.get(f"{self.base_url}/api/download/{job_id}")
        with open(output_path, 'wb') as f:
            f.write(response.content)

# Usage
client = AnalysisClient()
job_id = client.start_analysis("in.swiggy.android", days=7)
client.wait_for_completion(job_id)
client.download_report(job_id, "report.xlsx")
```

---

## See Also

- [Architecture](architecture.md) - System design
- [Data Flow](data-flow.md) - Pipeline details
- [User Guide](user-guide.md) - Usage instructions
- [Troubleshooting](troubleshooting.md) - Common issues
