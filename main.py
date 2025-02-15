from crew_definition import BrandGraphCrew

def main():
    # Example input for Category Mode
    input_data = {
        "mode": "category",
        "category": "Footwear",
        "product_type": "Running Shoes"
    }
    
    # Or for Brand Mode:
    # input_data = {
    #     "mode": "brand",
    #     "brand": "Nike",
    #     "category": "Footwear",
    #     "product_type": "Running Shoes"
    # }
    
    crew_instance = BrandGraphCrew()
    
    # Optionally, set up Neo4j indexes once at startup:
    from graph_updater import GraphUpdaterAgent
    updater = GraphUpdaterAgent()
    updater.setup_indexes()
    
    # Kick off the crew with inputs
    result = crew_instance.crew().kickoff(inputs=input_data)
    # The after_kickoff hook will update the graph.
    print("Final result:", result)

if __name__ == "__main__":
    main()
