from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

class GraphUpdaterAgent:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def upsert_brand_info(self, brand: str, category: str, product_type: str, attributes: dict, variations: list):
        with self.driver.session() as session:
            # Upsert Brand and link to Category
            session.run(
                "MERGE (b:Brand {name:$brand}) "
                "MERGE (c:Category {name:$category}) "
                "MERGE (b)-[:BELONGS_TO]->(c)",
                {"brand": brand, "category": category}
            )
            # Upsert ProductType and link to Brand, if provided
            if product_type:
                session.run(
                    "MERGE (pt:ProductType {name:$pt}) "
                    "MERGE (b:Brand {name:$brand}) "
                    "MERGE (b)-[:HAS_PRODUCT_TYPE]->(pt)",
                    {"pt": product_type, "brand": brand}
                )
            # Upsert Attributes and their Values
            for attr, values in attributes.items():
                for val in values:
                    session.run(
                        "MERGE (a:Attribute {name:$attr}) "
                        "MERGE (v:Value {name:$val}) "
                        "MERGE (b:Brand {name:$brand})-[:HAS_ATTRIBUTE]->(a) "
                        "MERGE (a)-[:HAS_VALUE]->(v)",
                        {"attr": attr, "val": val, "brand": brand}
                    )
            # Upsert Variations as Counterfeit nodes
            for var in variations:
                session.run(
                    "MERGE (v:Counterfeit {name:$var}) "
                    "MERGE (b:Brand {name:$brand})-[:HAS_VARIATION]->(v)",
                    {"var": var, "brand": brand}
                )
        print(f"[GraphUpdaterAgent] Upserted data for brand: {brand}")

    def setup_indexes(self):
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS ON (b:Brand) ASSERT b.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS ON (c:Category) ASSERT c.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS ON (pt:ProductType) ASSERT pt.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS ON (a:Attribute) ASSERT a.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS ON (v:Value) ASSERT v.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS ON (v:Counterfeit) ASSERT v.name IS UNIQUE")
        print("[GraphUpdaterAgent] Indexes and constraints set up.")
