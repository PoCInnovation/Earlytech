import logging
from typing import Dict, List, Any, Tuple
from sentence_transformers import CrossEncoder
import numpy as np

logger = logging.getLogger(__name__)


class CrossEncoderManager:
    """Manages cross-encoder for computing semantic relevance scores between articles."""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize the cross encoder.
        
        Args:
            model_name: HuggingFace model identifier for cross-encoder
                       Default: ms-marco-MiniLM-L-6-v2 (efficient and accurate for relevance)
        """
        self.model_name = model_name
        try:
            self.model = CrossEncoder(model_name)
            logger.info(f"Cross-encoder loaded: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load cross-encoder: {e}")
            self.model = None
    
    def compute_relevance_score(
        self,
        query_article: Dict[str, Any],
        candidate_article: Dict[str, Any]
    ) -> float:
        """
        Compute semantic relevance score between two articles.
        
        Args:
            query_article: Source article dict with title, description, full_content
            candidate_article: Target article dict for comparison
            
        Returns:
            Relevance score between 0 and 1
        """
        if self.model is None:
            logger.warning("Cross-encoder model not loaded, returning 0.5")
            return 0.5
        
        try:
            query_text = self._build_article_text(query_article)
            candidate_text = self._build_article_text(candidate_article)
            scores = self.model.predict([
                [query_text, candidate_text]
            ])
            relevance_score = self._sigmoid(scores[0])
            
            return float(relevance_score)
        
        except Exception as e:
            logger.error(f"Error computing relevance score: {e}")
            return 0.5
    
    def compute_batch_relevance_scores(
        self,
        query_article: Dict[str, Any],
        candidate_articles: List[Dict[str, Any]]
    ) -> List[float]:
        """
        Compute relevance scores between one query article and multiple candidates.
        
        Args:
            query_article: Source article
            candidate_articles: List of candidate articles
            
        Returns:
            List of relevance scores
        """
        if self.model is None or not candidate_articles:
            return [0.5] * len(candidate_articles)
        
        try:
            query_text = self._build_article_text(query_article)
            
            pairs = [
                [query_text, self._build_article_text(candidate)]
                for candidate in candidate_articles
            ]
            scores = self.model.predict(pairs)
            normalized_scores = [float(self._sigmoid(score)) for score in scores]
            
            return normalized_scores
        
        except Exception as e:
            logger.error(f"Error computing batch relevance scores: {e}")
            return [0.5] * len(candidate_articles)
    
    def _build_article_text(self, article: Dict[str, Any]) -> str:
        """
        Build a text representation of an article for cross-encoder.
        
        Args:
            article: Article dictionary
            
        Returns:
            Combined text of title and description
        """
        title = article.get("title", "").strip()
        description = article.get("description", "").strip()
        
        if title and description:
            return f"{title} {description}"
        elif title:
            return title
        elif description:
            return description
        else:
            return ""
    
    @staticmethod
    def _sigmoid(x: float) -> float:
        """Apply sigmoid function to normalize cross-encoder output."""
        import math
        try:
            return 1.0 / (1.0 + math.exp(-x))
        except OverflowError:
            return 0.0 if x < 0 else 1.0
