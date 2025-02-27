"""
Query counterfeit variations from Neo4j
"""
from neo4j import GraphDatabase
from config.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_variations():
    """Get all counterfeit variations."""
    with driver.session() as session:
        result = session.run("""
            MATCH (b:Brand)-[:HAS_VARIATION]->(v:Variation)
            RETURN b.name AS brand, collect(v.name) AS variations
            ORDER BY b.name
        """)
        
        print("Counterfeit Variations by Brand:")
        for record in result:
            brand = record["brand"]
            variations = record["variations"]
            print(f"\n{brand} ({len(variations)} variations):")
            for variation in variations:
                print(f"  - {variation}")

def get_brand_attributes(brand_name):
    """Get attributes for a specific brand."""
    with driver.session() as session:
        result = session.run("""
            MATCH (b:Brand {name: $brand})-[:HAS_ATTRIBUTE]->(a:Attribute)-[:HAS_VALUE]->(v:Value)
            RETURN a.name AS attribute, collect(v.name) AS values
            ORDER BY a.name
        """, brand=brand_name)
        
        print(f"\nAttributes for {brand_name}:")
        for record in result:
            attribute = record["attribute"]
            values = record["values"]
            print(f"\n{attribute}:")
            for value in values:
                print(f"  - {value}")

if __name__ == "__main__":
    get_variations()
    
    # Get attributes for a specific brand (Nike)
    get_brand_attributes("Nike")
    
    # Get attributes for a specific brand (Rolex)
    get_brand_attributes("Rolex")
    
    driver.close()