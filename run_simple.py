from core.BrandGraphIngester import BrandGraphIngester

def test_neo4j_connection():
    """Test the connection to Neo4j."""
    ingester = BrandGraphIngester()
    
    # Create a test brand node
    brand_name = "TestBrand"
    category = "TestCategory"
    product_type = "TestProduct"
    attributes = {"Color": ["Red", "Blue"], "Size": ["Small", "Medium", "Large"]}
    variations = ["TestBrandX", "T3stBrand"]
    
    try:
        # Insert data
        ingester.upsert_brand_info(brand_name, category, product_type, attributes, variations)
        print(f"Successfully inserted test brand '{brand_name}' into Neo4j")
        
        # Query data
        with ingester.driver.session() as session:
            result = session.run(
                """
                MATCH (b:Brand {name: $name})-[:HAS_ATTRIBUTE]->(a:Attribute)
                RETURN b.name as brand, collect(a.name) as attributes
                """,
                name=brand_name
            )
            record = result.single()
            if record:
                print(f"Retrieved brand: {record['brand']}")
                print(f"Attributes: {record['attributes']}")
            else:
                print("Brand not found in database")
        
        return True
    except Exception as e:
        print(f"Error in Neo4j operations: {str(e)}")
        return False

if __name__ == "__main__":
    test_neo4j_connection()