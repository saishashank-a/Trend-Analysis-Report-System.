# Data Flow

This document provides a detailed explanation of how data flows through the system from scraping reviews to generating Excel reports.

## Table of Contents

1. [Overview](#overview)
2. [Phase 1: Data Collection](#phase-1-data-collection)
3. [Phase 2: Topic Extraction](#phase-2-topic-extraction)
4. [Phase 3: Topic Consolidation](#phase-3-topic-consolidation)
5. [Phase 4: Trend Analysis](#phase-4-trend-analysis)
6. [Phase 5: Report Generation](#phase-5-report-generation)
7. [Optimization Strategies](#optimization-strategies)

---

## Overview

The system processes data through five sequential phases:

```
Reviews → Topics → Canonical Topics → Counts → Excel Report
  (5k)    (20k)         (18)          (18×30)     (.xlsx)
```

**Key Metrics** (for 30-day analysis of Swiggy):
- **Input**: ~5,000 reviews from Play Store
- **Extracted**: ~20,000 raw topics
- **Consolidated**: ~18 canonical topics
- **Output**: 18×30 Excel matrix + charts

**Processing Time**:
- With cache: ~3-5 minutes
- Without cache: ~10-15 minutes

---

## Phase 1: Data Collection

### Input
- App package ID (e.g., `in.swiggy.android`)
- Date range (start_date → end_date)

### Process

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Collection Flow                     │
└─────────────────────────────────────────────────────────────┘

1. Check Cache
   ├─ Cache exists & fresh (<24h old)?
   │  ├─ Yes → Load from cache/in.swiggy.android/reviews_cache.json
   │  └─ No  → Continue to step 2
   │
2. Fetch from Play Store
   ├─ Use google-play-scraper library
   ├─ Sort by NEWEST
   ├─ Fetch in batches of 500
   │  ├─ Batch 1: Reviews 1-500
   │  ├─ Batch 2: Reviews 501-1000
   │  └─ ... continue until past start_date (SMART STOPPING)
   │
3. Save to Cache
   ├─ Convert datetime to ISO strings
   ├─ Save as JSON to cache/
   └─ Log cache stats
   │
4. Filter by Date Range
   ├─ Keep only reviews where: start_date ≤ review.at ≤ end_date
   └─ Organize by date string (YYYY-MM-DD)
```

### Output

```python
{
  "2024-12-25": [
    {
      "reviewId": "abc123",
      "userName": "John Doe",
      "content": "Delivery was 2 hours late, food was cold",
      "score": 1,
      "at": datetime(2024, 12, 25, 14, 30),
      ...
    },
    {
      "reviewId": "def456",
      "content": "Great service, delivery partner was very friendly",
      "score": 5,
      "at": datetime(2024, 12, 25, 15, 45),
      ...
    }
    # ... more reviews for this date
  ],
  "2024-12-24": [ ... ],
  ...
}
```

### Data Transformations

```
Play Store API Response
  ↓
[Datetime Parsing]
  ↓
Cached JSON (datetime → ISO string)
  ↓
[Load from Cache]
  ↓
Python dict (ISO string → datetime)
  ↓
[Filter by Date]
  ↓
Reviews organized by date
```

### Cache Structure

```json
{
  "app_id": "in.swiggy.android",
  "last_update": "2024-12-25T14:30:00",
  "total_reviews": 5243,
  "reviews": [
    {
      "reviewId": "abc123",
      "userName": "John Doe",
      "userImage": "https://...",
      "content": "Delivery was 2 hours late...",
      "score": 1,
      "thumbsUpCount": 5,
      "reviewCreatedVersion": "4.32.0",
      "at": "2024-12-25T14:30:00",
      "replyContent": null,
      "repliedAt": null
    }
  ]
}
```

### Smart Stopping Example

```
Timeline (sorted NEWEST first):
  Dec 25 ──► Dec 24 ──► Dec 23 ──► ... ──► Nov 26 ──► Nov 25 (STOP!)
                                             ↑
                                        start_date

Instead of fetching ALL reviews:
  ✓ Fetch Dec 25 → Nov 26 (30 days needed)
  ✗ Skip Nov 25 → Ancient (not needed)

Savings: 80-90% fewer API calls
```

---

## Phase 2: Topic Extraction

### Input
```python
{
  "2024-12-25": [review1, review2, ...],
  "2024-12-24": [...],
  ...
}
```

### Process

```
┌─────────────────────────────────────────────────────────────┐
│                   Topic Extraction Flow                     │
└─────────────────────────────────────────────────────────────┘

For each date:
  1. Batch Reviews
     ├─ Group into batches of 20 reviews
     ├─ Example: 150 reviews → 8 batches
     │
  2. Parallel Processing (8 workers)
     ├─ Worker 1: Batch 0 (reviews 0-19)
     ├─ Worker 2: Batch 1 (reviews 20-39)
     ├─ Worker 3: Batch 2 (reviews 40-59)
     ├─ ...
     └─ Worker 8: Batch 7 (reviews 140-159)
     │
  3. For each batch:
     ├─ Build prompt with 20 reviews
     ├─ Call LLM API (single call for 20 reviews)
     ├─ Parse JSON response
     └─ Extract topics for each review
     │
  4. Collect Results
     ├─ Merge topics from all batches
     └─ Flatten to list of topic strings
```

### LLM Prompt Example

**Input to LLM**:
```
Extract ALL topics from these app reviews. Prioritize HIGH RECALL.

Include context in topic names (e.g., "delivery partner rude" not just "rude").
Detect sarcasm: "Great job delivering cold food" → "food delivered cold"
Return max 5 most important topics per review.

Reviews:
0. Delivery was 2 hours late, food was cold
1. Great service today, delivery partner was very friendly
2. App keeps crashing when I try to checkout

Output JSON object ONLY (no markdown, just raw JSON):
{"reviews": [
  {"review_id": "0", "topics": [{"topic": "...", "category": "issue|request|feedback"}]},
  {"review_id": "1", "topics": [...]},
  ...
]}
```

**LLM Response**:
```json
{
  "reviews": [
    {
      "review_id": "0",
      "topics": [
        {"topic": "delivery delay 2 hours", "category": "issue"},
        {"topic": "food delivered cold", "category": "issue"}
      ]
    },
    {
      "review_id": "1",
      "topics": [
        {"topic": "positive feedback", "category": "feedback"},
        {"topic": "delivery partner friendly", "category": "feedback"}
      ]
    },
    {
      "review_id": "2",
      "topics": [
        {"topic": "app crashes at checkout", "category": "issue"}
      ]
    }
  ]
}
```

### Output

```python
{
  "2024-12-25": [
    "delivery delay 2 hours",
    "food delivered cold",
    "positive feedback",
    "delivery partner friendly",
    "app crashes at checkout",
    # ... more topics from other reviews
  ],
  "2024-12-24": [...],
  ...
}
```

### Parallelization Strategy

```
Sequential Processing:
  Review 1 → LLM → Wait → Review 2 → LLM → Wait → ...
  Time: 5000 reviews × 2 sec = 10,000 seconds (2.7 hours)

Batch Processing:
  Batch 1 (20 reviews) → LLM → Wait → Batch 2 (20 reviews) → ...
  Time: 250 batches × 3 sec = 750 seconds (12.5 min)

Parallel Batch Processing:
  ┌─ Batch 1 → LLM ─┐
  ├─ Batch 2 → LLM ─┤
  ├─ Batch 3 → LLM ─┤ ← 8 workers
  ├─ ...           ─┤   running in
  └─ Batch 8 → LLM ─┘   parallel
  Time: 250 batches ÷ 8 workers × 3 sec = 94 seconds (1.5 min)

Speed: 64x faster than sequential!
```

### Topic Categorization

**Issue**: Problems users report
```
"delivery delay", "food cold", "app crashes"
```

**Request**: Features users want
```
"10 minute delivery", "24/7 service", "express delivery"
```

**Feedback**: General comments
```
"positive feedback", "good service", "pricing concerns"
```

---

## Phase 3: Topic Consolidation

### Input
```python
[
  "delivery delay 2 hours",
  "delivery delayed",
  "late delivery",
  "food delivered cold",
  "cold food",
  "food not hot",
  "app crashes at checkout",
  "app freezing",
  ...
]
# ~20,000 topics from ~5,000 reviews
```

### Process

```
┌─────────────────────────────────────────────────────────────┐
│                  Topic Consolidation Flow                   │
└─────────────────────────────────────────────────────────────┘

1. Remove Duplicates
   ├─ ["delivery delay", "delivery delay", "food cold"]
   └─ → ["delivery delay", "food cold"]
   │
2. Normalize Text
   ├─ "The delivery guy was very rude" → "delivery partner rude"
   ├─ Remove: articles (a, the), intensifiers (very), tense markers
   └─ Standardize: "delivery guy" → "delivery partner"
   │
3. Group Exact Matches
   ├─ After normalization, group identical topics
   └─ 20,000 → 342 unique normalized topics
   │
4. LLM-Based Semantic Grouping
   ├─ Send 342 unique topics to LLM (Consolidation model)
   ├─ LLM identifies semantic similarity
   ├─ Target: 15-25 canonical topics
   └─ Returns mapping: canonical → [variations]
   │
5. Build Canonical Mapping
   ├─ For each canonical topic
   ├─ Expand to include all normalized variations
   └─ Create reverse mapping: variation → canonical
```

### LLM Consolidation Prompt

**Input to LLM**:
```
You are consolidating topics from app reviews. BE EXTREMELY AGGRESSIVE -
aim for 15-25 final topics MAXIMUM.

Here are 342 extracted topics:
- delivery delay 2 hours
- delivery delayed 2 hours
- 2 hour delivery wait
- delivery extremely delayed
- late delivery
- food cold
- cold food delivered
- food not hot
- ...

CRITICAL RULES - MERGE EVERYTHING SIMILAR:
1. ALL positive feedback → "Positive feedback"
2. ALL negative delivery partner behavior → "Delivery partner unprofessional"
3. ALL delivery delays → "Delivery delay"
4. ALL food temperature issues → "Food temperature issues"
5. ALL app crashes/freezes → "App crashes/freezes"
...

OUTPUT (JSON only, no markdown):
{
  "canonical_topics": [
    {
      "canonical_name": "Delivery delay",
      "variations": ["delivery delay 2 hours", "late delivery", ...]
    },
    ...
  ]
}
```

**LLM Response**:
```json
{
  "canonical_topics": [
    {
      "canonical_name": "Delivery delay",
      "variations": [
        "delivery delay 2 hours",
        "delivery delayed 2 hours",
        "2 hour delivery wait",
        "late delivery",
        "delivery extremely delayed"
      ]
    },
    {
      "canonical_name": "Food temperature issues",
      "variations": [
        "food cold",
        "cold food delivered",
        "food not hot",
        "lukewarm food"
      ]
    },
    {
      "canonical_name": "App crashes/freezes",
      "variations": [
        "app crashes at checkout",
        "app freezing",
        "app stuck",
        "app not responding"
      ]
    }
  ]
}
```

### Output

```python
{
  "Delivery delay": [
    "delivery delay 2 hours",
    "delivery delayed 2 hours",
    "2 hour delivery wait",
    "late delivery",
    "delivery extremely delayed"
  ],
  "Food temperature issues": [
    "food cold",
    "cold food delivered",
    "food not hot",
    "lukewarm food"
  ],
  "App crashes/freezes": [
    "app crashes at checkout",
    "app freezing",
    "app stuck",
    "app not responding"
  ],
  # ... 15 more canonical topics
}
```

### Consolidation Funnel

```
20,000 raw topics (from extraction)
    ↓
 [Remove duplicates]
    ↓
 342 unique topics
    ↓
 [Normalize text]
    ↓
 187 normalized groups
    ↓
 [LLM semantic grouping]
    ↓
  18 canonical topics

Reduction: 1111x (20,000 → 18)
```

### Normalization Examples

```
Before:                         After:
"The delivery guy was rude"  →  "delivery partner rude"
"Delivery guy very rude"     →  "delivery partner rude"
"Rude delivery partner"      →  "delivery partner rude"
"Impolite delivery person"   →  "delivery partner rude"  (fuzzy match)

All map to: "Delivery partner unprofessional"
```

---

## Phase 4: Trend Analysis

### Input

**Extracted Topics by Date**:
```python
{
  "2024-12-25": ["delivery delay 2 hours", "food cold", ...],
  "2024-12-24": ["late delivery", "cold food", ...],
  ...
}
```

**Canonical Mapping**:
```python
{
  "Delivery delay": ["delivery delay 2 hours", "late delivery", ...],
  "Food temperature issues": ["food cold", "cold food", ...],
  ...
}
```

### Process

```
┌─────────────────────────────────────────────────────────────┐
│                     Trend Analysis Flow                     │
└─────────────────────────────────────────────────────────────┘

1. Build Reverse Mapping
   ├─ variation → canonical lookup table
   ├─ "delivery delay 2 hours" → "Delivery delay"
   ├─ "late delivery" → "Delivery delay"
   └─ "food cold" → "Food temperature issues"
   │
2. Map & Count
   ├─ For each date:
   │  ├─ For each extracted topic:
   │  │  ├─ Look up canonical version
   │  │  └─ Increment count for (date, canonical)
   │
3. Handle Unmapped Topics
   ├─ Topics not in canonical mapping
   ├─ Try fuzzy matching (contains/substring)
   ├─ Track for validation report
   └─ Suggest best canonical match
   │
4. Build Count Matrix
   └─ canonical_counts[date][topic] = count
```

### Mapping Example

```
Date: 2024-12-25
Extracted topics:
  1. "delivery delay 2 hours"  →  Delivery delay
  2. "food cold"                →  Food temperature issues
  3. "late delivery"            →  Delivery delay
  4. "app crashes at checkout"  →  App crashes/freezes
  5. "delivery delay"           →  Delivery delay

Counts for 2024-12-25:
  - Delivery delay: 3
  - Food temperature issues: 1
  - App crashes/freezes: 1
```

### Output

```python
{
  "2024-12-25": {
    "Delivery delay": 12,
    "Food temperature issues": 8,
    "Positive feedback": 25,
    "App crashes/freezes": 3,
    "Delivery partner unprofessional": 6,
    ...
  },
  "2024-12-24": {
    "Delivery delay": 15,
    "Food temperature issues": 7,
    ...
  },
  ...
}
```

### Unmapped Topics Handling

```
Unmapped: "delivery guy extremely rude"

Fuzzy matching:
  Check if contains "delivery" + "rude"
  → Best match: "Delivery partner unprofessional"

Suggest in report:
  "delivery guy extremely rude" → "Delivery partner unprofessional"
```

---

## Phase 5: Report Generation

### Input

```python
canonical_counts = {
  "2024-12-25": {"Delivery delay": 12, "Food issues": 8, ...},
  "2024-12-24": {"Delivery delay": 15, ...},
  ...
}
```

### Process

```
┌─────────────────────────────────────────────────────────────┐
│                   Report Generation Flow                    │
└─────────────────────────────────────────────────────────────┘

1. Calculate Date Range
   ├─ start_date = target_date - 29 days
   ├─ Generate list: [Dec 1, Dec 2, ..., Dec 30]
   │
2. Collect All Topics
   ├─ Union of all topics across all dates
   ├─ Sort: canonical first, unmapped last
   │
3. Build Matrix
   ├─ Rows: Topics
   ├─ Columns: Dates
   ├─ Cells: Counts (0 if topic not mentioned that day)
   │
4. Create Excel Workbook
   ├─ Add headers (blue background)
   ├─ Add data rows (alternating colors)
   ├─ Highlight unmapped topics (yellow)
   ├─ Auto-size columns
   └─ Add legend
   │
5. Validation Report
   ├─ Check: expected topics vs actual
   ├─ List unmapped topics with suggestions
   └─ Print to console
   │
6. Save File
   └─ output/<app>_trend_report_<date>.xlsx
```

### Excel Layout

```
┌─────────────────────────┬──────┬──────┬──────┬─────┬──────┐
│ Topic                   │Dec 1 │Dec 2 │Dec 3 │ ... │Dec 30│  ← Header (Blue)
├─────────────────────────┼──────┼──────┼──────┼─────┼──────┤
│ Delivery delay          │  12  │  15  │  18  │ ... │  20  │  ← Row 1 (Light blue)
├─────────────────────────┼──────┼──────┼──────┼─────┼──────┤
│ Food temperature issues │   8  │   7  │   6  │ ... │  11  │  ← Row 2 (White)
├─────────────────────────┼──────┼──────┼──────┼─────┼──────┤
│ Positive feedback       │  25  │  28  │  30  │ ... │  32  │  ← Row 3 (Light blue)
├─────────────────────────┼──────┼──────┼──────┼─────┼──────┤
│ ...                     │  ... │  ... │  ... │ ... │  ... │
└─────────────────────────┴──────┴──────┴──────┴─────┴──────┘

⚠️ Yellow-highlighted topics are unmapped (not in canonical list)
```

### Formatting Rules

```python
# Header row
fill = Blue (#366092)
font = Bold, White
alignment = Center

# Data rows
if row % 2 == 0:
    fill = Light Blue (#E8EFF7)
else:
    fill = White

# Unmapped topics (column A only)
if topic not in canonical_mapping:
    fill = Yellow (#FFF4CC)
    font = Italic

# Column widths
Column A (Topic): 40 characters
Columns B-AE (Dates): 12 characters
```

### Validation Output

```
📊 VALIDATION REPORT:
  Expected canonical topics: 18
  Topics appearing in Excel: 20
  ⚠️  WARNING: Mismatch detected (20 vs 18)

  ❌ Topics in Excel but NOT in canonical mapping (2):
    - 'delivery guy extremely rude' (suggested: 'Delivery partner unprofessional')
    - 'food spoiled badly' (suggested: 'Food freshness issues')

  ✅ All 18 canonical topics appear in data
```

---

## Optimization Strategies

### 1. Caching (100x speedup)

```
Without cache:
  Scrape 5000 reviews: 5-10 minutes

With cache:
  Load 5000 reviews: 2-3 seconds

Speedup: 100-200x
```

### 2. Batch Processing (20x speedup)

```
Individual requests:
  5000 reviews × 1 request = 5000 requests
  Time: ~30 minutes (with API limits)

Batch requests (20 per batch):
  5000 reviews ÷ 20 = 250 requests
  Time: ~8 minutes

Speedup: ~4x
```

### 3. Parallel Processing (8x speedup)

```
Sequential batches:
  250 batches × 3 sec = 750 seconds

Parallel (8 workers):
  250 batches ÷ 8 workers × 3 sec = 94 seconds

Speedup: 8x
```

### 4. Combined Optimization

```
Base (sequential, no cache):
  Scrape: 10 min + Extract: 30 min = 40 minutes

Optimized (cache + batch + parallel):
  Load cache: 3 sec + Extract: 90 sec = 93 seconds

Total speedup: 26x
```

### 5. Model Selection

```
Extraction (bulk):
  Model: qwen2.5:32b (smaller, faster)
  Frequency: 250 calls
  Time per call: 2-3 sec

Consolidation (once):
  Model: llama3.1:70b (larger, better quality)
  Frequency: 1 call
  Time per call: 5-10 sec

Strategy: Use fast model for repetitive tasks,
          high-quality model for critical once-off tasks
```

---

## Data Flow Summary

### End-to-End Example

**Input**:
```
App: in.swiggy.android
Date Range: Dec 1 - Dec 30, 2024
```

**Flow**:
```
1. Scrape → 5,243 reviews
2. Extract → 20,972 raw topics
3. Consolidate → 18 canonical topics
4. Map → 30 × 18 count matrix
5. Generate → Excel file (18 rows × 31 columns)
```

**Output**:
```
output/swiggy_trend_report_2024-12-30.xlsx
Size: ~50 KB
Contains:
  - 18 topics
  - 30 days of data
  - 540 cells with counts
  - Formatting + legends
```

### Performance Metrics

| Metric | Value |
|--------|-------|
| Reviews processed | 5,243 |
| Topics extracted | 20,972 |
| Canonical topics | 18 |
| API calls (with batching) | ~262 |
| Processing time (cached) | ~3 min |
| Processing time (no cache) | ~12 min |
| Output file size | ~50 KB |
| Data reduction ratio | 1165:1 |

---

## See Also

- [Architecture](architecture.md) - System design
- [User Guide](user-guide.md) - How to use
- [API Reference](api-reference.md) - Code documentation
- [Troubleshooting](troubleshooting.md) - Common issues
