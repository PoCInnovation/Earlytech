import logging
import json
from typing import Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)

class EntityLLMProcessor:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = OpenAI()
        self.model = model
        self.system_prompt = (
            "You are an expert technical analysis system. Your task is to extract "
            "key entities from a given technical article text and return them in "
            "JSON format. Focus on high-level subjects, involved organizations, "
            "and the type of event the article describes."
        )

    def process(self, article: Dict, db_manager: Any) -> bool:
        article_id = article["id"]
        content = (
            f"Title: {article.get('title', '')}\n"
            f"Description: {article.get('description', '')}\n"
            f"Content: {article.get('full_content', '')[:500]}..."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": content}
                ],
                response_format={"type": "json_object"},
            )

            data = json.loads(response.choices[0].message.content)

            db_manager.assign_cluster_with_similarity(
                article_id=article_id,
                subject=data.get("subject", ""),
                orgs=data.get("organization_list", []),
                event=data.get("event_type", "")
            )
            return True

        except Exception as e:
            logger.error(f"Error for {article_id}: {e}")
            return False
