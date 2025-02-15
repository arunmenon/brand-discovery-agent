import json
from typing import Any, Dict, List
from crewai import Crew, Process
from crewai.project import CrewBase, before_kickoff, after_kickoff, crew
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from agents import get_brand_discovery_agent, get_attribute_extraction_agent, get_brand_variation_agent
from tasks import brand_discovery_task, attribute_extraction_task, variation_generation_task
from graph_updater import GraphUpdaterAgent

@CrewBase
class BrandGraphCrew:
    """
    Crew that builds/updates a Brand Knowledge Graph in Neo4j.
    
    Supports two modes:
      - Category Mode: Discovers brands given a category and product type, then extracts attributes
        and name variations for each discovered brand.
      - Brand Mode: Directly processes a given brand.
    """
    
    def __init__(self):
        self.inputs: Dict[str, Any] = {}
    
    @before_kickoff
    def capture_inputs(self, inputs: Dict[str, Any]):
        self.inputs = inputs
        return inputs

    @crew
    def crew(self) -> Crew:
        mode = self.inputs.get("mode", "category").lower()
        tasks_list: List[Any] = []
        if mode == "category":
            tasks_list.append(brand_discovery_task())
        elif mode == "brand":
            tasks_list.append(attribute_extraction_task())
            tasks_list.append(variation_generation_task())
        else:
            raise ValueError("Invalid mode. Must be 'category' or 'brand'.")
        return Crew(
            agents=[
                get_brand_discovery_agent(),
                get_attribute_extraction_agent(),
                get_brand_variation_agent()
            ],
            tasks=tasks_list,
            process=Process.sequential,
            verbose=True
        )

    @after_kickoff
    def update_graph(self, output: Dict[str, Any]):
        mode = self.inputs.get("mode", "category").lower()
        updater = GraphUpdaterAgent()
        category = self.inputs.get("category", "")
        product_type = self.inputs.get("product_type", "")
        
        if mode == "category":
            try:
                discovered_brands = json.loads(output.get("brand_discovery_task", "[]"))
            except Exception as e:
                print(f"[update_graph] Error parsing discovered brands: {e}")
                discovered_brands = []
            for brand in discovered_brands:
                attr_task = attribute_extraction_task()
                var_task = variation_generation_task()
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
        print("[after_kickoff] Neo4j graph update completed.")
        return output
