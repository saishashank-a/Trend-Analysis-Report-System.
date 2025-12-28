#!/usr/bin/env python3
"""
Unit tests for sentiment analysis functionality
Tests the SentimentAnalyzer class and integration with the main pipeline
"""

import unittest
from utils.sentiment_analyzer import SentimentAnalyzer


class TestSentimentAnalyzer(unittest.TestCase):
    """Test cases for SentimentAnalyzer class"""

    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = SentimentAnalyzer(method='rating')

    def test_positive_sentiment(self):
        """Test positive sentiment detection"""
        review = {
            'content': 'Amazing app! Love the fast delivery!',
            'score': 5
        }
        result = self.analyzer.analyze_review_sentiment(review)

        self.assertEqual(result['score'], 1.0)
        self.assertEqual(result['label'], 'positive')
        self.assertGreater(result['confidence'], 0.8)

    def test_negative_sentiment(self):
        """Test negative sentiment detection"""
        review = {
            'content': 'Terrible service. Very disappointed.',
            'score': 1
        }
        result = self.analyzer.analyze_review_sentiment(review)

        self.assertEqual(result['score'], -1.0)
        self.assertEqual(result['label'], 'negative')
        self.assertGreater(result['confidence'], 0.8)

    def test_neutral_sentiment(self):
        """Test neutral sentiment detection"""
        review = {
            'content': 'Average service, nothing special',
            'score': 3
        }
        result = self.analyzer.analyze_review_sentiment(review)

        self.assertEqual(result['score'], 0.0)
        self.assertEqual(result['label'], 'neutral')

    def test_rating_to_sentiment_mapping(self):
        """Test all rating values map correctly"""
        ratings = {
            5: 1.0,
            4: 0.5,
            3: 0.0,
            2: -0.5,
            1: -1.0
        }

        for rating, expected_score in ratings.items():
            review = {'content': 'Test review', 'score': rating}
            result = self.analyzer.analyze_review_sentiment(review)
            self.assertEqual(result['score'], expected_score)

    def test_confidence_high_when_aligned(self):
        """Test high confidence when text matches rating"""
        # Positive rating with positive text
        review = {
            'content': 'Excellent service! Amazing experience!',
            'score': 5
        }
        result = self.analyzer.analyze_review_sentiment(review)
        self.assertGreater(result['confidence'], 0.8)

        # Negative rating with negative text
        review = {
            'content': 'Terrible awful bad service',
            'score': 1
        }
        result = self.analyzer.analyze_review_sentiment(review)
        self.assertGreater(result['confidence'], 0.8)

    def test_confidence_low_when_misaligned(self):
        """Test low confidence when text doesn't match rating"""
        # Positive rating with negative text (sarcasm or mistake)
        review = {
            'content': 'Terrible awful horrible service',
            'score': 5
        }
        result = self.analyzer.analyze_review_sentiment(review)
        self.assertLess(result['confidence'], 0.6)

    def test_batch_processing(self):
        """Test batch sentiment analysis"""
        reviews = [
            {'content': 'Great!', 'score': 5},
            {'content': 'Bad', 'score': 1},
            {'content': 'OK', 'score': 3}
        ]

        results = self.analyzer.analyze_reviews_batch(reviews)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['label'], 'positive')
        self.assertEqual(results[1]['label'], 'negative')
        self.assertEqual(results[2]['label'], 'neutral')

    def test_sentiment_distribution(self):
        """Test sentiment distribution calculation"""
        reviews = [
            {'content': 'Great!', 'score': 5, 'sentiment': {'score': 1.0}},
            {'content': 'Great!', 'score': 5, 'sentiment': {'score': 1.0}},
            {'content': 'Bad', 'score': 1, 'sentiment': {'score': -1.0}},
            {'content': 'OK', 'score': 3, 'sentiment': {'score': 0.0}}
        ]

        dist = self.analyzer.get_sentiment_distribution(reviews)

        self.assertEqual(dist['total'], 4)
        self.assertEqual(dist['positive'], 2)
        self.assertEqual(dist['negative'], 1)
        self.assertEqual(dist['neutral'], 1)
        self.assertEqual(dist['positive_pct'], 50.0)
        self.assertEqual(dist['avg_sentiment'], 0.25)

    def test_empty_content(self):
        """Test handling of empty content"""
        review = {'content': '', 'score': 5}
        result = self.analyzer.analyze_review_sentiment(review)

        # Should still work but with lower confidence
        self.assertEqual(result['score'], 1.0)
        self.assertLess(result['confidence'], 0.7)

    def test_missing_score(self):
        """Test handling of missing score"""
        review = {'content': 'Test review'}
        result = self.analyzer.analyze_review_sentiment(review)

        # Should default to neutral (score 3)
        self.assertEqual(result['score'], 0.0)
        self.assertEqual(result['label'], 'neutral')

    def test_invalid_rating(self):
        """Test handling of invalid rating"""
        review = {'content': 'Test', 'score': 10}
        result = self.analyzer.analyze_review_sentiment(review)

        # Should default to neutral
        self.assertEqual(result['score'], 0.0)

    def test_method_validation(self):
        """Test that only valid methods are accepted"""
        # Valid method should work
        analyzer = SentimentAnalyzer(method='rating')
        self.assertEqual(analyzer.method, 'rating')

        # Invalid method should warn and fallback to rating
        analyzer = SentimentAnalyzer(method='invalid')
        self.assertEqual(analyzer.method, 'rating')

    def test_sentiment_thresholds(self):
        """Test sentiment label thresholds"""
        # Test positive threshold (> 0.3)
        review = {'content': 'Good', 'score': 4}  # score = 0.5
        result = self.analyzer.analyze_review_sentiment(review)
        self.assertEqual(result['label'], 'positive')

        # Test negative threshold (< -0.3)
        review = {'content': 'Bad', 'score': 2}  # score = -0.5
        result = self.analyzer.analyze_review_sentiment(review)
        self.assertEqual(result['label'], 'negative')

        # Test neutral range (-0.3 to 0.3)
        review = {'content': 'OK', 'score': 3}  # score = 0.0
        result = self.analyzer.analyze_review_sentiment(review)
        self.assertEqual(result['label'], 'neutral')


class TestSentimentIntegration(unittest.TestCase):
    """Integration tests for sentiment analysis in main pipeline"""

    def test_review_sentiment_field(self):
        """Test that sentiment is added to review dict"""
        analyzer = SentimentAnalyzer()
        review = {'content': 'Test', 'score': 5}

        sentiment = analyzer.analyze_review_sentiment(review)
        review['sentiment'] = sentiment

        self.assertIn('sentiment', review)
        self.assertIn('score', review['sentiment'])
        self.assertIn('label', review['sentiment'])
        self.assertIn('confidence', review['sentiment'])
        self.assertIn('method', review['sentiment'])

    def test_sentiment_structure(self):
        """Test sentiment dict has correct structure"""
        analyzer = SentimentAnalyzer()
        review = {'content': 'Great app!', 'score': 5}

        sentiment = analyzer.analyze_review_sentiment(review)

        # Check all required fields exist
        required_fields = ['score', 'label', 'confidence', 'method']
        for field in required_fields:
            self.assertIn(field, sentiment)

        # Check types
        self.assertIsInstance(sentiment['score'], float)
        self.assertIsInstance(sentiment['label'], str)
        self.assertIsInstance(sentiment['confidence'], float)
        self.assertIsInstance(sentiment['method'], str)

        # Check value ranges
        self.assertGreaterEqual(sentiment['score'], -1.0)
        self.assertLessEqual(sentiment['score'], 1.0)
        self.assertGreaterEqual(sentiment['confidence'], 0.0)
        self.assertLessEqual(sentiment['confidence'], 1.0)
        self.assertIn(sentiment['label'], ['positive', 'negative', 'neutral'])


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
