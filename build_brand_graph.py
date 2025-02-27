"""
Script to build a comprehensive brand graph in Neo4j
"""
import json
import time
from openai import OpenAI
from neo4j import GraphDatabase
from config.config import OPENAI_API_KEY, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Fashion categories and product types to process
CATEGORIES = [
    {"category": "Footwear", "product_types": ["Athletic Shoes", "Dress Shoes", "Boots"]},
    {"category": "Apparel", "product_types": ["Jeans", "T-Shirts", "Dresses"]},
    {"category": "Accessories", "product_types": ["Luxury Watches", "Handbags", "Sunglasses"]},
    {"category": "Luxury", "product_types": ["Designer Handbags", "High-end Footwear"]}
]

def discover_brands(category, product_type, num_brands=15):
    """Discover brands for a category and product type."""
    prompt = f"""
    You are a brand discovery agent specialized in fashion and retail intelligence. 
    
    Your task is to identify ALL well-known brands for the category "{category}" and product type "{product_type}".
    
    Return a JSON array of {num_brands} brand names, focusing on the most recognizable global brands.
    Include a comprehensive mix of:
    - Luxury/high-end brands (e.g., Gucci, Louis Vuitton)
    - Mid-range brands (e.g., Nike, Levi's)
    - Affordable/mass-market brands (e.g., H&M, Zara)
    
    Format your response as a valid JSON array of strings only.
    Example: ["Brand1", "Brand2", "Brand3"]
    """
    
    try:
        print(f"Discovering brands for {category} - {product_type}...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        
        result = response.choices[0].message.content.strip()
        try:
            brands = json.loads(result)
            return brands
        except json.JSONDecodeError:
            if '[' in result and ']' in result:
                json_part = result[result.find('['):result.rfind(']')+1]
                try:
                    return json.loads(json_part)
                except:
                    pass
            print(f"Error parsing brands: {result}")
            return []
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        return []

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

def generate_variations(brand, num_variations=15):
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

def generate_cypher_examples():
    """Generate Cypher queries for exploring the graph."""
    return [
        {
            "description": "Find all brands in a category",
            "query": "MATCH (b:Brand)-[:BELONGS_TO]->(c:Category {name: 'Luxury'}) RETURN b.name ORDER BY b.name"
        },
        {
            "description": "Find all counterfeit variations for a brand",
            "query": "MATCH (b:Brand {name: 'Rolex'})-[:HAS_VARIATION]->(v:Variation) RETURN v.name"
        },
        {
            "description": "Get all attributes and values for a brand",
            "query": "MATCH (b:Brand {name: 'Nike'})-[:HAS_ATTRIBUTE]->(a:Attribute)-[:HAS_VALUE]->(v:Value) RETURN a.name, collect(v.name)"
        },
        {
            "description": "Find brands by product type",
            "query": "MATCH (b:Brand)-[:IS_TYPE]->(p:ProductType {name: 'Athletic Shoes'}) RETURN b.name"
        },
        {
            "description": "Find brands with a specific attribute value",
            "query": "MATCH (b:Brand)-[:HAS_ATTRIBUTE]->(a:Attribute)-[:HAS_VALUE]->(v:Value) WHERE a.name = 'Material' AND v.name = 'Leather' RETURN b.name"
        }
    ]

def main():
    """Main function to build the brand graph."""
    # Get initial stats
    print("Getting initial graph statistics...")
    initial_stats = get_graph_stats()
    print(f"Initial graph contains: {initial_stats}")
    
    # Process each category and product type
    for category_info in CATEGORIES:
        category = category_info["category"]
        for product_type in category_info["product_types"]:
            # Discover brands
            brands = discover_brands(category, product_type)
            print(f"Discovered {len(brands)} brands for {category} - {product_type}: {', '.join(brands)}")
            
            # Process brands
            for brand in brands:
                attributes = extract_attributes(brand, product_type)
                variations = generate_variations(brand)
                
                # Store in Neo4j
                upsert_brand_info(brand, category, product_type, attributes, variations)
                
                # Small delay to avoid API rate limits
                time.sleep(0.5)
    
    # Get final stats
    print("\nGetting final graph statistics...")
    final_stats = get_graph_stats()
    print(f"Final graph contains: {final_stats}")
    print(f"Added {final_stats['brands'] - initial_stats['brands']} new brands")
    print(f"Added {final_stats['variations'] - initial_stats['variations']} new counterfeit variations")
    
    # Generate Cypher queries
    print("\nCypher queries for exploring the graph:")
    for example in generate_cypher_examples():
        print(f"\n{example['description']}:")
        print(f"{example['query']}")
    
    # Close Neo4j connection
    driver.close()
    print("\nBrand graph generation complete!")

if __name__ == "__main__":
    main()