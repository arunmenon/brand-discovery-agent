import json

from crewai import Crew, Process
from core.tasks import product_type_discovery_task
from core.crew_definition import BrandGraphCrew
from core.graph_updater import BrandGraphIngester

def orchestrate_brand_graph_for_category(category: str):
    """
    1) Discover product types for the given category.
    2) For each product type, run the BrandGraphCrew in 'category' mode.
    """

    # Step A: Set up & run the product_type_discovery_task
    product_type_task = product_type_discovery_task()
    # We can directly invoke the agent, similar to how we do for attribute/variation tasks
    prompt_str = product_type_task.description.format(category=category)
    try:
        product_type_json = product_type_task.agent.invoke(prompt=prompt_str)
        product_types = json.loads(product_type_json.strip())  # e.g. ["Running Shoes", "Sandals"]
    except Exception as e:
        print(f"[Orchestrator] Error discovering product types for category='{category}': {e}")
        product_types = []

    if not product_types:
        print(f"[Orchestrator] No product types found for category={category}. Aborting.")
        return

    # Step B: Optionally set up indexes if not done at startup
    ingester = BrandGraphIngester()
    ingester.setup_indexes()

    # Step C: For each product type, run BrandGraphCrew in category mode
    for pt in product_types:
        input_data = {
            "mode": "category",
            "category": category,
            "product_type": pt
        }
        print(f"[Orchestrator] --- Processing Category={category} / ProductType={pt} ---")
        crew_instance = BrandGraphCrew()     # Instantiate a new pipeline
        result = crew_instance.crew().kickoff(inputs=input_data)
        print(f"[Orchestrator] Done processing {pt}. Pipeline output: {result}")

def main():
    # Example usage
    category = "Footwear"
    orchestrate_brand_graph_for_category(category)

if __name__ == "__main__":
    main()
