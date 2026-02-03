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
            "JSON format.\n\n"
            "CRITICAL: Distinguish between PRIMARY and SECONDARY sources:\n"
            "- PRIMARY: Information that originates DIRECTLY from the source (e.g., official announcement, "
            "company blog, official paper, GitHub repo by the organization itself)\n"
            "- SECONDARY: Information that is REPORTED BY A THIRD PARTY (e.g., news article, analysis, "
            "commentary about someone else's work)\n\n"
            "Extract and categorize entities as follows:\n"
            "1. For SUBJECTS/TOPICS:\n"
            "   - primary_subject: The main subject directly communicated by the source organization\n"
            "   - secondary_subject: Subjects mentioned but not the primary focus of communication\n\n"
            "2. For ORGANIZATIONS:\n"
            "   - primary_organizations: Organizations that are the SOURCE/AUTHOR of the information\n"
            "   - secondary_organizations: Organizations mentioned/discussed but not the source\n\n"
            "3. For EVENT TYPES:\n"
            "   - primary_event_type: The main event being announced/reported by the source\n"
            "   - secondary_event_type: Related events or context mentioned secondarily\n\n"
            "EXAMPLES:\n"
            "- If article is 'Google announces new Gemini model': primary_org=['Google']\n"
            "- If article is 'Le Monde reports on Google\\'s new model': primary_org=['Le Monde'] as reporter, "
            "secondary_org=['Google'] as subject\n\n"
            "Return results in JSON format with clear separation between primary and secondary entities."
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

            # Extract primary and secondary entities
            primary_subject = data.get("primary_subject", "")
            secondary_subject = data.get("secondary_subject", "")
            
            primary_orgs = data.get("primary_organizations", [])
            secondary_orgs = data.get("secondary_organizations", [])
            
            primary_event = data.get("primary_event_type", "")
            secondary_event = data.get("secondary_event_type", "")

            db_manager.assign_cluster_with_similarity(
                article_id=article_id,
                primary_subject=primary_subject,
                secondary_subject=secondary_subject,
                primary_orgs=primary_orgs,
                secondary_orgs=secondary_orgs,
                primary_event=primary_event,
                secondary_event=secondary_event,
                article_data=article  # Pass full article for cross-encoder
            )
            return True

        except Exception as e:
            logger.error(f"Error for {article_id}: {e}")
            return False
