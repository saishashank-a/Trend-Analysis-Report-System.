#!/usr/bin/env python3
"""
Swiggy App Store Review Trend Analysis System
Analyzes reviews from Google Play Store using Agentic AI approaches
"""

import json
import os
import sys
import re
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Third-party imports
import pandas as pd
from anthropic import Anthropic
from google_play_scraper import app, reviews, Sort
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Anthropic client
client = Anthropic()

# Configuration
SWIGGY_APP_ID = "in.swiggy.android"
DATA_DIR = Path("data")
OUTPUT_DIR = Path("output")
CACHE_DIR = Path("cache")
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# Prompts
EXTRACTION_PROMPT = """Extract ALL topics from this Swiggy review. Prioritize HIGH RECALL.

Include context in topic names (e.g., "delivery partner rude" not just "rude").
Detect sarcasm: "Great job delivering cold food" → "food delivered cold"
Return max 5 most important topics.

Review: {review_text}

Output JSON array ONLY (no markdown, just raw JSON):
[{{"topic": "descriptive phrase", "category": "issue|request|feedback"}}]"""

BATCH_EXTRACTION_PROMPT = """Extract ALL topics from these app reviews. Prioritize HIGH RECALL.

Include context in topic names (e.g., "delivery partner rude" not just "rude").
Detect sarcasm: "Great job delivering cold food" → "food delivered cold"
Return max 5 most important topics per review.

Reviews:
{reviews_batch}

Output JSON object ONLY (no markdown, just raw JSON):
{{"reviews": [
  {{"review_id": "0", "topics": [{{"topic": "descriptive phrase", "category": "issue|request|feedback"}}]}},
  {{"review_id": "1", "topics": [{{"topic": "descriptive phrase", "category": "issue|request|feedback"}}]}},
  ...
]}}"""

CONSOLIDATION_PROMPT = """You are consolidating topics from app reviews. BE EXTREMELY AGGRESSIVE - aim for 15-25 final topics MAXIMUM.

Here are {num_topics} extracted topics:
{topics_list}

CRITICAL RULES - MERGE EVERYTHING SIMILAR:
1. **ALL positive feedback** → "Positive feedback" (good, great, excellent, amazing, love, helpful, friendly, fast, etc.)
2. **ALL negative delivery partner behavior** → "Delivery partner unprofessional" (rude, impolite, disrespectful, unprofessional, etc.)
3. **ALL delivery delays** → "Delivery delay" (late, delayed, slow, 2 hours, extreme delay, etc.)
4. **ALL food quality issues** → Merge into 2-3 categories ONLY:
   - "Food temperature issues" (cold, hot, lukewarm)
   - "Food freshness issues" (stale, spoiled, rotten, old)
   - "Food quality issues" (bad quality, taste, portion)
5. **ALL app technical issues** → Merge into 2 categories:
   - "App crashes/freezes" (crash, freeze, not responding, stuck)
   - "App performance issues" (slow, laggy, buggy, glitches)
6. **ALL feature removal/requests** → Use ONE topic per feature:
   - "10 minute delivery removed"
   - "24/7 service request"
7. **Ignore ALL grammar differences**: tense, plural, word order, articles
8. **Merge similar sentiment**: "good", "great", "excellent", "awesome" → "Positive feedback"

AGGRESSIVE MERGING EXAMPLES:
- "good service", "great app", "excellent delivery", "love it", "awesome", "amazing" → "Positive feedback"
- "delivery guy rude", "rude rider", "impolite partner", "disrespectful delivery" → "Delivery partner unprofessional"
- "food cold", "cold food", "food not hot", "lukewarm food" → "Food temperature issues"
- "app crash", "app freezes", "app not working", "app stuck" → "App crashes/freezes"
- "app slow", "app laggy", "app buggy", "app has bugs", "app glitchy" → "App performance issues"

TARGET: 15-25 CANONICAL TOPICS MAXIMUM. Be RUTHLESS in merging!

OUTPUT (JSON only, no markdown):
{{
  "canonical_topics": [
    {{
      "canonical_name": "Delivery delay",
      "variations": ["delivery delay 2 hours", "delivery delayed 2 hours", "2 hour delivery wait", "delivery extremely delayed"]
    }},
    ...
  ]
}}"""


def get_cache_file_path(app_id: str) -> Path:
    """Get cache file path for an app. Creates per-app subdirectory."""
    app_cache_dir = CACHE_DIR / app_id
    app_cache_dir.mkdir(exist_ok=True)
    return app_cache_dir / "reviews_cache.json"


def load_cached_reviews(app_id: str) -> tuple[list, datetime]:
    """
    Load cached reviews for an app.
    Returns: (reviews_list, last_update_time)
    """
    cache_file = get_cache_file_path(app_id)

    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                reviews = data.get('reviews', [])
                last_update = datetime.fromisoformat(data.get('last_update', datetime.now().isoformat()))

                # Convert all datetime string fields back to datetime objects
                datetime_fields = ['at', 'repliedAt']
                for review in reviews:
                    for field in datetime_fields:
                        if field in review and isinstance(review.get(field), str):
                            try:
                                review[field] = datetime.fromisoformat(review[field])
                            except (ValueError, TypeError):
                                # Keep as string if conversion fails
                                pass

                print(f"  ✓ Loaded {len(reviews)} cached reviews for {app_id}")
                print(f"    Last updated: {last_update.date()}")
                return reviews, last_update
        except Exception as e:
            print(f"  Warning: Could not load cache: {e}")
            return [], None

    return [], None


def save_cached_reviews(app_id: str, reviews: list) -> None:
    """Save reviews to cache for an app."""
    cache_file = get_cache_file_path(app_id)

    try:
        # Convert datetime objects to ISO strings for JSON serialization
        serializable_reviews = []
        for review in reviews:
            review_copy = review.copy()
            # Convert all datetime fields to ISO strings
            for key, value in review_copy.items():
                if isinstance(value, datetime):
                    review_copy[key] = value.isoformat()
            serializable_reviews.append(review_copy)

        cache_data = {
            'app_id': app_id,
            'last_update': datetime.now().isoformat(),
            'total_reviews': len(reviews),
            'reviews': serializable_reviews
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

        # Get file size in MB
        file_size_mb = cache_file.stat().st_size / (1024 * 1024)
        print(f"  ✓ Cached {len(reviews)} reviews for {app_id} ({file_size_mb:.2f} MB)")
    except Exception as e:
        print(f"  Warning: Could not save cache: {e}")


def extract_json_from_response(response_text: str) -> dict:
    """Extract JSON from Claude response, handling markdown code blocks."""
    # Remove markdown code blocks if present
    text = response_text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    return json.loads(text)


def scrape_reviews(app_id: str, start_date: datetime, end_date: datetime) -> Dict[str, List[dict]]:
    """
    Scrape reviews with smart stopping + intelligent caching.
    - Uses cache to avoid re-fetching
    - Stops fetching once past start_date (since sorted NEWEST first)
    - Saves new data to cache for future use
    Returns reviews organized by date.
    """
    print(f"Scraping reviews from {start_date.date()} to {end_date.date()}...")
    reviews_by_date = {}

    print("\nChecking cache...")
    # Load cached reviews
    cached_reviews, last_update = load_cached_reviews(app_id)

    # Combine cached reviews with any new ones
    all_reviews = cached_reviews.copy() if cached_reviews else []
    fetch_from_newest = True

    if cached_reviews:
        # Check if cache is still fresh (less than 1 day old)
        if last_update and (datetime.now() - last_update).days < 1:
            print(f"  Cache is fresh (less than 1 day old)")
            fetch_from_newest = False
        else:
            print(f"  Cache is older than 1 day, updating...")
            fetch_from_newest = True

    if fetch_from_newest:
        print("\nFetching new reviews from Play Store...")
        print("(Smart stopping: will stop once past start_date)\n")

        continuation_token = None
        batch_num = 0
        reached_start_date = False

        try:
            # Fetch reviews until we go past the start_date
            while not reached_start_date:
                batch_num += 1
                print(f"  Batch {batch_num}...", end=" ", flush=True)

                try:
                    # Fetch reviews with pagination
                    if batch_num == 1:
                        # First batch without token
                        result, continuation_token = reviews(
                            app_id,
                            sort=Sort.NEWEST,
                            count=500,
                            lang='en',
                            country='in'
                        )
                    else:
                        # Subsequent batches with continuation token
                        if not continuation_token:
                            print("(No more reviews)")
                            break

                        result, continuation_token = reviews(
                            app_id,
                            sort=Sort.NEWEST,
                            count=500,
                            lang='en',
                            country='in',
                            continuation_token=continuation_token
                        )

                    if not result:
                        print("(Empty batch - stopping)")
                        break

                    batch_fetched = len(result)
                    print(f"{batch_fetched} reviews (Total: {len(all_reviews) + batch_fetched})")

                    # Check if we've gone past the start_date
                    for review in result:
                        review_date = review['at'].date()
                        if review_date < start_date.date():
                            # We've passed the start_date, can stop fetching
                            reached_start_date = True
                            all_reviews.append(review)
                            break
                        all_reviews.append(review)

                    if reached_start_date:
                        print("  ✓ Reached start_date, stopping fetch (smart stopping)")

                except Exception as batch_error:
                    print(f"(Error: {batch_error})")
                    break

            print(f"\n✓ Total reviews fetched: {len(all_reviews)}")

            # Save to cache
            save_cached_reviews(app_id, all_reviews)

        except Exception as e:
            print(f"Warning: Scraping error: {e}")
            if not all_reviews:
                print("Proceeding with mock data for demonstration...")
                return generate_mock_reviews(start_date, end_date)

    # Filter by date range
    print(f"\nFiltering reviews for {start_date.date()} to {end_date.date()}...\n")

    for review in all_reviews:
        review_date = review['at'].date()
        if start_date.date() <= review_date <= end_date.date():
            date_str = review_date.isoformat()
            if date_str not in reviews_by_date:
                reviews_by_date[date_str] = []
            reviews_by_date[date_str].append(review)

    reviews_in_range = sum(len(v) for v in reviews_by_date.values())
    print(f"✓ Found {reviews_in_range} reviews within date range")

    # If no reviews in the specified date range, fall back to mock data
    if reviews_in_range == 0:
        print(f"\nNo reviews found for {start_date.date()} to {end_date.date()}")
        print("Using mock data for demonstration...")
        return generate_mock_reviews(start_date, end_date)

    return reviews_by_date


def generate_mock_reviews(start_date: datetime, end_date: datetime) -> Dict[str, List[dict]]:
    """Generate mock reviews for demonstration purposes."""
    mock_reviews_text = [
        "Delivery was very late, food was cold",
        "Delivery guy was very rude to me",
        "App keeps crashing when I try to checkout",
        "Please bring back the 10 minute delivery option",
        "Food quality has really declined lately",
        "Maps integration not working properly",
        "Great service today, delivery was fast!",
        "Delivery partner was impolite and disrespectful",
        "Food arrived stale, very disappointed",
        "Why did you remove the express delivery?",
        "App is slow and buggy",
        "Delivery person was helpful and friendly",
        "Cold food delivered again",
        "Instamart should be open 24/7",
        "Delivery delay of 2 hours",
    ]

    reviews_by_date = {}
    current_date = start_date
    review_idx = 0

    while current_date <= end_date:
        date_str = current_date.date().isoformat()
        date_reviews = []

        # Add 10-20 reviews per day
        for i in range(10 + (hash(date_str) % 10)):
            date_reviews.append({
                'reviewId': f"review_{date_str}_{i}",
                'userName': f"User{i}",
                'userImage': "",
                'content': mock_reviews_text[(review_idx + i) % len(mock_reviews_text)],
                'score': 1 + (hash(date_str + str(i)) % 5),
                'thumbsUpCount': 0,
                'reviewCreatedVersion': None,
                'at': current_date.replace(hour=10 + (i % 12), minute=i % 60),
                'replyContent': None,
                'repliedAt': None
            })
            review_idx += 1

        reviews_by_date[date_str] = date_reviews
        current_date += timedelta(days=1)

    print(f"✓ Generated {sum(len(v) for v in reviews_by_date.values())} mock reviews")
    return reviews_by_date


def extract_topics_from_review(review_text: str) -> List[dict]:
    """Extract topics from a single review using Claude Haiku."""
    try:
        prompt = EXTRACTION_PROMPT.format(review_text=review_text)

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text
        topics = extract_json_from_response(response_text)

        # Ensure topics is a list
        if not isinstance(topics, list):
            return []
        return topics

    except Exception as e:
        # Fallback: Use heuristic topic extraction
        return extract_topics_heuristic(review_text)


def extract_topics_batch(reviews_batch: List[dict]) -> Dict[int, List[dict]]:
    """Extract topics from a batch of reviews using a single API call."""
    try:
        # Build batch string (optimized for larger batches)
        batch_str = ""
        for idx, review in enumerate(reviews_batch):
            content = review.get('content', '')
            if content and len(content) >= 5:
                # Truncate very long reviews to save tokens
                truncated_content = content[:500] if len(content) > 500 else content
                batch_str += f"\n{idx}. {truncated_content}\n"

        if not batch_str:
            return {}

        prompt = BATCH_EXTRACTION_PROMPT.format(reviews_batch=batch_str)

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=6000,  # Increased for larger batches
            timeout=30.0,  # 30 second timeout
            messages=[{"role": "user", "content": prompt}]
        )

        # Check rate limit headers (on first request only)
        if hasattr(response, '_headers') and not hasattr(extract_topics_batch, '_rate_limit_shown'):
            headers = response._headers
            if 'x-ratelimit-requests-limit' in headers:
                print(f"\n  📊 API Rate Limits Detected:")
                print(f"    Requests/min: {headers.get('x-ratelimit-requests-limit', 'N/A')}")
                print(f"    Tokens/min: {headers.get('x-ratelimit-tokens-limit', 'N/A')}")
                print(f"    Remaining requests: {headers.get('x-ratelimit-requests-remaining', 'N/A')}")
                print(f"    Remaining tokens: {headers.get('x-ratelimit-tokens-remaining', 'N/A')}\n")
                extract_topics_batch._rate_limit_shown = True

        response_text = response.content[0].text
        result = extract_json_from_response(response_text)

        # Parse results
        topics_by_idx = {}
        if 'reviews' in result:
            for review_result in result['reviews']:
                review_id = int(review_result.get('review_id', -1))
                topics = review_result.get('topics', [])
                if review_id >= 0 and isinstance(topics, list):
                    topics_by_idx[review_id] = topics

        return topics_by_idx

    except Exception as e:
        # Fallback: Extract individually using heuristics
        result = {}
        for idx, review in enumerate(reviews_batch):
            content = review.get('content', '')
            if content and len(content) >= 5:
                result[idx] = extract_topics_heuristic(content)
        return result


def extract_topics_heuristic(review_text: str) -> List[dict]:
    """Fallback: Extract topics using heuristics (for demo without API key)."""
    topics = []
    text_lower = review_text.lower()

    # Define keyword patterns
    patterns = [
        ("rude", "Rude/Unprofessional Delivery Partner", "issue"),
        ("late", "Late Delivery", "issue"),
        ("cold", "Food Delivered Cold", "issue"),
        ("stale", "Food Quality Issue - Stale", "issue"),
        ("crash", "App Crashes/Bugs", "issue"),
        ("slow", "App Performance Issue", "issue"),
        ("10 minute", "Fast Delivery Feature Request", "request"),
        ("24/7", "24/7 Service Request", "request"),
        ("delivery", "Delivery Issue", "issue"),
        ("app", "App Issue", "issue"),
        ("great", "Positive Feedback", "praise"),
        ("good", "Positive Feedback", "praise"),
        ("helpful", "Positive Feedback - Helpful Service", "praise"),
        ("fast", "Fast Delivery Feedback", "praise"),
    ]

    found_topics = set()
    for keyword, topic_name, category in patterns:
        if keyword in text_lower:
            found_topics.add(topic_name)

    # Convert to required format, limit to 5
    for topic_name in list(found_topics)[:5]:
        # Find category for this topic
        category = next((c for k, t, c in patterns if t == topic_name), "feedback")
        topics.append({
            "topic": topic_name,
            "category": category
        })

    return topics if topics else [{"topic": "General Review", "category": "feedback"}]


def process_batch_wrapper(args):
    """Wrapper function for parallel batch processing."""
    batch_id, batch, batch_start = args
    try:
        print(f"    → Processing batch {batch_id} ({len(batch)} reviews)...", flush=True)
        batch_topics = extract_topics_batch(batch)
        # Collect topics from this batch
        topics = []
        for idx, review in enumerate(batch):
            if idx in batch_topics:
                extracted = batch_topics[idx]
                for item in extracted:
                    if isinstance(item, dict) and 'topic' in item:
                        topics.append(item['topic'])
        print(f"    ✓ Batch {batch_id} complete ({len(topics)} topics extracted)", flush=True)
        return batch_id, topics, len(batch)
    except Exception as e:
        print(f"    ✗ Batch {batch_id} failed: {e}", flush=True)
        return batch_id, [], len(batch)


def extract_all_topics(reviews_by_date: Dict[str, List[dict]]) -> Dict[str, List[str]]:
    """
    Extract topics from all reviews using optimized parallel batch processing.
    Returns mapping of date -> list of unique topics.
    """
    print("Extracting topics from reviews (using parallel batch processing)...")
    topics_by_date = {}
    total_reviews = sum(len(reviews) for reviews in reviews_by_date.values())

    # OPTIMIZED settings for Build tier (50 RPM)
    BATCH_SIZE = 20  # 20 reviews per batch
    MAX_WORKERS = 8  # 8 parallel workers for faster processing

    print(f"  Configuration: {BATCH_SIZE} reviews/batch, {MAX_WORKERS} parallel workers")
    print(f"  Total reviews: {total_reviews}")
    estimated_batches = (total_reviews // BATCH_SIZE) + 1
    print(f"  Total batches: {estimated_batches}")
    print(f"  Note: This will take ~{int(estimated_batches / MAX_WORKERS * 3)} seconds (API dependent)\n")

    start_time = time.time()

    # Calculate dynamic progress interval
    if total_reviews <= 100:
        progress_interval = 10
    elif total_reviews <= 500:
        progress_interval = 50
    elif total_reviews <= 1000:
        progress_interval = 100
    elif total_reviews <= 2000:
        progress_interval = 200
    else:
        progress_interval = max(total_reviews // 10, 500)

    processed = 0

    for date_str in sorted(reviews_by_date.keys()):
        date_reviews = reviews_by_date[date_str]

        # Create batches for this date
        batches = []
        batch_id = 0
        for batch_start in range(0, len(date_reviews), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(date_reviews))
            batch = date_reviews[batch_start:batch_end]
            batches.append((batch_id, batch, batch_start))
            batch_id += 1

        # Process batches in parallel
        date_topics = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all batches for parallel processing
            futures = {executor.submit(process_batch_wrapper, batch_args): batch_args[0]
                      for batch_args in batches}

            # Collect results as they complete
            for future in as_completed(futures):
                batch_id, topics, batch_size = future.result()
                date_topics.extend(topics)
                processed += batch_size

                if processed % progress_interval == 0:
                    elapsed = time.time() - start_time
                    rate = processed / elapsed if elapsed > 0 else 0
                    remaining = (total_reviews - processed) / rate if rate > 0 else 0
                    print(f"  Processed {processed}/{total_reviews} reviews | Elapsed: {int(elapsed)}s | ETA: {int(remaining)}s | Rate: {int(rate)}/s")

        if date_topics:
            topics_by_date[date_str] = date_topics

    total_time = time.time() - start_time
    print(f"✓ Extracted topics from {processed} reviews using ULTRA-FAST parallel processing")
    print(f"  Total time: {int(total_time)} seconds ({total_time/60:.1f} minutes)")
    print(f"  Average rate: {int(processed/total_time)} reviews/second")
    return topics_by_date


def normalize_topic(topic: str) -> str:
    """Normalize topic text for better consolidation matching."""
    # Convert to lowercase
    normalized = topic.lower().strip()

    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)

    # Normalize common word variations
    replacements = {
        r'\b(is|are|was|were|be|being|been)\b': '',  # Remove "to be" verbs
        r'\b(a|an|the)\b': '',  # Remove articles
        r'\b(very|extremely|really|so|too)\b': '',  # Remove intensifiers
        r'\bhas\b': '',
        r'\bcontains\b': '',
        r'\bdelivery partner\b': 'delivery partner',  # Normalize to singular form
        r'\bdelivery guy\b': 'delivery partner',
        r'\bdelivery person\b': 'delivery partner',
        r'\brider\b': 'delivery partner',
        r'\b(\d+)\s*hour[s]?\b': r'\1 hour',  # Normalize hours
        r'\b(\d+)\s*min(ute)?[s]?\b': r'\1 minute',  # Normalize minutes
    }

    for pattern, replacement in replacements.items():
        normalized = re.sub(pattern, replacement, normalized)

    # Remove extra spaces created by replacements
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    return normalized


def consolidate_topics(all_topics: List[str]) -> Dict[str, List[str]]:
    """
    Consolidate similar topics using Claude Sonnet with aggressive grouping.
    Returns mapping of canonical_topic -> list of variations.
    """
    if not all_topics:
        return {}

    # Remove duplicates but keep count
    unique_topics = list(set(all_topics))
    print(f"Consolidating {len(unique_topics)} unique topics...")

    # Pre-process: Group exact matches after normalization
    normalized_groups = {}
    for topic in unique_topics:
        normalized = normalize_topic(topic)
        if normalized not in normalized_groups:
            normalized_groups[normalized] = []
        normalized_groups[normalized].append(topic)

    print(f"  After normalization: {len(normalized_groups)} topic groups")

    # Create topic list string (use one representative from each normalized group)
    representative_topics = [topics[0] for topics in normalized_groups.values()]
    topics_str = "\n".join([f"- {t}" for t in representative_topics[:200]])  # Increased limit
    if len(representative_topics) > 200:
        topics_str += f"\n... and {len(representative_topics) - 200} more topics"

    try:
        prompt = CONSOLIDATION_PROMPT.format(
            num_topics=len(representative_topics),
            topics_list=topics_str
        )

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,  # Increased for more topics
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text
        result = extract_json_from_response(response_text)

        # Build canonical mapping
        canonical_mapping = {}
        if 'canonical_topics' in result:
            for item in result['canonical_topics']:
                canonical = item.get('canonical_name', '')
                variations = item.get('variations', [])

                if canonical:
                    # Add all variations from normalized groups
                    all_variations = []
                    for variation in variations:
                        # Find all topics in the same normalized group
                        norm_var = normalize_topic(variation)
                        if norm_var in normalized_groups:
                            all_variations.extend(normalized_groups[norm_var])

                    canonical_mapping[canonical] = list(set(all_variations))

        print(f"✓ Consolidated to {len(canonical_mapping)} canonical topics")
        return canonical_mapping

    except Exception as e:
        print(f"  Warning: Consolidation error: {e}")
        # Fallback: use heuristic consolidation
        return consolidate_topics_heuristic(unique_topics)


def consolidate_topics_heuristic(unique_topics: List[str]) -> Dict[str, List[str]]:
    """Fallback: Consolidate topics using heuristics with AGGRESSIVE merging."""
    # Define VERY aggressive consolidation rules
    consolidation_rules = {
        "Positive feedback": [
            "positive", "good", "great", "excellent", "amazing", "awesome", "love",
            "best", "helpful", "friendly", "fast", "quick", "perfect", "satisfied"
        ],
        "Delivery partner unprofessional": [
            "rude", "impolite", "unprofessional", "disrespectful", "behavior", "attitude"
        ],
        "Delivery delay": [
            "late", "delay", "slow", "hour", "wait", "time", "delayed"
        ],
        "Food temperature issues": [
            "cold", "hot", "warm", "temperature", "lukewarm"
        ],
        "Food freshness issues": [
            "stale", "spoiled", "rotten", "old", "fresh", "bad quality"
        ],
        "App crashes/freezes": [
            "crash", "freeze", "stuck", "not working", "not responding", "hang"
        ],
        "App performance issues": [
            "slow", "lag", "bug", "glitch", "issue", "problem", "error"
        ],
        "10 minute delivery removed": [
            "10 minute", "bolt", "express", "fast delivery"
        ],
        "24/7 service request": [
            "24/7", "24 hour", "all night", "late night", "instamart"
        ],
        "Missing items": [
            "missing", "forgot", "didn't receive", "not delivered"
        ],
        "Wrong order": [
            "wrong", "incorrect", "mistake", "different"
        ],
        "Payment issues": [
            "payment", "charge", "refund", "money", "price", "cost"
        ],
    }

    # Map topics to canonical
    canonical_mapping = {}
    mapped_topics = set()

    for canonical, variations in consolidation_rules.items():
        matching_topics = [t for t in unique_topics if t in variations]
        if matching_topics:
            canonical_mapping[canonical] = matching_topics
            mapped_topics.update(matching_topics)

    # Add unmapped topics
    for topic in unique_topics:
        if topic not in mapped_topics:
            canonical_mapping[topic] = [topic]

    return canonical_mapping


def map_topics_to_canonical(topics_by_date: Dict[str, List[str]],
                           canonical_mapping: Dict[str, List[str]]) -> Dict[str, Dict[str, int]]:
    """
    Map extracted topics to canonical topics and count frequencies by date.
    Returns date -> canonical_topic -> count mapping.
    """
    # Build reverse mapping: variation -> canonical
    variation_to_canonical = {}
    for canonical, variations in canonical_mapping.items():
        for variation in variations:
            variation_to_canonical[variation.lower()] = canonical

    # Count topics by date
    result = {}
    for date_str in sorted(topics_by_date.keys()):
        result[date_str] = {}
        for topic in topics_by_date[date_str]:
            canonical = variation_to_canonical.get(topic.lower(), topic)
            result[date_str][canonical] = result[date_str].get(canonical, 0) + 1

    return result


def extract_app_id_from_link(link: str) -> str:
    """Extract app package ID from a Play Store link or return as-is if it's already a package ID."""
    if not link:
        return None

    link = link.strip()

    # Check if it's a Play Store URL
    if 'play.google.com' in link:
        # Extract package ID from URL like: https://play.google.com/store/apps/details?id=com.example.app
        if 'id=' in link:
            app_id = link.split('id=')[1].split('&')[0]
            return app_id

    # Otherwise assume it's already a package ID
    return link


def generate_trend_report(canonical_counts: Dict[str, Dict[str, int]],
                         target_date: datetime,
                         output_file: str) -> None:
    """Generate Excel trend report with Topic x Date matrix."""
    print(f"Generating trend report for {target_date.date()}...")

    # Ensure we have 30 days of data
    start_date = target_date - timedelta(days=29)
    date_range = [start_date + timedelta(days=i) for i in range(30)]
    date_strs = [d.strftime("%Y-%m-%d") for d in date_range]

    # Collect all topics
    all_topics = set()
    for date_str in date_strs:
        if date_str in canonical_counts:
            all_topics.update(canonical_counts[date_str].keys())

    all_topics = sorted(list(all_topics))

    # Create matrix
    data = []
    for topic in all_topics:
        row = [topic]
        for date_str in date_strs:
            count = canonical_counts.get(date_str, {}).get(topic, 0)
            row.append(count)
        data.append(row)

    # Create DataFrame
    columns = ["Topic"] + [d.strftime("%b %d") for d in date_range]
    df = pd.DataFrame(data, columns=columns)

    # Create Excel workbook with formatting
    wb = Workbook()
    ws = wb.active
    ws.title = "Trend Report"

    # Add headers
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    for col_idx, header in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Add data with alternating colors
    light_fill = PatternFill(start_color="E8EFF7", end_color="E8EFF7", fill_type="solid")
    for row_idx, row_data in enumerate(data, 2):
        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            if row_idx % 2 == 0:
                cell.fill = light_fill
            if col_idx > 1:
                cell.alignment = Alignment(horizontal="center")

    # Set column widths
    ws.column_dimensions['A'].width = 40
    col_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    for col_idx in range(1, len(columns)):
        if col_idx < len(col_letters):
            ws.column_dimensions[col_letters[col_idx]].width = 12

    # Save
    wb.save(output_file)
    print(f"✓ Report saved to {output_file}")


def main():
    """Main execution flow."""
    parser = argparse.ArgumentParser(description="App Store Review Trend Analysis")
    parser.add_argument("--target-date", type=str, default=None,
                       help="Target date (YYYY-MM-DD). Default: today")
    parser.add_argument("--days", type=int, default=30,
                       help="Number of days to analyze (default: 30)")
    parser.add_argument("--app-id", type=str, default=None,
                       help="App package ID or Play Store link")

    args = parser.parse_args()

    print("=" * 60)
    print("App Store Review Trend Analysis")
    print("=" * 60)

    # Prompt for app ID if not provided via command line
    if args.app_id:
        app_id = extract_app_id_from_link(args.app_id)
    else:
        while True:
            app_input = input("\nEnter app package ID (e.g., in.swiggy.android) or Play Store link,\nor press Enter for Swiggy: ").strip()

            if not app_input:
                app_id = SWIGGY_APP_ID
                print(f"Using default app: Swiggy ({app_id})")
                break
            else:
                app_id = extract_app_id_from_link(app_input)
                if app_id:
                    print(f"Using app: {app_id}")
                    break
                else:
                    print("Invalid input. Please provide a valid package ID or Play Store link.")

    # Prompt for target date if not provided via command line
    if args.target_date:
        target_date = datetime.strptime(args.target_date, "%Y-%m-%d")
    else:
        while True:
            try:
                date_input = input("\nEnter target date (YYYY-MM-DD) or press Enter for today: ").strip()

                if not date_input:
                    target_date = datetime.now()
                    print(f"Using today's date: {target_date.date()}")
                else:
                    target_date = datetime.strptime(date_input, "%Y-%m-%d")
                    print(f"Using target date: {target_date.date()}")
                break
            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD format.")

    # Calculate date range (30 days including target date)
    end_date = target_date
    start_date = target_date - timedelta(days=args.days - 1)

    print(f"Analysis Period: {start_date.date()} to {end_date.date()}")
    print()

    # Phase 1: Data Collection
    print("PHASE 1: Data Collection")
    print("-" * 40)
    reviews_by_date = scrape_reviews(app_id, start_date, end_date)
    print()

    # Phase 2: Topic Extraction
    print("PHASE 2: Topic Extraction")
    print("-" * 40)
    topics_by_date = extract_all_topics(reviews_by_date)
    print()

    # Phase 3: Topic Consolidation
    print("PHASE 3: Topic Consolidation")
    print("-" * 40)
    all_extracted_topics = []
    for topics in topics_by_date.values():
        all_extracted_topics.extend(topics)

    canonical_mapping = consolidate_topics(all_extracted_topics)
    print()

    # Phase 4: Generate Trend Matrix
    print("PHASE 4: Trend Analysis")
    print("-" * 40)
    canonical_counts = map_topics_to_canonical(topics_by_date, canonical_mapping)
    print()

    # Phase 5: Generate Report
    print("PHASE 5: Report Generation")
    print("-" * 40)
    # Extract app name from app_id (e.g., "in.swiggy.android" → "swiggy")
    app_name = app_id.split('.')[-2] if '.' in app_id else app_id
    output_file = OUTPUT_DIR / f"{app_name}_trend_report_{target_date.strftime('%Y-%m-%d')}.xlsx"
    generate_trend_report(canonical_counts, target_date, str(output_file))

    print()
    print("=" * 60)
    print("✓ Analysis Complete!")
    print("=" * 60)
    print(f"Output saved to: {output_file}")


if __name__ == "__main__":
    main()
