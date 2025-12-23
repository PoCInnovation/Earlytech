import logging
import json
from typing import Dict, Any, List
from openai import OpenAI, APIError

logger = logging.getLogger(__name__)

class EntityLLMProcessor:

    
    def __init__(self, model: str = "gpt-4o-mini"):

        self.client = OpenAI()
        self.model = model
        self.system_prompt = (
            "You are an expert technical analysis system. Your task is to extract "
            "key entities from a given technical article text and return them in "
            "JSON format. Focus on high-level subjects, involved organizations, "
            "and the type of event the article describes (e.g., Release, Rumor, Paper, Vulnerability)."
        )

        self.entity_schema = {
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "The main technical topic, e.g., 'LLMs', 'Kubernetes', 'Quantum Computing', 'Cybersecurity'."
                },
                "organization_list": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of key organizations or companies mentioned (e.g., Google, Microsoft, Meta)."
                },
                "event_type": {
                    "type": "string",
                    "description": "The type of event described: 'Release', 'Rumor', 'Acquisition', 'Vulnerability', 'Paper', 'Announcement', 'Fake', 'Update', 'Explainer'."
                },
            },
            "required": ["subject", "organization_list", "event_type"]
        }

    def process(self, article: Dict, db_manager: Any) -> bool:

        article_id = article["id"]
        
        content_for_llm = f"Title: {article.get('title', '')}\nDescription: {article.get('description', '')}\nContent snippet: {article.get('full_content', '')[:500]}..."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": content_for_llm}
                ],
                response_model=self.entity_schema,
                response_format={"type": "json_object"},
            )
            
            entity_data = json.loads(response.choices[0].message.content)
            
            db_manager.update_article_entities(
                article_id,
                subject=entity_data.get("subject"),
                organization_list=json.dumps(entity_data.get("organization_list", [])),
                event_type=entity_data.get("event_type"),
            )
            logger.debug(f"Entities successfully extracted and saved for {article_id}")
            return True
        
        except APIError as e:
            logger.error(f"OpenAI API Error for {article_id}: {e}")
        except json.JSONDecodeError:
            logger.error(f"LLM did not return valid JSON for {article_id}")
        except Exception as e:
            logger.error(f"General error during LLM processing for {article_id}: {e}")
            
        return False