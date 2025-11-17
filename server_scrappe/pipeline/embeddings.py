from typing import Optional, List
import os

try:
    # Try to import new openai client (v1.x+)
    from openai import OpenAI as OpenAIClient
    OPENAI_NEW = True
except Exception:
    OpenAIClient = None
    OPENAI_NEW = False

try:
    import openai as openai_legacy  # type: ignore
    OPENAI_LEGACY = True
except Exception:
    openai_legacy = None
    OPENAI_LEGACY = False


def _openai_embedding_new(text: str) -> Optional[List[float]]:
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        return None
    client = OpenAIClient(api_key=key)
    try:
        resp = client.embeddings.create(model="text-embedding-3-small", input=text)
        return resp.data[0].embedding
    except Exception:
        return None


def _openai_embedding_legacy(text: str) -> Optional[List[float]]:
    # legacy openai package (<=0.28)
    key = os.environ.get('OPENAI_API_KEY')
    if not key or not openai_legacy:
        return None
    try:
        openai_legacy.api_key = key
        resp = openai_legacy.Embedding.create(input=text, model="text-embedding-3-small")
        return resp["data"][0]["embedding"]
    except Exception:
        return None


def get_embedding(text: str) -> Optional[List[float]]:
    """Return embedding vector for given text using OpenAI (new or legacy client).

    Falls back to None if no provider configured.
    """
    # Prefer new client
    if OPENAI_NEW and OpenAIClient is not None:
        emb = _openai_embedding_new(text)
        if emb:
            return emb

    if OPENAI_LEGACY and openai_legacy is not None:
        emb = _openai_embedding_legacy(text)
        if emb:
            return emb

    # No provider available
    return None
