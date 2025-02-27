"""
Neo4j Graph Database Client for Brand Knowledge Graph
"""

from neo4j import GraphDatabase
from config.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

class BrandGraphClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        # Initialize caches
        self.variation_cache = self.load_variation_cache()
        
    def close(self):
        self.driver.close()
        
    def get_brand_data(self, brand):
        """Get comprehensive brand data including attributes and references"""
        with self.driver.session() as session:
            # Query for brand attributes
            result = session.run("""
                MATCH (b:Brand {name: $brand})-[:PRODUCES]->(p)-[:HAS_ATTRIBUTE]->(a)
                MATCH (a)-[:VALID_VALUE]->(v)
                RETURN p.name as product, 
                       collect({attribute: a.name, values: collect(v.value)}) as attributes
            """, brand=brand)
            
            attributes = {record["product"]: record["attributes"] for record in result}
            
            # Query for reference images
            result = session.run("""
                MATCH (b:Brand {name: $brand})-[:HAS_REFERENCE]->(r:ReferenceImage)
                RETURN r.path as image_path
            """, brand=brand)
            
            reference_images = [record["image_path"] for record in result]
            
            return {
                "name": brand,
                "attributes": attributes,
                "reference_images": reference_images,
                "variations": self.variation_cache.get(brand, [])
            }
    
    def get_brands_data(self, brands):
        """Get data for multiple brands in a single database operation"""
        with self.driver.session() as session:
            # Query for brand attributes in batch
            result = session.run("""
                UNWIND $brands AS brand
                MATCH (b:Brand {name: brand})-[:PRODUCES]->(p)-[:HAS_ATTRIBUTE]->(a)
                MATCH (a)-[:VALID_VALUE]->(v)
                RETURN brand,
                       p.name as product, 
                       collect({attribute: a.name, values: collect(v.value)}) as attributes
            """, brands=brands)
            
            # Organize results by brand
            brand_attributes = {}
            for record in result:
                brand = record["brand"]
                if brand not in brand_attributes:
                    brand_attributes[brand] = {}
                brand_attributes[brand][record["product"]] = record["attributes"]
            
            # Query for reference images in batch
            result = session.run("""
                UNWIND $brands AS brand
                MATCH (b:Brand {name: brand})-[:HAS_REFERENCE]->(r:ReferenceImage)
                RETURN brand, r.path as image_path
            """, brands=brands)
            
            # Organize reference images by brand
            brand_images = {}
            for record in result:
                brand = record["brand"]
                if brand not in brand_images:
                    brand_images[brand] = []
                brand_images[brand].append(record["image_path"])
            
            # Combine all data
            brand_data = {}
            for brand in brands:
                brand_data[brand] = {
                    "name": brand,
                    "attributes": brand_attributes.get(brand, {}),
                    "reference_images": brand_images.get(brand, []),
                    "variations": self.variation_cache.get(brand, [])
                }
            
            return brand_data
    
    def load_variation_cache(self):
        """Preload all brand variations to cache"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (b:Brand)<-[:VARIATION_OF]-(v:Variation)
                RETURN b.name as brand, collect(v.name) as variations
            """)
            return {record["brand"]: record["variations"] for record in result}