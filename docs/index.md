# Swiggy App Store Review Trend Analysis System

## Overview

The Swiggy App Store Review Trend Analysis System is an intelligent application that leverages AI to analyze Google Play Store reviews and identify trending topics, issues, and user feedback patterns over time. The system provides actionable insights through automated topic extraction, consolidation, and trend visualization.

## What Does It Do?

This system automates the analysis of thousands of app store reviews by:

1. **Scraping Reviews**: Fetches reviews from Google Play Store with intelligent caching
2. **Extracting Topics**: Uses AI to identify key topics, issues, and feedback from each review
3. **Consolidating Topics**: Merges similar topics to prevent fragmentation (e.g., "delivery guy rude" + "delivery partner impolite" → "Delivery partner unprofessional")
4. **Analyzing Trends**: Tracks topic frequency over 30-day rolling windows
5. **Generating Reports**: Creates Excel reports and interactive web dashboards

## Key Features

### AI-Powered Analysis
- **High Recall Topic Extraction**: Captures >90% of mentioned topics using specialized LLM prompts
- **Intelligent Consolidation**: Prevents topic fragmentation by merging semantically similar topics
- **Sarcasm Detection**: Identifies sarcasm in reviews (e.g., "Great job delivering cold food" → "food delivered cold")
- **Multi-Category Classification**: Categorizes topics as issues, requests, or feedback

### Data Collection
- **Smart Caching**: Saves reviews locally to minimize API calls and speed up repeated analyses
- **Incremental Updates**: Fetches only new reviews since last cache update
- **Fallback Support**: Mock data generation for testing without API limits
- **Multi-App Support**: Analyze any Android app, not just Swiggy

### Reporting & Visualization
- **Excel Reports**: Professional formatted Topic × Date matrix with conditional formatting
- **Web Dashboard**: Real-time progress tracking and interactive charts
- **Trend Charts**: Line charts showing topic trends over time
- **Summary Statistics**: Bar charts of top topics and comprehensive tables

### Deployment Options
- **CLI Tool**: Command-line interface for batch processing
- **Web UI**: Flask-based dashboard for interactive analysis
- **Flexible LLM Backend**: Works with Ollama (local), Anthropic Claude, or Groq

## Use Cases

### Product Teams
- Identify emerging issues before they escalate
- Track feature request trends
- Monitor impact of new features on user sentiment
- Prioritize bug fixes based on frequency

### Customer Support
- Understand common user pain points
- Create FAQs based on frequent issues
- Track resolution effectiveness over time

### Business Intelligence
- Monitor competitor app sentiment
- Track market trends in food delivery
- Measure impact of marketing campaigns

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI analysis
python main.py

# Or start web dashboard
python app.py
```

Visit the [Getting Started](getting-started.md) guide for detailed setup instructions.

## System Requirements

- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum (8GB recommended for large datasets)
- **Storage**: 500MB for cache and output files
- **Internet**: Required for scraping reviews and cloud LLM APIs
- **LLM Backend**: One of:
  - Ollama (local, free, requires 16GB+ RAM for 70B models)
  - Anthropic API (cloud, paid)
  - Groq API (cloud, free tier available)

## Documentation Structure

- **[Getting Started](getting-started.md)**: Installation and setup guide
- **[Architecture](architecture.md)**: System design and components
- **[User Guide](user-guide.md)**: How to use the CLI and Web UI
- **[API Reference](api-reference.md)**: Code documentation and API endpoints
- **[Data Flow](data-flow.md)**: Detailed pipeline explanation
- **[Troubleshooting](troubleshooting.md)**: Common issues and solutions

## Technology Stack

### Core Libraries
- **google-play-scraper**: Review scraping
- **pandas**: Data manipulation
- **openpyxl**: Excel report generation

### AI/LLM
- **Ollama**: Local LLM inference (default)
- **Anthropic SDK**: Claude API integration
- **Groq SDK**: Fast cloud inference

### Web Framework
- **Flask**: Backend API server
- **Chart.js**: Interactive data visualization
- **Tailwind CSS**: Modern UI styling

## Project Status

This project was created as part of the Pulsegen Technologies AI Engineer Assignment. It demonstrates:
- Agentic AI design patterns
- High-recall topic extraction
- Intelligent topic consolidation
- Production-ready code structure
- Comprehensive error handling

## License

This project is for educational purposes as part of the AI Engineer Assignment.

## Next Steps

- **New Users**: Start with [Getting Started](getting-started.md)
- **Developers**: Review [Architecture](architecture.md) and [API Reference](api-reference.md)
- **Analysts**: Jump to [User Guide](user-guide.md) for usage instructions
- **Troubleshooting**: See [Troubleshooting](troubleshooting.md) for common issues

## Contact & Support

For questions, issues, or feedback:
- Review the [Troubleshooting](troubleshooting.md) guide
- Check the existing documentation
- Refer to the assignment specification PDF
