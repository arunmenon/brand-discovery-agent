# brand_graph_crew.py

import os
import re
import json
import requests
from typing import Any, Dict, List
from bs4 import BeautifulSoup
from neo4j import GraphDatabase
from crewai import Agent, Task, Crew, Process, LLM
from crewai.project import CrewBase, agent, task, crew, before_kickoff, after_kickoff

# ------------------------------------------------------------
# Global configuration and tool initialization
# ------------------------------------------------------------

# Ensure API keys are set in your environment (or replace with your keys)
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "<YOUR_OPENAI_API_KEY>")
os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY", "<YOUR_SERPER_API_KEY>")

# Neo4j connection parameters
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

# ------------------------------------------------------------
# Crew: BrandGraphCrew
# ------------------------------------------------------------
@CrewBase
class BrandGraphCrew:
    """
    A multi-step Crew that builds/updates a Brand Knowledge Graph in Neo4j.
    
    It supports two modes:
      - Category Mode: Given a category and product type, it discovers brands, extracts attributes,
        generates name variations, and upserts all data into Neo4j.
      - Brand Mode: Given a brand, it directly extracts any new attributes/variations and updates the graph.
    
    Expected input JSON:
      For Category Mode:
        {
          "mode": "category",
          "category": "Footwear",
          "product_type": "Running Shoes"
        }
      For Brand Mode:
        {
          "mode": "brand",
          "brand": "Nike",
          "category": "Footwear",      # optional if known
          "product_type": "Running Shoes"  # optional if known
        }
    """
    
    def __init__(self, llm_model="openai/gpt-4", neo4j_uri=NEO4J_URI, neo4j_user=NEO4J_USER, neo4j_pass=NEO4J_PASSWORD):
        self.llm = LLM(model=llm_model, temperature=0.2, verbose=False)
        self.inputs: Dict[str, Any] = {}
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
    
    @before_kickoff
    def capture_inputs(self, inputs: Dict[str, Any]):
        """
        Capture the pipeline inputs.
        """
        self.inputs = inputs
        return inputs

    # ------------------------------------------------------------
    # Agent Definitions
    # ------------------------------------------------------------
    @agent
    def brand_discovery_agent(self) -> Agent:
        """
        Agent to discover brand names given a category and product type.
        (For demonstration, this agent uses an LLM prompt. In production, integrate a search tool.)
        """
        return Agent(
            role="Brand Discovery",
            goal=(
                "Given the category '{category}' and product type '{product_type}', "
                "search online for relevant brand names and list one brand per line. "
                "Return strictly a JSON array (no extra text)."
            ),
            backstory="An expert researcher in identifying brands from various online sources.",
            llm=self.llm,
            memory=False,
            verbose=True,
            cache=False
        )

    @agent
    def attribute_extraction_agent(self) -> Agent:
        """
        Agent to extract product-specific attributes for a given brand.
        """
        return Agent(
            role="Attribute Extractor",
            goal=(
                "For the brand '{brand}' and product type '{product_type}', extract product-specific attributes "
                "and possible values. Return strictly JSON in the format: "
                "{\"Color\": [\"Red\", \"Blue\"], \"Size\": [\"8\", \"9\", \"10\"]}."
            ),
            backstory="Skilled at scraping and summarizing product details from online sources.",
            llm=self.llm,
            memory=False,
            verbose=True,
            cache=False
        )

    @agent
    def brand_variation_agent(self) -> Agent:
        """
        Agent to generate name variations or potential counterfeit aliases for a given brand.
        """
        return Agent(
            role="Brand Variation Generator",
            goal=(
                "Generate a list of alternative names, misspellings, or knock-off variations for the brand '{brand}'. "
                "Return strictly as a JSON array (e.g., [\"BrandX\", \"Br4ndX\"])."
            ),
            backstory="Expert at detecting subtle variations that might represent counterfeit or alias names.",
            llm=self.llm,
            memory=False,
            verbose=True,
            cache=False
        )

    # ------------------------------------------------------------
    # Task Definitions
    # ------------------------------------------------------------
    @task
    def brand_discovery_task(self) -> Task:
        description = r"""
Given:
  Category: {category}
  Product Type: {product_type}

**INSTRUCTIONS**:
Search online for brand names relevant to these inputs.
Return strictly a JSON array of brand names, for example:
["BrandA", "BrandB", "BrandC"]
Do not include any extra commentary.
"""
        return Task(
            description=description,
            expected_output='["BrandA", "BrandB"]',
            agent=self.brand_discovery_agent()
        )

    @task
    def attribute_extraction_task(self) -> Task:
        description = r"""
For the brand "{brand}" and product type "{product_type}", extract product-specific attributes.
Return strictly as JSON in the format:
{
  "Color": ["Red", "Blue"],
  "Size": ["8", "9", "10"]
}
If no attributes are found, return {}.
"""
        return Task(
            description=description,
            expected_output='{"Color": [], "Size": []}',
            agent=self.attribute_extraction_agent()
        )

    @task
    def variation_generation_task(self) -> Task:
        description = r"""
For the brand "{brand}", generate a list of name variations or misspellings.
Return strictly a JSON array, for example:
["Variation1", "Variation2"]
Do not include any extra commentary.
"""
        return Task(
            description=description,
            expected_output='["Variation1", "Variation2"]',
            agent=self.brand_variation_agent()
        )

    # ------------------------------------------------------------
    # Crew Workflow: Dynamically construct tasks based on mode
    # ------------------------------------------------------------
    @crew
    def crew(self) -> Crew:
        """
        Build the Crew workflow based on the selected mode.
        
        - Category Mode:
            1) Run brand_discovery_task.
            2) (Later, for each discovered brand, attribute and variation tasks will be run.)
        
        - Brand Mode:
            1) Directly run attribute_extraction_task and variation_generation_task for the given brand.
        """
        mode = self.inputs.get("mode", "category").lower()
        tasks_list: List[Task] = []
        if mode == "category":
            tasks_list.append(self.brand_discovery_task())
        elif mode == "brand":
            tasks_list.append(self.attribute_extraction_task())
            tasks_list.append(self.variation_generation_task())
        else:
            raise ValueError("Invalid mode. Must be 'category' or 'brand'.")
        return Crew(
            agents=[
                self.brand_discovery_agent(),
                self.attribute_extraction_agent(),
                self.brand_variation_agent()
            ],
            tasks=tasks_list,
            process=Process.sequential,
            verbose=True
        )

    # ------------------------------------------------------------
    # After Kickoff: Update Neo4j Graph with discovered data
    # ------------------------------------------------------------
    @after_kickoff
    def update_graph(self, output: Dict[str, Any]):
        """
        After the crew tasks complete, parse their outputs and upsert into Neo4j.
        
        In Category Mode:
          - Parse the discovered brand list.
          - For each discovered brand, dynamically call the attribute extraction and variation agents,
            then upsert the results.
        
        In Brand Mode:
          - Parse attribute_extraction_task and variation_generation_task outputs and upsert.
        """
        mode = self.inputs.get("mode", "category").lower()
        updater = GraphUpdaterAgent(self.neo4j_driver)
        category = self.inputs.get("category", "")
        product_type = self.inputs.get("product_type", "")
        
        if mode == "category":
            try:
                # Parse output from brand_discovery_task
                discovered_brands = json.loads(output.get("brand_discovery_task", "[]"))
            except Exception as e:
                print(f"[update_graph] Error parsing discovered brands: {e}")
                discovered_brands = []
            # For each discovered brand, dynamically run attribute and variation extraction
            for brand in discovered_brands:
                attr_task = self.attribute_extraction_task()
                var_task = self.variation_generation_task()
                try:
                    attr_response = attr_task.agent.invoke(
                        prompt=attr_task.description.format(brand=brand, product_type=product_type)
                    )
                    attrs = json.loads(attr_response.strip())
                except Exception as e:
                    print(f"[update_graph] Attribute extraction failed for {brand}: {e}")
                    attrs = {}
                try:
                    var_response = var_task.agent.invoke(
                        prompt=var_task.description.format(brand=brand)
                    )
                    variations = json.loads(var_response.strip())
                except Exception as e:
                    print(f"[update_graph] Variation generation failed for {brand}: {e}")
                    variations = []
                updater.upsert_brand_info(brand, category, product_type, attrs, variations)
        elif mode == "brand":
            brand = self.inputs.get("brand", "")
            try:
                attrs = json.loads(output.get("attribute_extraction_task", "{}"))
            except Exception as e:
                print(f"[update_graph] Error parsing attributes for {brand}: {e}")
                attrs = {}
            try:
                variations = json.loads(output.get("variation_generation_task", "[]"))
            except Exception as e:
                print(f"[update_graph] Error parsing variations for {brand}: {e}")
                variations = []
            updater.upsert_brand_info(brand, category, product_type, attrs, variations)
        print("[After Kickoff] Neo4j graph update completed.")
        return output

    # Optionally, run this once at startup to set up indexes in Neo4j
    def setup_neo4j_indexes(self):
        with self.neo4j_driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS ON (b:Brand) ASSERT b.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS ON (c:Category) ASSERT c.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS ON (pt:ProductType) ASSERT pt.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS ON (a:Attribute) ASSERT a.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS ON (v:Value) ASSERT v.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS ON (v:Counterfeit) ASSERT v.name IS UNIQUE")
        print("[Setup] Neo4j indexes and constraints are set up.")

# ------------------------------------------------------------
# GraphUpdaterAgent: Upsert data into Neo4j
# ------------------------------------------------------------
class GraphUpdaterAgent:
    def __init__(self, driver):
        self.driver = driver

    def upsert_brand_info(self, brand: str, category: str, product_type: str, attributes: dict, variations: list):
        with self.driver.session() as session:
            # Upsert Brand and link to Category
            session.run(
                "MERGE (b:Brand {name:$brand}) "
                "MERGE (c:Category {name:$category}) "
                "MERGE (b)-[:BELONGS_TO]->(c)",
                {"brand": brand, "category": category}
            )
            # Upsert ProductType and link to Brand, if provided
            if product_type:
                session.run(
                    "MERGE (pt:ProductType {name:$pt}) "
                    "MERGE (b:Brand {name:$brand}) "
                    "MERGE (b)-[:HAS_PRODUCT_TYPE]->(pt)",
                    {"pt": product_type, "brand": brand}
                )
            # Upsert Attributes and their Values
            for attr, values in attributes.items():
                for val in values:
                    session.run(
                        "MERGE (a:Attribute {name:$attr}) "
                        "MERGE (v:Value {name:$val}) "
                        "MERGE (b:Brand {name:$brand})-[:HAS_ATTRIBUTE]->(a) "
                        "MERGE (a)-[:HAS_VALUE]->(v)",
                        {"attr": attr, "val": val, "brand": brand}
                    )
            # Upsert Variations as Counterfeit nodes
            for var in variations:
                session.run(
                    "MERGE (v:Counterfeit {name:$var}) "
                    "MERGE (b:Brand {name:$brand})-[:HAS_VARIATION]->(v)",
                    {"var": var, "brand": brand}
                )
        print(f"[GraphUpdaterAgent] Upserted data for brand: {brand}")
