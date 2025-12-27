"""
Embedding Service with Metal GPU Acceleration

Provides semantic embedding generation using sentence-transformers with
Metal Performance Shaders (MPS) backend for Apple Silicon optimization.

Performance on M4 Pro:
- ~200 embeddings/second with Metal GPU
- ~50 embeddings/second with CPU fallback
"""

import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Optional
import hashlib


class EmbeddingService:
    """
    Semantic embedding service with Metal GPU acceleration
    Uses sentence-transformers with MPS (Metal Performance Shaders) backend
    """

    def __init__(self, model_name='all-MiniLM-L6-v2', use_metal=True, cache=None, app_id=None):
        """
        Initialize embedding service

        Args:
            model_name: Sentence-transformers model (default: all-MiniLM-L6-v2)
            use_metal: Enable Metal GPU acceleration if available
            cache: EmbeddingCache instance for persistent caching
            app_id: App package ID for app-specific caching (optional)
        """
        # Initialize device (Metal GPU or CPU)
        if use_metal and torch.backends.mps.is_available():
            self.device = torch.device("mps")
            print("✓ Using Metal GPU acceleration for embeddings")
        else:
            self.device = torch.device("cpu")
            print("⚠ Using CPU for embeddings (Metal not available)")

        # Load model
        self.model = SentenceTransformer(model_name, device=str(self.device))
        self.model_name = model_name
        self.cache = cache  # EmbeddingCache instance
        self.app_id = app_id  # App-specific caching

    def encode(self, texts: List[str], batch_size=128, show_progress=False) -> np.ndarray:
        """
        Encode texts to embeddings with batching and caching

        Args:
            texts: List of strings to embed
            batch_size: Batch size for encoding (default: 128)
            show_progress: Show progress bar during encoding

        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        # Filter empty texts
        valid_texts = [t for t in texts if t and len(t.strip()) > 0]
        if not valid_texts:
            return np.array([])

        # Check cache first
        if self.cache:
            cached_embeddings = []
            uncached_indices = []
            uncached_texts = []

            for idx, text in enumerate(valid_texts):
                text_hash = self._hash_text(text)
                cached = self.cache.get_embedding(text_hash, app_id=self.app_id)
                if cached is not None:
                    cached_embeddings.append((idx, cached))
                else:
                    uncached_indices.append(idx)
                    uncached_texts.append(text)

            # Generate embeddings for uncached texts
            if uncached_texts:
                new_embeddings = self.model.encode(
                    uncached_texts,
                    batch_size=batch_size,
                    show_progress_bar=show_progress,
                    convert_to_numpy=True
                )

                # Store in cache with app_id
                for text, embedding in zip(uncached_texts, new_embeddings):
                    text_hash = self._hash_text(text)
                    self.cache.set_embedding(text_hash, text, self.model_name, embedding, app_id=self.app_id)
            else:
                new_embeddings = np.array([])

            # Combine cached and new embeddings
            all_embeddings = np.zeros((len(valid_texts), self.model.get_sentence_embedding_dimension()))
            for idx, emb in cached_embeddings:
                all_embeddings[idx] = emb
            for uncached_idx, embedding in zip(uncached_indices, new_embeddings):
                all_embeddings[uncached_idx] = embedding

            if cached_embeddings:
                cache_hit_rate = len(cached_embeddings) / len(valid_texts) * 100
                print(f"  Cache hit rate: {cache_hit_rate:.1f}% ({len(cached_embeddings)}/{len(valid_texts)})")

            return all_embeddings
        else:
            # No cache - direct encoding
            return self.model.encode(
                valid_texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )

    def encode_single(self, text: str) -> np.ndarray:
        """
        Encode single text to embedding

        Args:
            text: Single string to embed

        Returns:
            numpy array of shape (embedding_dim,)
        """
        return self.encode([text])[0]

    def cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings

        Args:
            emb1: First embedding vector
            emb2: Second embedding vector

        Returns:
            Similarity score between -1 and 1
        """
        from sklearn.metrics.pairwise import cosine_similarity as cos_sim
        return float(cos_sim([emb1], [emb2])[0][0])

    def batch_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Compute pairwise cosine similarity matrix

        Args:
            embeddings: numpy array of shape (n_samples, embedding_dim)

        Returns:
            Similarity matrix of shape (n_samples, n_samples)
        """
        from sklearn.metrics.pairwise import cosine_similarity
        return cosine_similarity(embeddings)

    def _hash_text(self, text: str) -> str:
        """Generate SHA256 hash for caching"""
        return hashlib.sha256(text.encode()).hexdigest()
