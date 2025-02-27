from neo4j import GraphDatabase

def test_neo4j_connection():
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "rathum12"  # Your actual Neo4j password
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()["count"]
            print(f"Database node count: {count}")
            
            # Create a test node
            session.run("CREATE (n:TestNode {name: 'test_connection'}) RETURN n")
            print("Created a test node")
            
            # Verify it exists
            result = session.run("MATCH (n:TestNode) RETURN count(n) as count")
            count = result.single()["count"]
            print(f"Test node count: {count}")
            
            # Clean up
            session.run("MATCH (n:TestNode) DELETE n")
            print("Deleted test nodes")
            
        driver.close()
        print("Neo4j database is working properly!")
        return True
    except Exception as e:
        print(f"Error connecting to Neo4j: {str(e)}")
        return False

if __name__ == "__main__":
    test_neo4j_connection()