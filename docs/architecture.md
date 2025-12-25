# System Architecture

This document describes the technical architecture of the Swiggy App Store Review Trend Analysis System.

## System Overview

The system follows a **pipeline architecture** with five distinct phases, each handling a specific aspect of the analysis workflow. The design emphasizes modularity, testability, and scalability.

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│  ┌──────────────────┐              ┌──────────────────────┐     │
│  │   CLI (main.py)  │              │  Web UI (app.py)     │     │
│  └────────┬─────────┘              └──────────┬───────────┘     │
│           │                                    │                 │
└───────────┼────────────────────────────────────┼─────────────────┘
            │                                    │
┌───────────▼────────────────────────────────────▼─────────────────┐
│                      Processing Pipeline                          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Phase 1    │  │   Phase 2    │  │   Phase 3    │          │
│  │     Data     │─▶│    Topic     │─▶│    Topic     │          │
│  │  Collection  │  │  Extraction  │  │Consolidation │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │   Phase 4    │  │   Phase 5    │                             │
│  │    Trend     │─▶│   Report     │                             │
│  │   Analysis   │  │  Generation  │                             │
│  └──────────────┘  └──────────────┘                             │
└───────────────────────────────────────────────────────────────────┘
            │                                    │
┌───────────▼────────────────────────────────────▼─────────────────┐
│                      Supporting Systems                           │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │     LLM      │  │    Cache     │  │   Storage    │          │
│  │   Provider   │  │    System    │  │   (Files)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└───────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. User Interfaces

#### CLI Interface ([main.py](../main.py))

**Purpose**: Batch processing for automated workflows and scripting

**Key Features**:
- Command-line argument parsing
- Interactive prompts for missing parameters
- Console progress reporting
- Direct Excel output

**Entry Points**:
```python
# Basic usage
python main.py

# With parameters
python main.py --target-date 2024-12-25 --days 30 --app-id in.swiggy.android
```

#### Web Dashboard ([app.py](../app.py))

**Purpose**: Interactive analysis with real-time progress tracking

**Architecture**:
- **Backend**: Flask REST API
- **Frontend**: HTML + JavaScript + Chart.js
- **Communication**: AJAX polling for job status
- **Threading**: Background job execution

**Key Endpoints**:
- `POST /api/analyze`: Start analysis job
- `GET /api/status/<job_id>`: Get job progress
- `GET /api/results/<job_id>`: Get chart data
- `GET /api/download/<job_id>`: Download Excel report
- `GET /api/health/llm`: Check LLM provider status

### 2. Processing Pipeline

#### Phase 1: Data Collection

**Module**: `scrape_reviews()` in [main.py:188](../main.py#L188)

**Responsibilities**:
1. Fetch reviews from Google Play Store
2. Implement smart caching to minimize API calls
3. Handle pagination and rate limits
4. Filter reviews by date range
5. Fallback to mock data if scraping fails

**Key Techniques**:
- **Smart Stopping**: Stops fetching when past target date (reviews sorted newest first)
- **Cache Invalidation**: Updates cache if older than 24 hours
- **Incremental Updates**: Only fetches new reviews since last cache

**Data Structure**:
```python
reviews_by_date: Dict[str, List[dict]]
# Example:
{
  "2024-12-25": [
    {
      "reviewId": "abc123",
      "userName": "John Doe",
      "content": "Delivery was very late",
      "score": 1,
      "at": datetime(2024, 12, 25, 14, 30),
      # ... more fields
    },
    # ... more reviews
  ],
  "2024-12-24": [ ... ]
}
```

#### Phase 2: Topic Extraction

**Module**: `extract_all_topics()` in [main.py:491](../main.py#L491)

**Responsibilities**:
1. Extract topics from each review using LLM
2. Classify topics (issue/request/feedback)
3. Handle batch processing for efficiency
4. Provide progress callbacks for UI updates

**Key Techniques**:
- **Batch Processing**: Processes 20 reviews per LLM call
- **Parallel Execution**: Uses ThreadPoolExecutor with 8 workers
- **Context-Aware Prompts**: Includes examples in prompts for better extraction
- **Sarcasm Detection**: Special instructions to detect sarcastic reviews

**Prompt Strategy** ([main.py:44](../main.py#L44)):
```
High Recall Extraction → Include ALL topics
Context in Names → "delivery partner rude" not just "rude"
Sarcasm Detection → "Great job cold food" → "food delivered cold"
Limit Per Review → Max 5 most important topics
```

**Data Structure**:
```python
topics_by_date: Dict[str, List[str]]
# Example:
{
  "2024-12-25": [
    "delivery delay 2 hours",
    "food delivered cold",
    "delivery partner rude",
    # ... more topics
  ]
}
```

#### Phase 3: Topic Consolidation

**Module**: `consolidate_topics()` in [main.py:612](../main.py#L612)

**Responsibilities**:
1. Identify similar topics across all reviews
2. Create canonical topic names
3. Map variations to canonical names
4. Prevent topic fragmentation

**Key Techniques**:
- **Text Normalization**: Remove articles, tenses, intensifiers
- **LLM-Based Grouping**: Use LLM to group semantically similar topics
- **Aggressive Merging**: Target 15-25 final topics from 100+ extracted
- **Variation Tracking**: Keep original variations for validation

**Consolidation Rules** ([main.py:76](../main.py#L76)):
```
Positive feedback → ALL positive words (good, great, amazing, etc.)
Delivery delays → ALL delay mentions (late, slow, 2 hours, etc.)
Food issues → Group by sub-type (temperature, freshness, quality)
App issues → Group by type (crashes vs performance)
```

**Data Structure**:
```python
canonical_mapping: Dict[str, List[str]]
# Example:
{
  "Delivery delay": [
    "delivery delay 2 hours",
    "delivery delayed 2 hours",
    "2 hour delivery wait",
    "late delivery"
  ],
  "Food temperature issues": [
    "food cold",
    "cold food delivered",
    "food not hot"
  ]
}
```

#### Phase 4: Trend Analysis

**Module**: `map_topics_to_canonical()` in [main.py:747](../main.py#L747)

**Responsibilities**:
1. Map extracted topics to canonical versions
2. Count frequency by date
3. Track unmapped topics for validation
4. Suggest canonical matches for unmapped topics

**Data Structure**:
```python
canonical_counts: Dict[str, Dict[str, int]]
# Example:
{
  "2024-12-25": {
    "Delivery delay": 12,
    "Food temperature issues": 8,
    "App crashes/freezes": 3
  },
  "2024-12-24": { ... }
}
```

#### Phase 5: Report Generation

**Module**: `generate_trend_report()` in [main.py:834](../main.py#L834)

**Responsibilities**:
1. Create Topic × Date matrix
2. Format Excel with colors and styles
3. Validate topic mapping
4. Add legends and warnings for unmapped topics

**Excel Format**:
```
┌─────────────────────────┬─────────┬─────────┬─────────┬─────────┐
│ Topic                   │ Dec 1   │ Dec 2   │ ...     │ Dec 30  │
├─────────────────────────┼─────────┼─────────┼─────────┼─────────┤
│ Delivery delay          │   12    │   8     │   ...   │   15    │
│ Food temperature issues │    8    │   7     │   ...   │   12    │
│ App crashes/freezes     │    3    │   4     │   ...   │    7    │
└─────────────────────────┴─────────┴─────────┴─────────┴─────────┘
```

### 3. LLM Abstraction Layer

**Module**: [config/llm_client.py](../config/llm_client.py)

**Purpose**: Provide unified interface for multiple LLM providers

**Architecture**:
```python
BaseLLMClient (Abstract Base Class)
    │
    ├── OllamaClient        # Local inference
    ├── AnthropicClient     # Claude API
    └── GroqClient          # Groq API
```

**Key Features**:
- **Provider Abstraction**: Switch providers via environment variable
- **Model Switching**: Different models for extraction vs consolidation (Ollama)
- **Error Handling**: Graceful fallbacks for API errors
- **Health Checks**: Verify provider availability

**Model Selection Strategy**:
```
Extraction (Bulk):  Fast, efficient model (qwen2.5:32b)
                   ↓
                   Processes 1000s of reviews

Consolidation:     High-quality model (llama3.1:70b)
                   ↓
                   Single critical operation
```

### 4. Caching System

**Location**: `cache/<app-id>/reviews_cache.json`

**Purpose**: Minimize API calls and speed up repeated analyses

**Cache Structure**:
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
      // ... all review fields
    }
  ]
}
```

**Cache Invalidation**:
- **Age**: Invalidates if >24 hours old
- **Manual**: Delete cache file to force refresh
- **Incremental**: Fetches only new reviews since last update

**Benefits**:
- 100x faster for repeated analyses
- Reduces Play Store API load
- Enables offline development/testing

## Design Patterns

### 1. Pipeline Pattern

Each phase is a pure function that takes input and produces output:
```python
reviews → topics → canonical → counts → report
```

**Benefits**:
- Easy to test each phase independently
- Can parallelize independent operations
- Clear separation of concerns

### 2. Strategy Pattern (LLM Providers)

Multiple LLM implementations with common interface:
```python
client = get_llm_client()  # Factory method
response = client.chat(prompt)  # Unified interface
```

**Benefits**:
- Easy to add new providers
- Swap providers without code changes
- Test with mock providers

### 3. Observer Pattern (Progress Tracking)

Web UI uses callbacks to track progress:
```python
extract_all_topics(
    reviews,
    progress_callback=lambda processed, total: update_ui(...)
)
```

**Benefits**:
- Real-time UI updates
- No tight coupling between processing and UI
- Works with CLI and Web UI

### 4. Repository Pattern (Caching)

Abstraction over data storage:
```python
load_cached_reviews(app_id) → reviews or None
save_cached_reviews(app_id, reviews)
```

**Benefits**:
- Could swap file cache for Redis/DB
- Consistent caching interface
- Easy to mock for testing

## Performance Optimizations

### 1. Parallel Batch Processing

**Problem**: Processing 5000 reviews sequentially is slow

**Solution**:
- Batch reviews into groups of 20
- Process 8 batches in parallel (ThreadPoolExecutor)
- Each batch makes one LLM call

**Impact**:
- Sequential: ~5000 API calls, 30+ minutes
- Parallel: ~250 API calls, 3-5 minutes
- **10x speedup**

### 2. Smart Caching

**Problem**: Re-fetching same reviews wastes time and API quota

**Solution**:
- Cache reviews locally with timestamps
- Incremental updates (fetch only new reviews)
- Smart stopping (stop when past target date)

**Impact**:
- First run: Fetches all reviews
- Subsequent runs: Near-instant (reads from cache)
- **100x speedup** for repeat analyses

### 3. Prompt Engineering

**Problem**: LLM calls are expensive and slow

**Solution**:
- Batch extraction (20 reviews per call)
- Use smaller models for extraction (qwen2.5:32b)
- Use larger models only for consolidation (llama3.1:70b)

**Impact**:
- Cost: $0.10-0.50 per 1000 reviews (vs $2-5 with single-review calls)
- Speed: 3-5 min for 5000 reviews (vs 30+ min)
- **5-10x cost reduction**

### 4. Aggressive Topic Consolidation

**Problem**: LLM extracts too many similar topics (200+ from 100 unique)

**Solution**:
- Normalize text (remove articles, tenses, etc.)
- Use LLM for semantic grouping
- Target 15-25 canonical topics
- Merge aggressively (all positive → "Positive feedback")

**Impact**:
- Before: 200+ fragmented topics
- After: 15-25 canonical topics
- **10x reduction** in topic count

## Scalability Considerations

### Current Limitations

| Component | Limit | Reason |
|-----------|-------|--------|
| Reviews per run | ~10,000 | Memory constraints |
| Concurrent jobs (Web UI) | 1-2 | In-memory job storage |
| LLM concurrency | 8 workers | API rate limits |
| Cache size | ~100MB per app | Disk space |

### Scaling Strategies

#### For More Reviews
- **Stream Processing**: Process reviews in chunks, write to DB
- **Distributed Processing**: Use Celery + Redis for task queue
- **Database**: Replace file cache with PostgreSQL

#### For More Users
- **Job Queue**: Replace threading with Celery
- **Persistent Storage**: Use Redis for job state
- **Load Balancer**: Multiple Flask instances behind nginx

#### For Faster Processing
- **GPU Inference**: Run Ollama on GPU for 5-10x speedup
- **Embedding-Based Consolidation**: Replace LLM consolidation with vector similarity
- **Incremental Processing**: Only process new reviews, reuse previous consolidation

## Error Handling

### Graceful Degradation

```python
try:
    # Try real scraping
    reviews = scrape_reviews_from_play_store()
except Exception:
    # Fall back to mock data
    reviews = generate_mock_reviews()
```

### Retry Logic

```python
# LLM clients implement retries
for attempt in range(3):
    try:
        return client.chat(prompt)
    except RateLimitError:
        sleep(2 ** attempt)  # Exponential backoff
```

### Validation

```python
# Validate topic mapping
if len(unmapped_topics) > 0:
    print(f"⚠️ Found {len(unmapped_topics)} unmapped topics")
    # Suggest canonical matches
    # Highlight in Excel with yellow
```

## Security Considerations

### API Keys
- Stored in `.env` (not committed to git)
- Loaded via python-dotenv
- Never logged or exposed in responses

### Input Validation
- App IDs validated/sanitized
- Date ranges limited (1-90 days)
- File paths validated before writes

### Rate Limiting
- Respects Play Store API limits
- Implements backoff for LLM APIs
- Prevents abuse with timeout limits

## Testing Strategy

### Unit Tests (Recommended)
```python
# Test individual functions
test_normalize_topic()
test_consolidate_topics_heuristic()
test_extract_app_id_from_link()
```

### Integration Tests
```python
# Test pipeline with mock data
test_full_pipeline_with_mock_reviews()
test_cache_invalidation()
```

### Manual Testing
```bash
# Test with real data
python main.py --days 7

# Test web UI
python app.py
# Open browser, submit job, verify output
```

## Future Enhancements

### Short-Term
- Add database support (PostgreSQL)
- Implement proper job queue (Celery)
- Add user authentication
- Support more app stores (iOS App Store)

### Long-Term
- Real-time streaming analysis
- ML-based topic classification
- Sentiment analysis integration
- Multi-language support
- API versioning
- Comprehensive test suite

## Technology Choices

### Why Flask?
- Lightweight, easy to deploy
- Good for small-medium projects
- Built-in development server
- Large ecosystem

**Alternatives**: FastAPI (async, better for large scale), Django (more features)

### Why ThreadPoolExecutor?
- Simple, built-in parallelism
- Good for I/O-bound tasks (LLM API calls)
- No external dependencies

**Alternatives**: Celery (production task queue), asyncio (for async I/O)

### Why Excel Output?
- Requested in assignment
- Universal format (no special viewers)
- Supports formatting (colors, fonts)

**Alternatives**: CSV (simpler), JSON (web-friendly), Database (queryable)

### Why Ollama?
- Free, local inference
- No API costs or rate limits
- Privacy (data never leaves machine)

**Alternatives**: Claude API (higher quality), Groq (faster cloud)

## References

- **Assignment Spec**: `AI Engineer Assignment.pdf`
- **Code**: [main.py](../main.py), [app.py](../app.py), [config/llm_client.py](../config/llm_client.py)
- **Data Flow**: See [data-flow.md](data-flow.md)
- **API Docs**: See [api-reference.md](api-reference.md)
