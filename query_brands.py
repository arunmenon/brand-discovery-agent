from core.BrandGraphIngester import BrandGraphIngester

def list_all_brands():
    """List all brands in the database."""
    ingester = BrandGraphIngester()
    
    try:
        with ingester.driver.session() as session:
            # Get all brands
            result = session.run(
                """
                MATCH (b:Brand)
                RETURN b.name as brand, b.added_date as date
                ORDER BY b.name
                """
            )
            brands = [record for record in result]
            
            if brands:
                print(f"Found {len(brands)} brands in the database:")
                for brand in brands:
                    print(f"- {brand['brand']} (added: {brand['date']})")
                
                # Get details for a sample brand
                if len(brands) > 0:
                    sample_brand = brands[0]['brand']
                    get_brand_details(sample_brand, ingester)
            else:
                print("No brands found in the database")
    except Exception as e:
        print(f"Error querying Neo4j: {str(e)}")

def get_brand_details(brand_name, ingester=None):
    """Get detailed information about a specific brand."""
    if ingester is None:
        ingester = BrandGraphIngester()
    
    try:
        with ingester.driver.session() as session:
            # Get brand attributes
            attr_result = session.run(
                """
                MATCH (b:Brand {name: $name})-[:HAS_ATTRIBUTE]->(a:Attribute)-[:HAS_VALUE]->(v:Value)
                RETURN a.name as attribute, collect(v.name) as values
                ORDER BY a.name
                """,
                name=brand_name
            )
            attributes = [record for record in attr_result]
            
            # Get brand variations
            var_result = session.run(
                """
                MATCH (b:Brand {name: $name})-[:HAS_VARIATION]->(v:Variation)
                RETURN v.name as variation
                """,
                name=brand_name
            )
            variations = [record['variation'] for record in var_result]
            
            # Get brand categories and product types
            cat_result = session.run(
                """
                MATCH (b:Brand {name: $name})-[:BELONGS_TO]->(c:Category)
                MATCH (b)-[:IS_TYPE]->(p:ProductType)
                RETURN c.name as category, p.name as product_type
                """,
                name=brand_name
            )
            category_info = [record for record in cat_result]
            
            # Print results
            print(f"\nDetailed information for brand: {brand_name}")
            
            if category_info:
                for info in category_info:
                    print(f"Category: {info['category']}, Product Type: {info['product_type']}")
            else:
                print("No category information found")
                
            if attributes:
                print("\nAttributes:")
                for attr in attributes:
                    print(f"- {attr['attribute']}: {', '.join(attr['values'])}")
            else:
                print("No attributes found")
                
            if variations:
                print("\nVariations/Counterfeits:")
                for var in variations:
                    print(f"- {var}")
            else:
                print("No variations found")
    except Exception as e:
        print(f"Error getting brand details: {str(e)}")

if __name__ == "__main__":
    list_all_brands()