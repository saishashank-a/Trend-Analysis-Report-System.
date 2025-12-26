"""
LLM Client Abstraction Layer
Supports multiple LLM providers: Ollama (local), Anthropic (cloud), Groq (cloud)
"""

import os
import json
import re
import requests
import asyncio
from enum import Enum
from typing import List, Dict, Any, Optional

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class LLMProvider(Enum):
    """Supported LLM providers"""
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    GROQ = "groq"


class BaseLLMClient:
    """Base class for LLM clients"""

    def chat(self, prompt: str, max_tokens: int = 500, temperature: float = 0.1) -> str:
        """Send a chat request and return the response text"""
        raise NotImplementedError

    def extract_json(self, response_text: str) -> dict:
        """Extract JSON from LLM response, handling markdown wrappers"""
        text = response_text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

        # Try direct JSON parsing
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback: Extract first {...} or [...]
            match = re.search(r'[\{\[].*[\}\]]', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass

            # Last resort: return error structure
            print(f"Warning: Failed to parse JSON from response: {text[:200]}...")
            raise ValueError(f"Could not parse JSON from response")


class OllamaClient(BaseLLMClient):
    """Ollama client for local LLM inference"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        extraction_model: str = "qwen2.5:32b",
        consolidation_model: str = "llama3.1:70b"
    ):
        self.base_url = base_url
        self.extraction_model = extraction_model
        self.consolidation_model = consolidation_model
        self.current_model = extraction_model

    def set_extraction_mode(self):
        """Switch to extraction model (fast, bulk processing)"""
        self.current_model = self.extraction_model

    def set_consolidation_mode(self):
        """Switch to consolidation model (high quality, single use)"""
        self.current_model = self.consolidation_model

    def chat(self, prompt: str, max_tokens: int = 500, temperature: float = 0.1) -> str:
        """Send request to Ollama API"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.current_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature
                    }
                },
                timeout=300  # 5 minute timeout for large models
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

            result = response.json()
            return result.get('response', '')

        except requests.exceptions.ConnectionError:
            raise Exception(
                "Could not connect to Ollama. Make sure Ollama is running:\n"
                "  1. Install from https://ollama.com/download\n"
                "  2. Open the Ollama app\n"
                "  3. Pull models: ollama pull qwen2.5:32b && ollama pull llama3.1:70b"
            )
        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}")

    def check_health(self) -> Dict[str, Any]:
        """Check if Ollama is running and models are available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return {
                    'status': 'error',
                    'message': 'Ollama server not responding'
                }

            data = response.json()
            models = data.get('models', [])
            model_names = [m['name'] for m in models]

            required_models = [self.extraction_model, self.consolidation_model]
            missing_models = [m for m in required_models if m not in model_names]

            if missing_models:
                return {
                    'status': 'warning',
                    'message': f'Missing models: {", ".join(missing_models)}',
                    'available_models': model_names,
                    'instructions': f'Run: ollama pull {" && ollama pull ".join(missing_models)}'
                }

            return {
                'status': 'ok',
                'message': 'Ollama is ready',
                'models': model_names,
                'extraction_model': self.extraction_model,
                'consolidation_model': self.consolidation_model
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Cannot reach Ollama: {str(e)}',
                'instructions': 'Make sure Ollama is installed and running'
            }


class AsyncOllamaClient(BaseLLMClient):
    """Async Ollama client for high-performance batch processing"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        extraction_model: str = "qwen2.5:32b",
        consolidation_model: str = "llama3.1:70b",
        max_connections: int = 20,
        enable_cache: bool = False
    ):
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx not installed. Run: pip install 'httpx[http2]'")

        self.base_url = base_url
        self.extraction_model = extraction_model
        self.consolidation_model = consolidation_model
        self.current_model = extraction_model
        self.max_connections = max_connections

        # Lazy initialization of async client
        self._client = None

        # Optional caching layer
        self.cache = None
        if enable_cache:
            try:
                from config.cache_db import LLMCache
                self.cache = LLMCache()
            except ImportError:
                print("Warning: cache_db not available, caching disabled")

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy initialization of async HTTP client"""
        if self._client is None:
            limits = httpx.Limits(
                max_connections=self.max_connections,
                max_keepalive_connections=self.max_connections
            )
            self._client = httpx.AsyncClient(
                limits=limits,
                timeout=httpx.Timeout(300.0),
                http2=True  # Enable HTTP/2 for better performance
            )
        return self._client

    def set_extraction_mode(self):
        """Switch to extraction model (fast, bulk processing)"""
        self.current_model = self.extraction_model

    def set_consolidation_mode(self):
        """Switch to consolidation model (high quality, single use)"""
        self.current_model = self.consolidation_model

    async def chat_async(self, prompt: str, max_tokens: int = 500, temperature: float = 0.1) -> str:
        """Async chat request to Ollama API"""

        # Check cache first
        if self.cache:
            cached = self.cache.get(prompt, self.current_model)
            if cached:
                return cached

        try:
            client = await self._get_client()

            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.current_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature
                    }
                }
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

            result = response.json()
            result_text = result.get('response', '')

            # Store in cache
            if self.cache:
                self.cache.set(prompt, self.current_model, result_text)

            return result_text

        except httpx.ConnectError:
            raise Exception(
                "Could not connect to Ollama. Make sure Ollama is running:\n"
                "  1. Install from https://ollama.com/download\n"
                "  2. Open the Ollama app\n"
                "  3. Pull models: ollama pull qwen2.5:32b && ollama pull llama3.1:70b"
            )
        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}")

    def chat(self, prompt: str, max_tokens: int = 500, temperature: float = 0.1) -> str:
        """Synchronous wrapper for backward compatibility"""
        return asyncio.run(self.chat_async(prompt, max_tokens, temperature))

    async def close(self):
        """Close the async client"""
        if self._client:
            await self._client.aclose()
            self._client = None


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude client (kept for backward compatibility)"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def chat(self, prompt: str, max_tokens: int = 500, temperature: float = 0.1) -> str:
        """Send request to Claude API"""
        response = self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text


class GroqClient(BaseLLMClient):
    """Groq client for fast cloud inference"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment")

        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            self.model = os.getenv('GROQ_MODEL', 'llama-3.1-70b-versatile')
        except ImportError:
            raise ImportError("groq package not installed. Run: pip install groq")

    def chat(self, prompt: str, max_tokens: int = 500, temperature: float = 0.1) -> str:
        """Send request to Groq API"""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content


def get_llm_client() -> BaseLLMClient:
    """
    Get LLM client based on environment variable

    Returns appropriate client based on LLM_PROVIDER env var:
    - ollama (default): Local Ollama instance
    - anthropic: Claude API
    - groq: Groq API
    """
    provider = os.getenv('LLM_PROVIDER', 'ollama').lower()

    if provider == 'ollama':
        return OllamaClient(
            base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
            extraction_model=os.getenv('OLLAMA_EXTRACTION_MODEL', 'qwen2.5:32b'),
            consolidation_model=os.getenv('OLLAMA_CONSOLIDATION_MODEL', 'llama3.1:70b')
        )

    elif provider == 'anthropic':
        return AnthropicClient()

    elif provider == 'groq':
        return GroqClient()

    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            f"Valid options: ollama, anthropic, groq"
        )


def check_llm_status() -> Dict[str, Any]:
    """Check the status of the configured LLM provider"""
    try:
        client = get_llm_client()

        # Only Ollama has health check currently
        if isinstance(client, OllamaClient):
            return client.check_health()
        else:
            return {
                'status': 'ok',
                'message': f'Using {type(client).__name__}',
                'provider': os.getenv('LLM_PROVIDER', 'ollama')
            }

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'provider': os.getenv('LLM_PROVIDER', 'ollama')
        }
