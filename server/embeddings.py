"""Embedding management and generation."""

import pickle
from typing import List, Optional
from abc import ABC, abstractmethod
import numpy as np
import os
from pathlib import Path


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


class DummyEmbeddingProvider(EmbeddingProvider):
    """Dummy embedding provider for development."""
    
    def __init__(self, dimension: int = 384):
        """
        Initialize dummy provider.
        
        Args:
            dimension: Embedding dimension
        """
        self.dimension = dimension
    
    def embed(self, text: str) -> np.ndarray:
        """Generate deterministic random embedding from text hash."""
        seed = abs(hash(text)) % (2**31)
        np.random.seed(seed)
        return np.random.randn(self.dimension).astype(np.float32)
    
    def get_name(self) -> str:
        """Return provider name."""
        return "dummy"


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """Embedding provider using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize SentenceTransformers provider.
        
        Args:
            model_name: Model name to use
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is required. Install it with: "
                "pip install sentence-transformers"
            )
        
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
    
    def embed(self, text: str) -> np.ndarray:
        """Generate embedding with SentenceTransformer."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float32)
    
    def get_name(self) -> str:
        """Return provider name."""
        return f"sentence-transformers-{self.model_name}"


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


class EmbeddingManager:
    """Manage embeddings for articles."""
    
    def __init__(self, provider: Optional[EmbeddingProvider] = None):
        """
        Initialize embedding manager.
        
        Args:
            provider: Embedding provider to use (default: Dummy)
        """
        self.provider = provider or DummyEmbeddingProvider()
    
    def embed_text(self, text: str) -> bytes:
        """
        Generate embedding for text and serialize.
        
        Args:
            text: Text to embed
            
        Returns:
            Serialized embedding in bytes
        """
        embedding = self.provider.embed(text)
        return pickle.dumps(embedding)
    
    def embed_article(self, article: dict) -> bytes:
        """
        Generate embedding for complete article.
        
        Uses full_content if available, otherwise combines title and description.
        
        Args:
            article: Dict with title, description, and optional full_content
            
        Returns:
            Serialized embedding in bytes
        """
        full_content = article.get("full_content")
        if full_content:
            text = full_content
        else:
            title = article.get("title", "")
            description = article.get("description", "")
            text = f"{title}\n{description}"
        
        return self.embed_text(text)
    
    def deserialize_embedding(self, embedding_bytes: bytes) -> np.ndarray:
        """
        Deserialize embedding from bytes.
        
        Args:
            embedding_bytes: Embedding in bytes format
            
        Returns:
            Embedding as numpy array
        """
        return pickle.loads(embedding_bytes)
    
    def get_provider_name(self) -> str:
        """Return embedding provider name."""
        return self.provider.get_name()
