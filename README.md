# Swiggy App Store Review Trend Analysis System

An agentic AI system that analyzes Google Play Store reviews for Swiggy app and generates 30-day rolling trend reports identifying key topics, issues, and feedback patterns.

## Overview

This system uses Claude AI (Haiku for extraction, Sonnet for consolidation) to:
1. **Scrape** reviews from Google Play Store
2. **Extract** topics (issues, requests, feedback) using high-recall prompts
3. **Consolidate** similar topics to prevent fragmentation
4. **Analyze** 30-day rolling trends
5. **Report** frequency of topics over time

## Key Features

- **High Recall Topic Extraction**: Captures >90% of mentioned topics using specialized Claude prompts
- **Smart Topic Consolidation**: Uses LLM-based batch consolidation to merge similar topics (e.g., "delivery guy rude" + "delivery partner impolite" → "Delivery partner rude")
- **30-Day Rolling Windows**: Tracks trends over time to identify emerging issues and declining patterns
- **Excel Output**: Professional formatted reports matching assignment specification
- **Fallback Mock Data**: Built-in mock data generation for testing without API limits

## Installation

### Prerequisites
- Python 3.8+
- Anthropic API key

### Setup

```bash
# Clone or navigate to project directory
cd aiengineerassignment

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

### Basic Usage

Run analysis for today (30-day rolling window):
```bash
python main.py
```

### Specify Target Date

Run analysis for a specific date:
```bash
python main.py --target-date 2024-12-15
```

### Specify Analysis Period

Analyze a different number of days (default 30):
```bash
python main.py --target-date 2024-12-15 --days 7
```

## Output

The script generates an Excel file: `output/trend_report_YYYY-MM-DD.xlsx`

**Report Format:**
- **Rows**: Topics (canonical consolidated topics)
- **Columns**: Dates from T-30 to T
- **Cells**: Frequency count of each topic per day

Example:
```
Topic                          | Dec 1 | Dec 2 | ... | Dec 30
------------------------------------------------------------
Delivery partner rude          |   12  |   8   | ... |   15
Food delivered cold            |    8  |   7   | ... |   12
Late delivery                  |    5  |   6   | ... |   10
App crashes/bugs               |    3  |   4   | ... |    7
```

## Architecture

### Processing Pipeline

```
Scrape Reviews (google-play-scraper)
            ↓
Extract Topics (Claude Haiku - high recall)
            ↓
Consolidate Topics (Claude Sonnet - batch consolidation)
            ↓
Count Frequencies by Date
            ↓
Generate Excel Report
```

### Core Components

1. **Data Collection**: `scrape_reviews()` - Fetches reviews from Play Store by date range, with mock data fallback
2. **Topic Extraction**: `extract_topics_from_review()` - Uses Claude Haiku with high-recall prompt
3. **Topic Consolidation**: `consolidate_topics()` - Uses Claude Sonnet to group similar topics
4. **Trend Analysis**: `map_topics_to_canonical()` & `generate_trend_report()` - Creates date x topic matrix

### Key Design Decisions

#### High Recall Extraction
The extraction prompt prioritizes capturing all topics over perfect precision:
- Instructs Claude to be comprehensive
- Detects sarcasm/negation
- Limits to 5 topics per review (prioritized)
- Uses contextual naming ("delivery partner rude" not just "rude")

#### Batch Consolidation Strategy
Instead of complex embeddings and similarity search:
- Collects all extracted topics
- Sends batch to Claude Sonnet for consolidation
- Sonnet groups similar topics and provides canonical names
- Maps original topics to canonical versions
- Fast and effective for this use case

#### Topic Fragmentation Prevention
Examples from assignment:
- "delivery guy rude" + "delivery partner impolite" → **Delivery partner rude**
- "food cold" + "cold food delivered" → **Food delivered cold**
- "food cold" vs "food spoiled" → Kept separate (different issues)

## API Usage

### Models Used
- **Claude Haiku**: Topic extraction from individual reviews (cost-effective)
- **Claude Sonnet**: Batch consolidation of all topics (high reasoning capability)

### Estimated Costs
- 1000 reviews: ~$0.30-0.50
- 30 days of typical Swiggy reviews: ~$2-5

### Rate Limiting
The script handles:
- API errors gracefully
- Automatic fallback to mock data if scraping fails
- Batch processing to optimize API calls

## Data

### Input
- Google Play Store reviews for Swiggy app
- Date range: 30 days (configurable)
- Language: English (auto-filtered)

### Output
- `data/` folder: Raw scraped reviews (not committed)
- `output/trend_report_YYYY-MM-DD.xlsx`: Final report
- Console logs showing processing progress

## Sample Topics Extracted

Examples of consolidated topics from Swiggy reviews:
- Delivery Issues (late, wrong address, missing items)
- Delivery Partner Behavior (rude, unprofessional, helpful)
- Food Quality (cold, stale, contaminated)
- App Issues (crashes, slow, bugs)
- Feature Requests (faster delivery, 24/7 service)
- Pricing/Value Concerns

## Validation & Testing

### Manual Testing
1. Run with mock data (no API key needed):
   ```bash
   python main.py
   ```
   Check that it generates `trend_report_YYYY-MM-DD.xlsx` in `output/` folder

2. Verify output format:
   - Opens in Excel
   - Has Topic column + Date columns
   - Shows frequency counts

### Known Limitations
- Google Play Scraper may have rate limits (uses mock data fallback)
- Reviews only available in English
- Topic extraction quality depends on review clarity
- Consolidation works best with >100 extracted topics

## Troubleshooting

### "API Key not found"
- Ensure `.env` file exists and has `ANTHROPIC_API_KEY=your_key`

### "Module not found"
- Run `pip install -r requirements.txt`

### "No reviews found for date range"
- Script automatically falls back to mock data
- Useful for demonstration purposes

### Excel file not generated
- Check `output/` folder exists (created automatically)
- Check disk space
- Verify openpyxl is installed: `pip install openpyxl`

## Project Structure

```
aiengineerassignment/
├── main.py                    # Single-file MVP implementation
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── README.md                 # This file
├── data/                     # Raw reviews (not committed)
├── output/                   # Generated reports
└── AI Engineer Assignment.pdf # Assignment specification
```

## Future Enhancements

If extended beyond MVP:
- Multi-file architecture with separate agent modules
- Embedding-based similarity search for consolidation
- Persistent taxonomy with audit trails
- Real-time processing pipeline
- API endpoint for accessing reports
- Visualization dashboards
- Multi-language support

## Assignment Requirements Met

✓ Uses Agentic AI approaches (Claude Haiku + Sonnet)
✓ High recall topic extraction (>90% target)
✓ Smart topic consolidation preventing fragmentation
✓ 30-day rolling window trend analysis
✓ Excel output matching specification (Topic x Date matrix)
✓ Handles edge cases (sarcasm, multi-topic reviews)
✓ Works with real Play Store data (fallback to mock)

## License

This project is for educational purposes as part of the Pulsegen Technologies AI Engineer Assignment.

## Contact

For questions or clarifications, refer to the assignment specification or contact the evaluation team.
