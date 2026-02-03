"""
Examples demonstrating the new primary/secondary entity extraction and cross-encoder usage.
"""

import os
import json
from typing import Dict, List

from cross_encoder import CrossEncoderManager
from entity_llm_processor import EntityLLMProcessor
from database import DatabaseManager


def example_cross_encoder_relevance():
    """
    Example: Using Cross Encoder to compute semantic relevance between articles.
    
    The cross encoder is more efficient than computing embeddings for many pairs
    and provides direct relevance scores optimized for ranking/clustering tasks.
    """
    print("\n" + "="*60)
    print("EXAMPLE: Cross-Encoder Relevance Scoring")
    print("="*60)
    
    # Initialize cross encoder
    ce_manager = CrossEncoderManager()
    
    # Sample articles
    article1 = {
        "id": "arxiv_001",
        "title": "Efficient Transformer Architectures with Flash Attention",
        "description": "New optimization techniques for transformer models",
        "full_content": "This paper presents Flash Attention, an I/O-aware attention mechanism..."
    }
    
    article2 = {
        "id": "github_001",
        "title": "OpenAI Releases GPT-4 Turbo Model",
        "description": "Announcement of new capabilities in GPT-4 Turbo",
        "full_content": "OpenAI has released GPT-4 Turbo with improved performance..."
    }
    
    article3 = {
        "id": "arxiv_002",
        "title": "Attention Mechanisms and Transformer Optimization",
        "description": "Survey of efficiency improvements in attention",
        "full_content": "This comprehensive survey covers attention optimization techniques..."
    }
    
    # Compute relevance scores
    print("\nComputing relevance scores:")
    print(f"\n1. Article1 vs Article2 (different topics):")
    score_1_2 = ce_manager.compute_relevance_score(article1, article2)
    print(f"   Relevance: {score_1_2:.3f}")
    
    print(f"\n2. Article1 vs Article3 (similar topics - attention/transformers):")
    score_1_3 = ce_manager.compute_relevance_score(article1, article3)
    print(f"   Relevance: {score_1_3:.3f}")
    
    print("\n✓ Article1 and Article3 should have higher relevance (same topic)")
    print(f"  Difference: {score_1_3 - score_1_2:.3f}")


def example_primary_secondary_extraction():
    """
    Example: Using enhanced LLM processor with primary/secondary entity extraction.
    
    The new system distinguishes between:
    - PRIMARY entities: Central focus of the article
    - SECONDARY entities: Supporting or contextual information
    
    This allows more nuanced clustering and relevance matching.
    """
    print("\n" + "="*60)
    print("EXAMPLE: Primary/Secondary Entity Extraction")
    print("="*60)
    
    processor = EntityLLMProcessor(model="gpt-4o-mini")
    
    # Example article
    article = {
        "id": "arxiv_123",
        "title": "OpenAI Releases GPT-4 with Multimodal Capabilities",
        "description": "OpenAI announces GPT-4, a new multimodal AI model with vision understanding",
        "full_content": (
            "OpenAI has released GPT-4, their most advanced model to date. "
            "GPT-4 can process both text and images, setting a new standard for AI capabilities. "
            "The model was trained using RLHF with input from domain experts. "
            "Anthropic's Claude model also supports multimodal inputs, showing industry convergence."
        )
    }
    
    print(f"\nProcessing article: {article['title']}")
    print("\nExpected extraction:")
    print("  PRIMARY subject: 'Large Language Models' or 'GPT-4'")
    print("  SECONDARY subject: 'Multimodal AI' or 'Vision Understanding'")
    print("  PRIMARY organizations: ['OpenAI']")
    print("  SECONDARY organizations: ['Anthropic']")
    print("  PRIMARY event: 'Model Release'")
    print("  SECONDARY event: 'Industry Convergence'")
    
    print("\nNote: In production, this would be called on actual article processing")
    print("      and would integrate with the database clustering system.")


def example_clustering_with_primary_secondary():
    """
    Example: How primary/secondary entities improve clustering.
    
    The clustering algorithm now considers:
    1. Embedding similarity (from vector database) - 30% weight
    2. Cross-encoder relevance score - 30% weight
    3. Entity matching with primary/secondary distinction - 40% weight
    
    This creates more meaningful clusters with better article grouping.
    """
    print("\n" + "="*60)
    print("EXAMPLE: Clustering with Primary/Secondary Entities")
    print("="*60)
    
    print("\nClustering Flow:")
    print("1. Article enters the system")
    print("2. LLM extracts PRIMARY and SECONDARY entities")
    print("3. Embedding is computed via text-embedding-3-small")
    print("4. Candidate articles are fetched (vector similarity)")
    print("5. For each candidate:")
    print("   a) Embedding similarity: cosine distance (30%)")
    print("   b) Cross-encoder score: semantic relevance (30%)")
    print("   c) Entity matching: primary > secondary (40%)")
    print("6. Best matching cluster is selected")
    print("7. If no good match: create new cluster")
    
    print("\nEntity Matching Weights:")
    print("  PRIMARY subject match        : +1.0")
    print("  SECONDARY subject match      : +0.3")
    print("  PRIMARY event match          : +0.5")
    print("  SECONDARY event match        : +0.2")
    print("  PRIMARY organizations match  : +0.3 per org")
    print("  SECONDARY organizations match: +0.1 per org")
    
    print("\n✓ Primary entities weighted higher = more focused clustering")


def example_database_schema():
    """
    Show the updated database schema with primary/secondary support.
    """
    print("\n" + "="*60)
    print("DATABASE SCHEMA - Articles Table")
    print("="*60)
    
    schema = {
        "articles": {
            "columns": {
                "id": "TEXT PRIMARY KEY",
                "source_site": "TEXT",
                "title": "TEXT",
                "description": "TEXT",
                "full_content": "TEXT",
                "primary_subject": "TEXT [NEW]",
                "secondary_subject": "TEXT [NEW]",
                "primary_organizations": "JSONB [NEW] (array of strings)",
                "secondary_organizations": "JSONB [NEW] (array of strings)",
                "primary_event_type": "TEXT [NEW]",
                "secondary_event_type": "TEXT [NEW]",
                "cluster_id": "INTEGER",
                "created_at": "TIMESTAMPTZ",
                "updated_at": "TIMESTAMPTZ",
            }
        }
    }
    
    print("\nNew columns for entity extraction:")
    for col in ["primary_subject", "secondary_subject", "primary_organizations", 
                "secondary_organizations", "primary_event_type", "secondary_event_type"]:
        print(f"  ✓ {col}")
    
    print("\n✓ Old columns removed: subject, organization_list, event_type")


def example_llm_prompt():
    """
    Show the new LLM system prompt for entity extraction.
    """
    print("\n" + "="*60)
    print("LLM SYSTEM PROMPT - Enhanced with Primary/Secondary")
    print("="*60)
    
    prompt = """You are an expert technical analysis system. Your task is to extract 
key entities from a given technical article text and return them in JSON format.

Extract and categorize entities as follows:
1. PRIMARY entities: Main subjects/topics that are the central focus of the article
2. SECONDARY entities: Supporting topics, related subjects, or contextual information

For organizations and event types, also use primary/secondary classification:
- PRIMARY organizations: Directly involved or central to the article
- SECONDARY organizations: Mentioned but peripheral to the main narrative
- PRIMARY event type: The main event/announcement being discussed
- SECONDARY event types: Related or background events

Return results in JSON format with clear separation between primary and secondary entities."""
    
    print(prompt)
    
    print("\n\nExpected JSON output structure:")
    expected_output = {
        "primary_subject": "Main topic of the article",
        "secondary_subject": "Supporting or related topic",
        "primary_organizations": ["Org1", "Org2"],
        "secondary_organizations": ["Org3"],
        "primary_event_type": "Main event (e.g., 'Model Release', 'Acquisition')",
        "secondary_event_type": "Related event or context"
    }
    print(json.dumps(expected_output, indent=2))


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("TECHNICAL WATCH SERVER - NEW FEATURES EXAMPLES")
    print("="*60)
    
    # Note: Uncomment to run examples that require API keys
    # example_cross_encoder_relevance()
    # example_primary_secondary_extraction()
    
    example_clustering_with_primary_secondary()
    example_database_schema()
    example_llm_prompt()
    
    print("\n" + "="*60)
    print("For production usage, check main.py watch/backfill modes")
    print("="*60)


if __name__ == "__main__":
    main()
