"""
Hardware Profile Detection and Optimization

Auto-detects hardware capabilities (CPU, RAM, GPU) and applies optimal
configuration for maximum performance.

Profiles:
- M4 Pro (24GB): 48 workers, Metal GPU, aggressive features
- M2/M3 (16GB): 24 workers, Metal GPU, balanced
- M1 (8GB): 8 workers, Metal GPU, memory-optimized
- Cloud CPU: 8 workers, CPU only, conservative
"""

import os
import torch
import multiprocessing
from typing import Dict, Any


def detect_hardware_profile() -> Dict[str, Any]:
    """
    Auto-detect hardware and return optimal configuration

    Returns:
        Hardware profile dict with optimal settings
    """
    # Detect Metal (Apple Silicon)
    has_metal = torch.backends.mps.is_available()

    # Detect CPU count
    cpu_count = multiprocessing.cpu_count()

    # Detect memory (approximate)
    try:
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024**3)
    except ImportError:
        # Fallback: estimate based on CPU count
        memory_gb = 16  # Conservative default

    # Determine profile based on hardware
    if has_metal and memory_gb >= 20 and cpu_count >= 10:
        profile_name = 'M4_PRO_24GB'
    elif has_metal and memory_gb >= 14 and cpu_count >= 8:
        profile_name = 'M2_16GB'
    elif has_metal and memory_gb >= 7:
        profile_name = 'M1_8GB'
    else:
        profile_name = 'CLOUD_CPU'

    return PROFILES[profile_name]


# Hardware profiles with optimal settings
PROFILES = {
    'M4_PRO_24GB': {
        'name': 'M4 Pro (24GB)',
        'max_concurrent': 48,
        'max_workers': 24,
        'batch_size': 30,
        'use_metal': True,
        'ollama_num_gpu_layers': 99,
        'ollama_num_thread': 12,
        'embedding_batch_size': 128,
        'enable_dedup': True,
        'enable_clustering': True,
        'enable_sentiment': True,  # Sentiment analysis enabled
        'duplicate_threshold': 0.85,
        'topic_similarity_threshold': 0.70
    },
    'M2_16GB': {
        'name': 'M2/M3 (16GB)',
        'max_concurrent': 24,
        'max_workers': 12,
        'batch_size': 20,
        'use_metal': True,
        'ollama_num_gpu_layers': 99,
        'ollama_num_thread': 8,
        'embedding_batch_size': 64,
        'enable_dedup': True,
        'enable_clustering': True,
        'enable_sentiment': True,
        'duplicate_threshold': 0.85,
        'topic_similarity_threshold': 0.70
    },
    'M1_8GB': {
        'name': 'M1 (8GB)',
        'max_concurrent': 8,
        'max_workers': 8,
        'batch_size': 15,
        'use_metal': True,
        'ollama_num_gpu_layers': 50,  # Partial offloading to save memory
        'ollama_num_thread': 4,
        'embedding_batch_size': 32,
        'enable_dedup': False,  # Save memory
        'enable_clustering': True,
        'enable_sentiment': True,
        'duplicate_threshold': 0.85,
        'topic_similarity_threshold': 0.70
    },
    'CLOUD_CPU': {
        'name': 'Cloud CPU',
        'max_concurrent': 8,
        'max_workers': 4,
        'batch_size': 10,
        'use_metal': False,
        'ollama_num_gpu_layers': 0,
        'ollama_num_thread': 4,
        'embedding_batch_size': 32,
        'enable_dedup': False,
        'enable_clustering': False,  # Fallback to LLM
        'enable_sentiment': True,
        'duplicate_threshold': 0.85,
        'topic_similarity_threshold': 0.70
    }
}


def apply_profile(profile_name: str = None) -> Dict[str, Any]:
    """
    Apply hardware profile to environment variables

    Args:
        profile_name: Name of profile to apply (None = auto-detect)

    Returns:
        Applied profile configuration
    """
    if profile_name is None:
        profile = detect_hardware_profile()
    else:
        profile = PROFILES.get(profile_name, PROFILES['CLOUD_CPU'])

    print(f"\n{'='*60}")
    print(f"Hardware Profile: {profile['name']}")
    print(f"{'='*60}")
    print(f"  Concurrency: {profile['max_concurrent']} workers")
    print(f"  Batch size: {profile['batch_size']} reviews/batch")
    print(f"  Metal GPU: {'Enabled' if profile['use_metal'] else 'Disabled'}")
    print(f"  Duplicate detection: {'Enabled' if profile['enable_dedup'] else 'Disabled'}")
    print(f"  Embedding clustering: {'Enabled' if profile['enable_clustering'] else 'Disabled'}")
    print(f"  Sentiment analysis: {'Enabled' if profile['enable_sentiment'] else 'Disabled'}")
    print(f"{'='*60}\n")

    # Update environment variables (only if not already set)
    env_mappings = {
        'MAX_CONCURRENT': profile['max_concurrent'],
        'MAX_WORKERS': profile['max_workers'],
        'BATCH_SIZE': profile['batch_size'],
        'OLLAMA_NUM_GPU_LAYERS': profile['ollama_num_gpu_layers'],
        'OLLAMA_NUM_THREAD': profile['ollama_num_thread'],
        'EMBEDDING_BATCH_SIZE': profile['embedding_batch_size'],
        'ENABLE_DEDUP': 'true' if profile['enable_dedup'] else 'false',
        'ENABLE_EMBEDDING_CLUSTERING': 'true' if profile['enable_clustering'] else 'false',
        'ENABLE_SENTIMENT': 'true' if profile['enable_sentiment'] else 'false',
        'DUPLICATE_THRESHOLD': profile['duplicate_threshold'],
        'TOPIC_SIMILARITY_THRESHOLD': profile['topic_similarity_threshold']
    }

    for key, value in env_mappings.items():
        # Only set if not already defined in environment
        if key not in os.environ:
            os.environ[key] = str(value)

    return profile


def get_config_value(key: str, default=None):
    """
    Get configuration value from environment with type conversion

    Args:
        key: Environment variable key
        default: Default value if not set

    Returns:
        Configuration value (converted to appropriate type)
    """
    value = os.getenv(key)

    if value is None:
        return default

    # Type conversion
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'

    try:
        # Try int first
        return int(value)
    except ValueError:
        try:
            # Then float
            return float(value)
        except ValueError:
            # Return as string
            return value
