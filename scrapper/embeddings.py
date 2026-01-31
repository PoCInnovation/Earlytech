"""Embedding management and generation."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

import numpy as np
import os


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (numpy array)
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return provider name."""
        pass

    def get_dimension(self) -> Optional[int]:
        """Return embedding dimension when available."""
        return None


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Embedding provider using OpenAI API."""
    
    def __init__(self, model: str = "text-embedding-3-small", api_key: Optional[str] = None):
        """
        Initialize OpenAI embedding provider.
        
        Args:
            model: OpenAI embedding model to use (text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002)
            api_key: OpenAI API key (defaults to .env file or OPENAI_API_KEY env var)
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required. Install it with: "
                "pip install openai"
            )
        
        self.model = model
        self.dimension = self._infer_dimension(model)
        
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = self._load_api_key_from_env()
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Add OPENAI_API_KEY to .env file "
                "or set OPENAI_API_KEY environment variable."
            )
        
        self.client = OpenAI(api_key=self.api_key)
    
    def _load_api_key_from_env(self) -> Optional[str]:
        """Load API key from .env file or environment variable."""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return api_key
        
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('OPENAI_API_KEY='):
                        return line.split('=', 1)[1].strip().strip('"').strip("'")
        
        return None
    
    def embed(self, text: str) -> np.ndarray:
        """Generate embedding with OpenAI API."""
        max_chars = 30000
        if len(text) > max_chars:
            text = text[:max_chars]
        
        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        
        embedding = np.array(response.data[0].embedding, dtype=np.float32)
        return embedding
    
    def get_name(self) -> str:
        """Return provider name."""
        return f"openai-{self.model}"

    def get_dimension(self) -> Optional[int]:
        return self.dimension

    def _infer_dimension(self, model: str) -> Optional[int]:
        return {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }.get(model)


class EmbeddingManager:
    """Manage embeddings for articles."""
    
    def __init__(self, provider: EmbeddingProvider, expected_dimension: Optional[int] = None):
        """Initialize embedding manager.

        Args:
            provider: Embedding provider to use
            expected_dimension: Optional enforced dimension (aligns with DB vector size)
        """
        self.provider = provider
        self.expected_dimension = expected_dimension or self.provider.get_dimension()

    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for text."""
        embedding = self.provider.embed(text)
        embedding = embedding.astype(np.float32)
        self._validate_dimension(embedding)
        return embedding

    def embed_article(self, article: dict) -> np.ndarray:
        """Generate embedding for complete article."""
        full_content = article.get("full_content")
        if full_content:
            text = full_content
        else:
            title = article.get("title", "")
            description = article.get("description", "")
            text = f"{title}\n{description}"

        return self.embed_text(text)

    def deserialize_embedding(self, embedding_values: List[float]) -> np.ndarray:
        """Convert stored vector values back to numpy array."""
        embedding = np.array(embedding_values, dtype=np.float32)
        self._validate_dimension(embedding)
        return embedding

    def get_provider_name(self) -> str:
        """Return embedding provider name."""
        return self.provider.get_name()

    def _validate_dimension(self, embedding: np.ndarray):
        if self.expected_dimension and embedding.shape[0] != self.expected_dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.expected_dimension}, got {embedding.shape[0]}"
            )
