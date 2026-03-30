"""
Keyword Matcher - Matches articles with user keywords using embedding similarity.

This module handles:
1. Computing embeddings for user keywords
2. Finding matching articles for keywords
3. Distributing articles to users
"""

import logging
import os
from typing import Dict, List, Optional, Any
import numpy as np

from database import DatabaseManager
from embeddings import EmbeddingManager

logger = logging.getLogger(__name__)


class KeywordMatcher:
    """Matches articles with user keywords using embeddings."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        embedding_manager: EmbeddingManager,
        similarity_threshold: float = 0.7,
        keyword_augmentation_model: Optional[str] = None,
        enable_llm_keyword_augmentation: Optional[bool] = None,
    ):
        """
        Initialize the keyword matcher.
        
        Args:
            db_manager: Database manager instance
            embedding_manager: Embedding manager instance
            similarity_threshold: Minimum similarity score (0-1) for matches
        """
        self.db_manager = db_manager
        self.embedding_manager = embedding_manager
        self.similarity_threshold = similarity_threshold
        self.keyword_augmentation_model = (
            keyword_augmentation_model
            or os.getenv("KEYWORD_AUGMENTATION_MODEL", "gpt-4o-mini")
        )
        if enable_llm_keyword_augmentation is None:
            env_value = os.getenv("KEYWORD_AUGMENTATION_USE_LLM", "true").strip().lower()
            self.enable_llm_keyword_augmentation = env_value in {"1", "true", "yes", "on"}
        else:
            self.enable_llm_keyword_augmentation = enable_llm_keyword_augmentation
        self._llm_client = None

    def augment_keyword_for_embedding(self, keyword: str) -> str:
        """Expand a short keyword into a natural sentence for embedding."""
        cleaned_keyword = keyword.strip()
        if not cleaned_keyword:
            return keyword

        if self.enable_llm_keyword_augmentation:
            llm_augmented = self._augment_keyword_with_llm(cleaned_keyword)
            if llm_augmented:
                return llm_augmented

        return (
            "This article discusses "
            f"{cleaned_keyword}, including practical use cases, recent news, "
            "technical details, and industry trends."
        )

    def _augment_keyword_with_llm(self, keyword: str) -> Optional[str]:
        """Generate an embedding-oriented expansion using a small GPT model."""
        try:
            if self._llm_client is None:
                from openai import OpenAI
                self._llm_client = OpenAI()

            response = self._llm_client.chat.completions.create(
                model=self.keyword_augmentation_model,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You rewrite search keywords into one concise sentence that is "
                            "optimized for semantic similarity with tech news or technical "
                            "articles. Keep the original keyword untouched inside the sentence. "
                            "Return only the sentence."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Keyword: "
                            f"{keyword}\n"
                            "Write one sentence (max 28 words) describing what an article "
                            "about this keyword would discuss (use cases, announcements, "
                            "methods, tooling, ecosystem)."
                        ),
                    },
                ],
            )

            content = (response.choices[0].message.content or "").strip()
            if not content:
                return None

            return " ".join(content.split())

        except Exception as e:
            logger.warning(
                "LLM keyword augmentation failed for '%s' (model=%s): %s. Falling back to template.",
                keyword,
                self.keyword_augmentation_model,
                e,
            )
            return None

    def setup_user_keywords(self, user_id: int, keywords: List[str]) -> Dict[int, str]:
        """
        Setup keywords for a user and compute their embeddings.
        
        Args:
            user_id: User ID
            keywords: List of keywords to add
            
        Returns:
            Dictionary mapping keyword_id to keyword text
        """
        keyword_map = {}
        
        for keyword in keywords:
            try:
                keyword_id = self.db_manager.add_user_keyword(user_id, keyword)

                embedding_input = self.augment_keyword_for_embedding(keyword)
                embedding = self.embedding_manager.embed_text(embedding_input)
                
                self.db_manager.store_keyword_embedding(
                    keyword_id=keyword_id,
                    user_id=user_id,
                    keyword=keyword,
                    embedding=embedding
                )
                
                keyword_map[keyword_id] = keyword
                logger.info(f"✓ Keyword '{keyword}' added for user {user_id} (ID: {keyword_id})")
                
            except Exception as e:
                logger.error(f"✗ Failed to add keyword '{keyword}': {e}")
        
        return keyword_map

    def match_article_with_keywords(self, article_id: str) -> List[Dict[str, Any]]:
        """
        Find all users who should receive an article based on keyword matching.
        
        Args:
            article_id: Article ID to match
            
        Returns:
            List of matching results with user info and similarity scores
        """
        try:
            # Get matching keywords for the article
            matches = self.db_manager.find_matching_keywords(
                article_id=article_id,
                similarity_threshold=self.similarity_threshold
            )
            
            if not matches:
                logger.debug(f"No keyword matches found for article {article_id}")
                return []
            
            logger.info(f"Found {len(matches)} keyword matches for article {article_id}")
            return matches
            
        except Exception as e:
            logger.error(f"Error matching article {article_id}: {e}")
            return []

    def dispatch_article_to_users(self, article_id: str) -> Dict[int, List[str]]:
        """
        Distribute an article to all matching users.
        
        This is the main workflow:
        1. Find all keywords matching the article
        2. Group matches by user (avoiding duplicate users)
        3. Record delivery with best matching keyword per user
        
        Args:
            article_id: Article ID to distribute
            
        Returns:
            Dictionary mapping user_id to list of matched keywords
        """
        matches = self.match_article_with_keywords(article_id)
        
        if not matches:
            return {}
        
        user_matches: Dict[int, Dict[str, Any]] = {}
        
        for match in matches:
            user_id = match["user_id"]
            
            if user_id not in user_matches or match["similarity_score"] > user_matches[user_id]["similarity_score"]:
                user_matches[user_id] = match
        
        delivery_summary = {}
        
        for user_id, match in user_matches.items():
            try:
                self.db_manager.record_article_delivery(
                    user_id=user_id,
                    article_id=article_id,
                    keyword_id=match["keyword_id"],
                    similarity_score=match["similarity_score"]
                )
                
                if user_id not in delivery_summary:
                    delivery_summary[user_id] = []
                
                delivery_summary[user_id].append(match["keyword"])
                
                logger.info(
                    f"✓ Article {article_id} delivered to user {user_id} ({match['name']}) "
                    f"via keyword '{match['keyword']}' (similarity: {match['similarity_score']:.3f})"
                )
                
            except Exception as e:
                logger.error(f"✗ Failed to deliver article {article_id} to user {user_id}: {e}")
        
        return delivery_summary

    def batch_dispatch_articles(self, article_ids: List[str]) -> Dict[str, Dict[int, List[str]]]:
        """
        Dispatch multiple articles to users.
        
        Args:
            article_ids: List of article IDs
            
        Returns:
            Dictionary mapping article_id to delivery summaries
        """
        results = {}
        
        for article_id in article_ids:
            results[article_id] = self.dispatch_article_to_users(article_id)
        
        return results

    def get_user_personalized_feed(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get personalized feed for a user (articles matched to their keywords).
        
        Args:
            user_id: User ID
            limit: Maximum articles to return
            
        Returns:
            List of articles with match information
        """
        return self.db_manager.get_user_articles(user_id, limit)

    def print_matching_summary(self, article_id: str) -> None:
        """Print a summary of keyword matches for an article."""
        matches = self.match_article_with_keywords(article_id)
        
        if not matches:
            print(f"No matches found for article {article_id}")
            return
        
        user_matches = {}
        for match in matches:
            user_id = match["user_id"]
            if user_id not in user_matches:
                user_matches[user_id] = {
                    "name": match["name"],
                    "keywords": []
                }
            user_matches[user_id]["keywords"].append({
                "keyword": match["keyword"],
                "score": match["similarity_score"]
            })
        
        print(f"\nKeyword Matches for Article {article_id}:")
        print("=" * 60)
        
        for user_id, user_info in user_matches.items():
            print(f"\n{user_info['username']} (User #{user_id}):")
            for kw_info in user_info["keywords"]:
                score_pct = kw_info["score"] * 100
                print(f"   - '{kw_info['keyword']}' → {score_pct:.1f}%")
