"""
Build a mini version of the brand graph with just two brands as an example
"""
import json
from openai import OpenAI
from neo4j import GraphDatabase
from config.config import OPENAI_API_KEY, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Test brands to process
TEST_BRANDS = [
    {"brand": "Nike", "category": "Footwear", "product_type": "Athletic Shoes"},
    {"brand": "Rolex", "category": "Accessories", "product_type": "Luxury Watches"}
]

def extract_attributes(brand, product_type):
    """Extract attributes for a brand and product type."""
    prompt = f"""
    You are an attribute extraction specialist for fashion brands.
    
    For the brand "{brand}" and product type "{product_type}", identify ALL key attributes and their possible values.
    Be extremely comprehensive and specific to this exact brand and product type.
    
    Return the result as a JSON object where keys are attribute names and values are arrays of possible values.
    
    For example:
    {{
        "Color": ["Red", "Blue", "Black"],
        "Size": ["Small", "Medium", "Large"],
        "Material": ["Leather", "Canvas", "Synthetic"]
    }}
    
    Include at least 5-8 attributes that are most relevant to this specific brand and product.
    """
    
    try:
        print(f"Extracting attributes for {brand} - {product_type}...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1000
        )
        
        result = response.choices[0].message.content.strip()
        try:
            attributes = json.loads(result)
            return attributes
        except json.JSONDecodeError:
            if '{' in result and '}' in result:
                json_part = result[result.find('{'):result.rfind('}')+1]
                try:
                    return json.loads(json_part)
                except:
                    pass
            print(f"Error parsing attributes: {result}")
            return {}
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        return {}

def generate_variations(brand, num_variations=10):
    """Generate brand variations that might be used for counterfeits."""
    prompt = f"""
    You are a counterfeit brand detection specialist.
    
    For the brand "{brand}", generate a COMPREHENSIVE list of {num_variations} different counterfeit name variations.
    
    Include a wide variety of tactics counterfeiters use:
    - Misspellings (like "Nikee" for "Nike")
    - Similar sounding names (like "Adides" for "Adidas")
    - Character substitutions (like "G00gle" for "Google")
    - Similar visual appearance names
    - Letter rearrangements
    - Adding/removing characters
    - Typographical variations
    
    Return ONLY a JSON array of strings.
    Example: ["Variation1", "Variation2", "Variation3"]
    
    Make each variation plausible - something that could actually appear on a counterfeit product.
    """
    
    try:
        print(f"Generating variations for {brand}...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=1000
        )
        
        result = response.choices[0].message.content.strip()
        try:
            variations = json.loads(result)
            return variations
        except json.JSONDecodeError:
            if '[' in result and ']' in result:
                json_part = result[result.find('['):result.rfind(']')+1]
                try:
                    return json.loads(json_part)
                except:
                    pass
            print(f"Error parsing variations: {result}")
            return []
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        return []

def upsert_brand_info(brand, category, product_type, attributes, variations):
    """Store brand information in Neo4j."""
    with driver.session() as session:
        # Create brand with timestamps
        session.run("""
            MERGE (b:Brand {name: $brand})
            ON CREATE SET b.created_at = datetime(), b.updated_at = datetime()
            ON MATCH SET b.updated_at = datetime()
        """, brand=brand)
        
        # Create category and relationship
        session.run("""
            MERGE (c:Category {name: $category})
            WITH c
            MATCH (b:Brand {name: $brand})
            MERGE (b)-[:BELONGS_TO]->(c)
        """, brand=brand, category=category)
        
        # Create product type and relationship
        session.run("""
            MERGE (p:ProductType {name: $product_type})
            WITH p
            MATCH (b:Brand {name: $brand})
            MERGE (b)-[:IS_TYPE]->(p)
        """, brand=brand, product_type=product_type)
        
        # Create attributes and values
        for attr_name, values in attributes.items():
            for value in values:
                session.run("""
                    MATCH (b:Brand {name: $brand})
                    MERGE (a:Attribute {name: $attr_name})
                    MERGE (v:Value {name: $value})
                    MERGE (b)-[:HAS_ATTRIBUTE]->(a)
                    MERGE (a)-[:HAS_VALUE]->(v)
                """, brand=brand, attr_name=attr_name, value=value)
        
        # Create variations
        for variation in variations:
            session.run("""
                MATCH (b:Brand {name: $brand})
                MERGE (v:Variation {name: $variation})
                MERGE (b)-[:HAS_VARIATION]->(v)
            """, brand=brand, variation=variation)
        
        print(f"Successfully stored {brand} in Neo4j with {len(attributes)} attributes and {len(variations)} variations")

def get_graph_stats():
    """Get statistics about the graph."""
    with driver.session() as session:
        brands = session.run("MATCH (b:Brand) RETURN count(b) as count").single()["count"]
        categories = session.run("MATCH (c:Category) RETURN count(c) as count").single()["count"]
        product_types = session.run("MATCH (p:ProductType) RETURN count(p) as count").single()["count"]
        attributes = session.run("MATCH (a:Attribute) RETURN count(a) as count").single()["count"]
        values = session.run("MATCH (v:Value) RETURN count(v) as count").single()["count"]
        variations = session.run("MATCH (v:Variation) RETURN count(v) as count").single()["count"]
        
        return {
            "brands": brands,
            "categories": categories,
            "product_types": product_types,
            "attributes": attributes,
            "values": values, 
            "variations": variations
        }

def main():
    """Main function to build a mini brand graph."""
    # Get initial stats
    print("Getting initial graph statistics...")
    initial_stats = get_graph_stats()
    print(f"Initial graph contains: {initial_stats}")
    
    # Process each test brand
    for brand_info in TEST_BRANDS:
        brand = brand_info["brand"]
        category = brand_info["category"]
        product_type = brand_info["product_type"]
        
        # Get attributes and variations
        attributes = extract_attributes(brand, product_type)
        variations = generate_variations(brand)
        
        # Store in Neo4j
        upsert_brand_info(brand, category, product_type, attributes, variations)
    
    # Get final stats
    print("\nGetting final graph statistics...")
    final_stats = get_graph_stats()
    print(f"Final graph contains: {final_stats}")
    print(f"Added {final_stats['brands'] - initial_stats['brands']} new brands")
    print(f"Added {final_stats['variations'] - initial_stats['variations']} new counterfeit variations")
    
    # Close Neo4j connection
    driver.close()
    print("\nMini brand graph generation complete!")

if __name__ == "__main__":
    main()