"""
Configuration for Brand Discovery Agent and Counterfeit Detection System
"""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI API Key for LLM
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your-api-key-here")

# Neo4j Connection Details
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")