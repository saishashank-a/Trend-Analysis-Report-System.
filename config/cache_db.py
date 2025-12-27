"""
SQLite Database Layer for Caching and Job Persistence
Provides LLM response caching, embedding caching, and persistent job tracking
"""

import sqlite3
import json
import hashlib
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime


class LLMCache:
    """SQLite-based cache for LLM responses"""

    def __init__(self, cache_file: Path = None):
        if cache_file is None:
            cache_file = Path("cache/llm_cache.db")
        self.cache_file = cache_file
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.cache_file)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS llm_responses (
                prompt_hash TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                prompt TEXT NOT NULL,
                response TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hit_count INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_model ON llm_responses(model)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON llm_responses(created_at)")
        conn.commit()
        conn.close()

    def _hash_prompt(self, prompt: str, model: str) -> str:
        """Generate cache key from prompt + model"""
        key = f"{model}:{prompt}"
        return hashlib.sha256(key.encode()).hexdigest()

    def get(self, prompt: str, model: str) -> Optional[str]:
        """Retrieve cached response"""
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()

        prompt_hash = self._hash_prompt(prompt, model)
        cursor.execute(
            "SELECT response FROM llm_responses WHERE prompt_hash = ?",
            (prompt_hash,)
        )

        result = cursor.fetchone()

        if result:
            # Increment hit count
            cursor.execute(
                "UPDATE llm_responses SET hit_count = hit_count + 1 WHERE prompt_hash = ?",
                (prompt_hash,)
            )
            conn.commit()

        conn.close()
        return result[0] if result else None

    def set(self, prompt: str, model: str, response: str):
        """Store response in cache"""
        conn = sqlite3.connect(self.cache_file)
        prompt_hash = self._hash_prompt(prompt, model)

        conn.execute(
            """
            INSERT OR REPLACE INTO llm_responses (prompt_hash, model, prompt, response)
            VALUES (?, ?, ?, ?)
            """,
            (prompt_hash, model, prompt, response)
        )
        conn.commit()
        conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*), SUM(hit_count) FROM llm_responses")
        total_entries, total_hits = cursor.fetchone()

        cursor.execute("SELECT model, COUNT(*) FROM llm_responses GROUP BY model")
        by_model = dict(cursor.fetchall())

        conn.close()

        return {
            'total_entries': total_entries or 0,
            'total_hits': total_hits or 0,
            'by_model': by_model
        }

    def clear(self):
        """Clear all cached responses"""
        conn = sqlite3.connect(self.cache_file)
        conn.execute("DELETE FROM llm_responses")
        conn.commit()
        conn.close()


class JobDatabase:
    """SQLite database for persistent job tracking"""

    def __init__(self, db_file: Path = None):
        if db_file is None:
            db_file = Path("cache/jobs.db")
        self.db_file = db_file
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize jobs and chat_messages tables"""
        conn = sqlite3.connect(self.db_file)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                app_id TEXT NOT NULL,
                app_name TEXT,
                status TEXT NOT NULL,
                phase TEXT,
                progress_pct INTEGER DEFAULT 0,
                message TEXT,
                target_date DATE,
                days INTEGER,
                result_file TEXT,
                results_data TEXT,
                metrics TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                cancelled_at TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_app ON jobs(app_id)")

        # Chat messages table for persistent chat history
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_job ON chat_messages(job_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_messages(created_at)")

        conn.commit()
        conn.close()

    def create_job(self, job_data: dict) -> str:
        """Create new job record"""
        conn = sqlite3.connect(self.db_file)
        conn.execute("""
            INSERT INTO jobs (job_id, app_id, app_name, status, phase, message, target_date, days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_data['job_id'],
            job_data['app_id'],
            job_data.get('app_name'),
            job_data['status'],
            job_data['phase'],
            job_data['message'],
            job_data.get('target_date'),
            job_data.get('days')
        ))
        conn.commit()
        conn.close()
        return job_data['job_id']

    def update_job(self, job_id: str, updates: dict):
        """Update job progress"""
        if not updates:
            return

        # Build SET clause dynamically
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        query = f"UPDATE jobs SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE job_id = ?"

        conn = sqlite3.connect(self.db_file)
        conn.execute(query, list(updates.values()) + [job_id])
        conn.commit()
        conn.close()

    def get_job(self, job_id: str) -> Optional[dict]:
        """Get job by ID"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            job = dict(row)
            # Parse JSON fields
            if job.get('results_data'):
                try:
                    job['results_data'] = json.loads(job['results_data'])
                except (json.JSONDecodeError, TypeError):
                    pass
            if job.get('metrics'):
                try:
                    job['metrics'] = json.loads(job['metrics'])
                except (json.JSONDecodeError, TypeError):
                    pass
            return job
        return None

    def get_job_history(self, limit: int = 50, offset: int = 0, status: str = None) -> List[dict]:
        """Get recent jobs"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if status:
            cursor.execute("""
                SELECT job_id, app_id, app_name, status, phase, progress_pct,
                       created_at, completed_at, target_date, days
                FROM jobs
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (status, limit, offset))
        else:
            cursor.execute("""
                SELECT job_id, app_id, app_name, status, phase, progress_pct,
                       created_at, completed_at, target_date, days
                FROM jobs
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def cancel_job(self, job_id: str):
        """Mark job as cancelled"""
        conn = sqlite3.connect(self.db_file)
        conn.execute("""
            UPDATE jobs
            SET status = 'cancelled', cancelled_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE job_id = ? AND status IN ('started', 'running')
        """, (job_id,))
        conn.commit()
        conn.close()

    def delete_job(self, job_id: str):
        """Delete a job from database"""
        conn = sqlite3.connect(self.db_file)
        conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
        conn.commit()
        conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get job statistics"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cursor.fetchone()[0]

        cursor.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
        by_status = dict(cursor.fetchall())

        cursor.execute("""
            SELECT COUNT(*) FROM jobs
            WHERE status = 'completed' AND completed_at IS NOT NULL
        """)
        completed_jobs = cursor.fetchone()[0]

        conn.close()

        return {
            'total_jobs': total_jobs,
            'by_status': by_status,
            'completed_jobs': completed_jobs
        }

    def save_chat_message(self, job_id: str, role: str, content: str):
        """Save a chat message to database"""
        conn = sqlite3.connect(self.db_file)
        conn.execute("""
            INSERT INTO chat_messages (job_id, role, content)
            VALUES (?, ?, ?)
        """, (job_id, role, content))
        conn.commit()
        conn.close()

    def get_chat_history(self, job_id: str) -> List[dict]:
        """Get all chat messages for a job"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content, created_at
            FROM chat_messages
            WHERE job_id = ?
            ORDER BY created_at ASC
        """, (job_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def clear_chat_history(self, job_id: str):
        """Clear all chat messages for a job"""
        conn = sqlite3.connect(self.db_file)
        conn.execute("DELETE FROM chat_messages WHERE job_id = ?", (job_id,))
        conn.commit()
        conn.close()


class EmbeddingCache:
    """SQLite-based cache for semantic embeddings"""

    def __init__(self, cache_file: Path = None):
        if cache_file is None:
            cache_file = Path("cache/embedding_cache.db")
        self.cache_file = cache_file
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema for embeddings"""
        conn = sqlite3.connect(self.cache_file)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                text_hash TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                model TEXT NOT NULL,
                embedding BLOB NOT NULL,
                embedding_dim INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hit_count INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_embedding_model ON embeddings(model)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_embedding_created ON embeddings(created_at)")
        conn.commit()
        conn.close()

    def get_embedding(self, text_hash: str, app_id: str = None) -> Optional[np.ndarray]:
        """
        Retrieve cached embedding

        Args:
            text_hash: SHA256 hash of the text
            app_id: App package ID for app-specific caching (optional for backwards compatibility)

        Returns:
            numpy array of embedding or None if not cached
        """
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()

        # If app_id provided, include it in the lookup for app-specific caching
        if app_id:
            cache_key = f"{app_id}:{text_hash}"
            cursor.execute(
                "SELECT embedding, embedding_dim FROM embeddings WHERE text_hash = ?",
                (cache_key,)
            )
        else:
            # Fallback to old behavior for backwards compatibility
            cursor.execute(
                "SELECT embedding, embedding_dim FROM embeddings WHERE text_hash = ?",
                (text_hash,)
            )

        result = cursor.fetchone()

        if result:
            # Increment hit count
            if app_id:
                cache_key = f"{app_id}:{text_hash}"
                cursor.execute(
                    "UPDATE embeddings SET hit_count = hit_count + 1 WHERE text_hash = ?",
                    (cache_key,)
                )
            else:
                cursor.execute(
                    "UPDATE embeddings SET hit_count = hit_count + 1 WHERE text_hash = ?",
                    (text_hash,)
                )
            conn.commit()

            # Deserialize numpy array
            embedding_bytes, dim = result
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32).reshape(dim)
            conn.close()
            return embedding

        conn.close()
        return None

    def set_embedding(self, text_hash: str, text: str, model: str, embedding: np.ndarray, app_id: str = None):
        """
        Store embedding in cache

        Args:
            text_hash: SHA256 hash of the text
            text: Original text (for debugging)
            model: Model name used to generate embedding
            embedding: numpy array of the embedding
            app_id: App package ID for app-specific caching (optional for backwards compatibility)
        """
        conn = sqlite3.connect(self.cache_file)

        # Serialize numpy array to bytes
        embedding_bytes = embedding.astype(np.float32).tobytes()
        dim = embedding.shape[0]

        # If app_id provided, include it in cache key for app-specific caching
        if app_id:
            cache_key = f"{app_id}:{text_hash}"
        else:
            cache_key = text_hash

        conn.execute(
            """
            INSERT OR REPLACE INTO embeddings
            (text_hash, text, model, embedding, embedding_dim)
            VALUES (?, ?, ?, ?, ?)
            """,
            (cache_key, text, model, embedding_bytes, dim)
        )
        conn.commit()
        conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*), SUM(hit_count) FROM embeddings")
        total_entries, total_hits = cursor.fetchone()

        cursor.execute("SELECT model, COUNT(*) FROM embeddings GROUP BY model")
        by_model = dict(cursor.fetchall())

        conn.close()
        return {
            'total_entries': total_entries or 0,
            'total_hits': total_hits or 0,
            'by_model': by_model
        }

    def clear(self):
        """Clear all cached embeddings"""
        conn = sqlite3.connect(self.cache_file)
        conn.execute("DELETE FROM embeddings")
        conn.commit()
        conn.close()
