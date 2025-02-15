from core.crew_definition import BrandGraphCrew
from core.graph_updater import BrandGraphIngester

def main():
    # Example input for Category Mode
    input_data = {
        "mode": "category",
        "category": "Footwear",
        "product_type": "Running Shoes"
    }
    
    # Alternatively, for Brand Mode:
    # input_data = {
    #     "mode": "brand",
    #     "brand": "Nike",
    #     "category": "Footwear",
    #     "product_type": "Running Shoes"
    # }
    
    crew_instance = BrandGraphCrew()
    
    # Set up indexes once at startup
    ingester = BrandGraphIngester()
    ingester.setup_indexes()
    
    result = crew_instance.crew().kickoff(inputs=input_data)
    print("Final result:", result)

if __name__ == "__main__":
    main()
