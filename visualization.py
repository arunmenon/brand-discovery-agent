"""
Visualize the brand graph from Neo4j data
"""
import os
import json
import matplotlib.pyplot as plt
import networkx as nx
from neo4j import GraphDatabase
from config.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

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

def get_brands_by_category():
    """Get brands grouped by category."""
    with driver.session() as session:
        result = session.run("""
            MATCH (b:Brand)-[:BELONGS_TO]->(c:Category)
            RETURN c.name as category, collect(b.name) as brands
            ORDER BY c.name
        """)
        return {record["category"]: record["brands"] for record in result}

def get_counterfeit_variations_count():
    """Get the count of counterfeit variations for each brand."""
    with driver.session() as session:
        result = session.run("""
            MATCH (b:Brand)-[:HAS_VARIATION]->(v:Variation)
            RETURN b.name as brand, count(v) as count
            ORDER BY count DESC
            LIMIT 20
        """)
        return {record["brand"]: record["count"] for record in result}

def get_attribute_counts():
    """Get the count of attributes for each brand."""
    with driver.session() as session:
        result = session.run("""
            MATCH (b:Brand)-[:HAS_ATTRIBUTE]->(a:Attribute)
            RETURN b.name as brand, count(distinct a) as count
            ORDER BY count DESC
            LIMIT 20
        """)
        return {record["brand"]: record["count"] for record in result}

def get_specific_brand_network(brand_name):
    """Get a subgraph for a specific brand to visualize."""
    graph = nx.Graph()
    
    with driver.session() as session:
        # Get brand node
        graph.add_node(brand_name, type="Brand")
        
        # Get categories
        result = session.run("""
            MATCH (b:Brand {name: $brand})-[:BELONGS_TO]->(c:Category)
            RETURN c.name as category
        """, brand=brand_name)
        
        for record in result:
            category = record["category"]
            graph.add_node(category, type="Category")
            graph.add_edge(brand_name, category, type="BELONGS_TO")
        
        # Get product types
        result = session.run("""
            MATCH (b:Brand {name: $brand})-[:IS_TYPE]->(p:ProductType)
            RETURN p.name as product_type
        """, brand=brand_name)
        
        for record in result:
            product_type = record["product_type"]
            graph.add_node(product_type, type="ProductType")
            graph.add_edge(brand_name, product_type, type="IS_TYPE")
        
        # Get attributes (limit to top 5 for visualization)
        result = session.run("""
            MATCH (b:Brand {name: $brand})-[:HAS_ATTRIBUTE]->(a:Attribute)
            RETURN a.name as attribute
            LIMIT 5
        """, brand=brand_name)
        
        for record in result:
            attribute = record["attribute"]
            graph.add_node(attribute, type="Attribute")
            graph.add_edge(brand_name, attribute, type="HAS_ATTRIBUTE")
        
        # Get variations (limit to top 5 for visualization)
        result = session.run("""
            MATCH (b:Brand {name: $brand})-[:HAS_VARIATION]->(v:Variation)
            RETURN v.name as variation
            LIMIT 5
        """, brand=brand_name)
        
        for record in result:
            variation = record["variation"]
            graph.add_node(variation, type="Variation")
            graph.add_edge(brand_name, variation, type="HAS_VARIATION")
    
    return graph

def create_visualizations():
    """Create visualizations of the brand graph."""
    # Create output directory
    os.makedirs("visualizations", exist_ok=True)
    
    # Get graph statistics
    stats = get_graph_stats()
    
    # Create bar chart for graph stats
    keys = ["brands", "categories", "product_types", "attributes", "values", "variations"]
    values = [stats[key] for key in keys]
    
    plt.figure(figsize=(12, 6))
    plt.bar(keys, values, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
    plt.title("Neo4j Brand Graph Statistics")
    plt.ylabel("Count")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("visualizations/graph_stats.png")
    plt.close()
    
    # Create pie chart for brands by category
    brands_by_category = get_brands_by_category()
    
    plt.figure(figsize=(10, 8))
    plt.pie([len(brands) for brands in brands_by_category.values()], 
            labels=brands_by_category.keys(),
            autopct='%1.1f%%',
            startangle=90)
    plt.axis('equal')
    plt.title("Brands by Category")
    plt.tight_layout()
    plt.savefig("visualizations/brands_by_category.png")
    plt.close()
    
    # Create bar chart for counterfeit variations
    variations = get_counterfeit_variations_count()
    
    plt.figure(figsize=(14, 8))
    plt.bar(variations.keys(), variations.values(), color='#ff7f0e')
    plt.title("Top Brands by Number of Counterfeit Variations")
    plt.ylabel("Number of Variations")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig("visualizations/counterfeit_variations.png")
    plt.close()
    
    # Create bar chart for attribute counts
    attributes = get_attribute_counts()
    
    plt.figure(figsize=(14, 8))
    plt.bar(attributes.keys(), attributes.values(), color='#2ca02c')
    plt.title("Top Brands by Number of Attributes")
    plt.ylabel("Number of Attributes")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig("visualizations/attribute_counts.png")
    plt.close()
    
    # Create network visualization for a sample brand
    top_brands = list(variations.keys())[:5]
    
    for brand in top_brands:
        graph = get_specific_brand_network(brand)
        
        plt.figure(figsize=(14, 10))
        pos = nx.spring_layout(graph, seed=42)
        
        # Draw nodes with different colors based on type
        node_colors = {
            'Brand': '#1f77b4',
            'Category': '#ff7f0e', 
            'ProductType': '#2ca02c',
            'Attribute': '#d62728',
            'Variation': '#9467bd'
        }
        
        for node_type, color in node_colors.items():
            nx.draw_networkx_nodes(
                graph, 
                pos, 
                nodelist=[n for n, data in graph.nodes(data=True) if data.get('type') == node_type],
                node_color=color,
                node_size=300,
                label=node_type
            )
        
        nx.draw_networkx_edges(graph, pos)
        nx.draw_networkx_labels(graph, pos, font_size=8)
        
        plt.title(f"Network Graph for {brand}")
        plt.axis('off')
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"visualizations/network_{brand.replace(' ', '_')}.png")
        plt.close()
    
    # Export sample of the data as JSON for inspection
    with driver.session() as session:
        sample_brand = top_brands[0] if top_brands else "Nike"
        
        # Get complete brand data
        result = session.run("""
            MATCH (b:Brand {name: $brand})
            OPTIONAL MATCH (b)-[:BELONGS_TO]->(c:Category)
            OPTIONAL MATCH (b)-[:IS_TYPE]->(p:ProductType)
            OPTIONAL MATCH (b)-[:HAS_ATTRIBUTE]->(a:Attribute)-[:HAS_VALUE]->(v:Value)
            OPTIONAL MATCH (b)-[:HAS_VARIATION]->(var:Variation)
            WITH b, collect(distinct c.name) as categories, 
                 collect(distinct p.name) as product_types,
                 collect(distinct {attribute: a.name, value: v.name}) as attr_values,
                 collect(distinct var.name) as variations
            RETURN b.name as brand, categories, product_types, attr_values, variations
        """, brand=sample_brand)
        
        for record in result:
            # Group attributes by name
            attributes = {}
            for attr_value in record["attr_values"]:
                attr_name = attr_value["attribute"]
                value = attr_value["value"]
                if attr_name not in attributes:
                    attributes[attr_name] = []
                attributes[attr_name].append(value)
            
            brand_data = {
                "brand": record["brand"],
                "categories": record["categories"],
                "product_types": record["product_types"],
                "attributes": attributes,
                "variations": record["variations"]
            }
            
            with open("visualizations/sample_brand_data.json", "w") as f:
                json.dump(brand_data, f, indent=2)
    
    print("Visualizations created in the 'visualizations' directory")

def main():
    """Main function to create visualizations."""
    create_visualizations()
    driver.close()

if __name__ == "__main__":
    main()