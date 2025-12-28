"""
Sentiment Analyzer

Analyzes sentiment in app reviews using rating-based approach.
Optional ML feature controlled by ENABLE_SENTIMENT flag.

Performance:
- Rating-based analysis: ~0 seconds (instant)
- No API costs (uses existing review scores)
- Can be enhanced with embedding or LLM methods
"""

from typing import List, Dict, Optional
import re


class SentimentAnalyzer:
    """
    Analyze sentiment in reviews using rating-based approach
    Follows the same pattern as DuplicateDetector and TopicClusterer
    """

    # Rating to sentiment score mapping
    RATING_TO_SENTIMENT = {
        5: 1.0,   # Very positive
        4: 0.5,   # Positive
        3: 0.0,   # Neutral
        2: -0.5,  # Negative
        1: -1.0   # Very negative
    }

    # Keywords for confidence adjustment
    NEGATIVE_KEYWORDS = [
        'terrible', 'awful', 'worst', 'horrible', 'disgusting', 'pathetic',
        'useless', 'garbage', 'trash', 'hate', 'never', 'disappointed',
        'frustrating', 'annoying', 'broken', 'crashed', 'bug', 'issue',
        'problem', 'slow', 'late', 'cold', 'rude', 'poor', 'bad'
    ]

    POSITIVE_KEYWORDS = [
        'excellent', 'amazing', 'great', 'awesome', 'perfect', 'fantastic',
        'wonderful', 'love', 'best', 'good', 'fast', 'friendly', 'helpful',
        'delicious', 'fresh', 'quick', 'reliable', 'satisfied', 'happy'
    ]

    def __init__(self, method: str = 'rating'):
        """
        Initialize sentiment analyzer

        Args:
            method: Analysis method ('rating', 'embedding', 'llm')
                   Currently only 'rating' is implemented
        """
        if method not in ['rating', 'embedding', 'llm']:
            print(f"  Warning: Unsupported method '{method}', using 'rating' instead")
            self.method = 'rating'
        elif method != 'rating':
            print(f"  Warning: Method '{method}' not implemented, using 'rating' instead")
            self.method = 'rating'
        else:
            self.method = method

    def analyze_review_sentiment(self, review: Dict) -> Dict:
        """
        Analyze sentiment of a single review

        Args:
            review: Review dict with 'content' and 'score' fields

        Returns:
            {
                'score': float (-1.0 to 1.0),
                'label': str ('positive', 'negative', 'neutral'),
                'confidence': float (0.0 to 1.0),
                'method': str ('rating', 'embedding', 'llm')
            }
        """
        # Get rating score (1-5)
        rating = review.get('score', 3)

        if rating not in self.RATING_TO_SENTIMENT:
            # Handle invalid ratings
            rating = 3

        # Convert rating to sentiment score (-1 to 1)
        sentiment_score = self.RATING_TO_SENTIMENT[rating]

        # Analyze text content for confidence adjustment
        content = review.get('content', '').lower()
        confidence = self._calculate_confidence(content, sentiment_score)

        # Determine sentiment label
        if sentiment_score > 0.3:
            label = 'positive'
        elif sentiment_score < -0.3:
            label = 'negative'
        else:
            label = 'neutral'

        return {
            'score': sentiment_score,
            'label': label,
            'confidence': confidence,
            'method': self.method
        }

    def analyze_reviews_batch(self, reviews: List[Dict]) -> List[Dict]:
        """
        Analyze sentiment for a batch of reviews

        Args:
            reviews: List of review dicts

        Returns:
            List of sentiment dicts (same order as input)
        """
        return [self.analyze_review_sentiment(review) for review in reviews]

    def _calculate_confidence(self, content: str, sentiment_score: float) -> float:
        """
        Calculate confidence score based on text-sentiment alignment

        If rating is positive but text contains negative keywords, lower confidence.
        If rating matches text sentiment, higher confidence.

        Args:
            content: Review text (lowercase)
            sentiment_score: Sentiment score from rating

        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not content or len(content) < 5:
            # Short or missing content = lower confidence
            return 0.5

        # Count negative and positive keywords
        negative_count = sum(1 for keyword in self.NEGATIVE_KEYWORDS if keyword in content)
        positive_count = sum(1 for keyword in self.POSITIVE_KEYWORDS if keyword in content)

        # Check for text-sentiment alignment
        is_positive_rating = sentiment_score > 0.3
        is_negative_rating = sentiment_score < -0.3

        # High confidence if text matches rating
        if is_positive_rating and positive_count > negative_count:
            # Positive rating with positive text
            confidence = 0.9
        elif is_negative_rating and negative_count > positive_count:
            # Negative rating with negative text
            confidence = 0.9
        elif sentiment_score == 0.0:
            # Neutral rating
            confidence = 0.7
        elif is_positive_rating and negative_count > positive_count:
            # Positive rating with negative text (sarcasm or low-quality review)
            confidence = 0.4
        elif is_negative_rating and positive_count > negative_count:
            # Negative rating with positive text (unusual)
            confidence = 0.4
        else:
            # Mixed signals
            confidence = 0.6

        return confidence

    def get_sentiment_distribution(self, reviews: List[Dict]) -> Dict:
        """
        Get sentiment distribution statistics for a list of reviews

        Args:
            reviews: List of review dicts (must have 'sentiment' field)

        Returns:
            {
                'total': int,
                'positive': int,
                'negative': int,
                'neutral': int,
                'positive_pct': float,
                'negative_pct': float,
                'neutral_pct': float,
                'avg_sentiment': float
            }
        """
        total = len(reviews)

        if total == 0:
            return {
                'total': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'positive_pct': 0.0,
                'negative_pct': 0.0,
                'neutral_pct': 0.0,
                'avg_sentiment': 0.0
            }

        # Count by label
        positive = sum(1 for r in reviews if r.get('sentiment', {}).get('score', 0) > 0.3)
        negative = sum(1 for r in reviews if r.get('sentiment', {}).get('score', 0) < -0.3)
        neutral = total - positive - negative

        # Calculate average sentiment
        avg_sentiment = sum(r.get('sentiment', {}).get('score', 0) for r in reviews) / total

        return {
            'total': total,
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'positive_pct': (positive / total * 100) if total > 0 else 0.0,
            'negative_pct': (negative / total * 100) if total > 0 else 0.0,
            'neutral_pct': (neutral / total * 100) if total > 0 else 0.0,
            'avg_sentiment': avg_sentiment
        }
