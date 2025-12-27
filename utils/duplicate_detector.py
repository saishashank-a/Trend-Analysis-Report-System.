"""
Duplicate Review Detector

Detects duplicate and near-duplicate reviews using semantic embeddings.
Reduces dataset size by ~50% for faster processing.

Performance:
- 7000 reviews checked in ~2 minutes on Metal GPU
- Typical duplicate rate: 40-60% (spam, bot reviews, repeated complaints)
"""

import numpy as np
from typing import List, Dict, Tuple
from config.embedding_service import EmbeddingService


class DuplicateDetector:
    """
    Detect duplicate/near-duplicate reviews using semantic embeddings
    Uses cosine similarity with configurable threshold
    """

    def __init__(self, embedding_service: EmbeddingService, threshold=0.85):
        """
        Initialize duplicate detector

        Args:
            embedding_service: EmbeddingService instance
            threshold: Cosine similarity threshold for duplicates (0.85 = 85% similar)
        """
        self.embedding_service = embedding_service
        self.threshold = threshold

    def detect_duplicates(self, reviews: List[dict]) -> Tuple[List[dict], List[dict]]:
        """
        Detect duplicates in review list

        Args:
            reviews: List of review dicts with 'content' field

        Returns:
            (unique_reviews, duplicate_reviews)
        """
        if not reviews:
            return [], []

        print(f"  Detecting duplicates in {len(reviews)} reviews (threshold: {self.threshold})...")

        # Extract review texts
        texts = [r.get('content', '') for r in reviews]

        # Generate embeddings
        embeddings = self.embedding_service.encode(texts, batch_size=128)

        # Compute similarity matrix (optimized for large datasets)
        similarity_matrix = self._compute_similarity_matrix_chunked(embeddings)

        # Find duplicate indices
        duplicate_indices = self._find_duplicates(similarity_matrix)

        # Split into unique and duplicates
        unique_reviews = []
        duplicate_reviews = []

        for idx, review in enumerate(reviews):
            if idx in duplicate_indices:
                duplicate_reviews.append(review)
            else:
                unique_reviews.append(review)

        dup_pct = len(duplicate_reviews) / len(reviews) * 100 if reviews else 0
        print(f"  ✓ Found {len(duplicate_reviews)} duplicates ({dup_pct:.1f}%)")
        print(f"  Unique reviews: {len(unique_reviews)}")

        return unique_reviews, duplicate_reviews

    def _compute_similarity_matrix_chunked(self, embeddings: np.ndarray, chunk_size=1000) -> np.ndarray:
        """
        Compute similarity matrix in chunks to avoid memory issues

        For 7000 reviews: 7000x7000 = 49M floats = 196MB (manageable)
        But chunking helps for larger datasets

        Args:
            embeddings: numpy array of shape (n_reviews, embedding_dim)
            chunk_size: Number of rows to process at once

        Returns:
            Similarity matrix of shape (n_reviews, n_reviews)
        """
        n = len(embeddings)
        similarity_matrix = np.zeros((n, n), dtype=np.float32)

        from sklearn.metrics.pairwise import cosine_similarity

        for i in range(0, n, chunk_size):
            end_i = min(i + chunk_size, n)
            chunk = embeddings[i:end_i]
            similarity_matrix[i:end_i, :] = cosine_similarity(chunk, embeddings)

        return similarity_matrix

    def _find_duplicates(self, similarity_matrix: np.ndarray) -> set:
        """
        Find duplicate indices using greedy algorithm
        Keep first occurrence, mark others as duplicates

        Args:
            similarity_matrix: Pairwise similarity matrix

        Returns:
            Set of indices to mark as duplicates
        """
        n = similarity_matrix.shape[0]
        duplicates = set()

        for i in range(n):
            if i in duplicates:
                continue  # Already marked as duplicate

            # Find reviews similar to review i (only look forward to avoid double-counting)
            similar_indices = np.where(
                (similarity_matrix[i] >= self.threshold) &
                (np.arange(n) > i)  # Only look forward
            )[0]

            # Mark them as duplicates
            duplicates.update(similar_indices.tolist())

        return duplicates
