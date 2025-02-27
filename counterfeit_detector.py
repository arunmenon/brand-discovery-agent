"""
Counterfeit detector for catalog item listings

This script analyzes new catalog items and detects potential counterfeit items 
by checking against the brand graph database.

Flow:
1. Item comes in with title, short description, long description
2. Extract potential brand mentions with confidence scores
3. Query brand graph for each candidate brand
4. Check if item matches known counterfeit patterns
5. Generate a counterfeit confidence score
6. Return detailed analysis
"""
import json
import re
from typing import Dict, List, Any, Tuple
from openai import OpenAI
from neo4j import GraphDatabase
from config.config import OPENAI_API_KEY, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

class CounterfeitDetector:
    """Main class for detecting counterfeit listings in catalog."""
    
    def __init__(self):
        """Initialize the detector with OpenAI and Neo4j connections."""
        self.openai_client = client
        self.neo4j_driver = driver
        
    def analyze_catalog_item(self, item: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyze a catalog item for potential counterfeits.
        
        Args:
            item: Dictionary with 'title', 'short_description', and 'long_description'
            
        Returns:
            Dict with analysis results including counterfeit confidence
        """
        # Step 1: Extract potential brand mentions with confidence
        brand_candidates = self._extract_brand_candidates(item)
        
        # Step 2: For each candidate, check against the brand graph
        enriched_candidates = []
        for candidate in brand_candidates:
            brand_name = candidate["brand_name"]
            confidence = candidate["confidence"]
            
            # Get brand context from the graph
            brand_context = self._get_brand_context(brand_name)
            
            # Check for counterfeit indicators
            counterfeit_indicators = self._check_counterfeit_indicators(
                item, brand_name, brand_context
            )
            
            # Create enriched candidate
            enriched_candidates.append({
                "brand_name": brand_name,
                "detection_confidence": confidence,
                "brand_context": brand_context,
                "counterfeit_indicators": counterfeit_indicators,
                "is_counterfeit": len(counterfeit_indicators) > 0,
                "counterfeit_confidence": self._calculate_counterfeit_confidence(
                    confidence, counterfeit_indicators
                )
            })
        
        # Step 3: Generate final analysis
        counterfeit_score = max([c["counterfeit_confidence"] for c in enriched_candidates], default=0)
        highest_risk_brand = next(
            (c["brand_name"] for c in enriched_candidates 
             if c["counterfeit_confidence"] == counterfeit_score), 
            None
        )
        
        return {
            "item": item,
            "brand_candidates": enriched_candidates,
            "counterfeit_score": counterfeit_score,
            "highest_risk_brand": highest_risk_brand,
            "is_likely_counterfeit": counterfeit_score > 0.7,
            "risk_level": self._get_risk_level(counterfeit_score),
            "analysis_timestamp": self._get_timestamp()
        }
    
    def _extract_brand_candidates(self, item: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extract potential brand mentions from catalog item.
        
        Returns list of dicts with brand_name and confidence score.
        """
        # Combine item text
        combined_text = f"{item.get('title', '')} {item.get('short_description', '')} {item.get('long_description', '')}"
        
        # Use LLM to extract brand candidates with confidence
        prompt = f"""
        You are a brand detection specialist analyzing a potential product listing.
        Extract all brand names mentioned in the following text, with a confidence score (0-1) 
        of how certain you are that this is a brand mention.
        
        Product Listing:
        Title: {item.get('title', '')}
        Short Description: {item.get('short_description', '')}
        Long Description: {item.get('long_description', '')}
        
        For each brand you detect, consider:
        1. Is this a well-known brand name?
        2. Is it formatted like a brand (capitalization, trademark symbols)?
        3. Is it in a position in the text where a brand would typically appear?
        4. Is it followed by product type words?
        
        Return a JSON array of objects with 'brand_name' and 'confidence':
        [
          {{"brand_name": "Nike", "confidence": 0.95}},
          {{"brand_name": "NB Shoes", "confidence": 0.65}}
        ]
        
        Only include actual potential brands, not generic terms.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # Extract JSON if surrounded by markdown or text
                if '[' in result and ']' in result:
                    json_part = result[result.find('['):result.rfind(']')+1]
                    try:
                        return json.loads(json_part)
                    except:
                        pass
                print(f"Error parsing brand candidates: {result}")
                return []
        except Exception as e:
            print(f"Error extracting brand candidates: {str(e)}")
            return []
    
    def _get_brand_context(self, brand_name: str) -> Dict[str, Any]:
        """
        Get brand context from Neo4j.
        
        Includes legitimate variations, attributes, etc.
        """
        with self.neo4j_driver.session() as session:
            # First, try exact match
            exact_match = self._query_exact_brand(session, brand_name)
            if exact_match:
                return exact_match
                
            # If no exact match, try fuzzy match
            fuzzy_matches = self._query_fuzzy_brand(session, brand_name)
            if fuzzy_matches:
                # Return the closest match
                return fuzzy_matches[0]
                
            # If still no match, check counterfeit variations
            variation_matches = self._query_brand_variations(session, brand_name)
            if variation_matches:
                return {
                    "brand": variation_matches[0]["original_brand"],
                    "is_variation": True,
                    "variation_type": "counterfeit",
                    "attributes": variation_matches[0]["attributes"],
                    "legitimate_variations": [],
                    "counterfeit_variations": [brand_name]
                }
            
            # No matches found
            return {
                "brand": brand_name,
                "exists_in_graph": False,
                "attributes": {},
                "legitimate_variations": [],
                "counterfeit_variations": []
            }
    
    def _query_exact_brand(self, session, brand_name: str) -> Dict[str, Any]:
        """Query for exact brand name match in Neo4j."""
        result = session.run("""
            MATCH (b:Brand {name: $brand})
            OPTIONAL MATCH (b)-[:HAS_ATTRIBUTE]->(a:Attribute)-[:HAS_VALUE]->(v:Value)
            OPTIONAL MATCH (b)-[:HAS_VARIATION]->(var:Variation)
            WITH b, 
                collect(distinct {name: a.name, value: v.name}) as attr_values,
                collect(distinct var.name) as variations
            RETURN b.name as brand, 
                   attr_values,
                   variations
        """, brand=brand_name)
        
        record = result.single()
        if not record:
            return None
            
        # Convert attribute values to dictionary
        attributes = {}
        for attr in record["attr_values"]:
            name = attr["name"]
            value = attr["value"]
            if name not in attributes:
                attributes[name] = []
            attributes[name].append(value)
        
        return {
            "brand": record["brand"],
            "exists_in_graph": True,
            "attributes": attributes,
            "legitimate_variations": [],
            "counterfeit_variations": record["variations"]
        }
    
    def _query_fuzzy_brand(self, session, brand_name: str) -> List[Dict[str, Any]]:
        """Query for fuzzy brand name match in Neo4j."""
        # Neo4j doesn't have great fuzzy matching, so we'll get all brands
        # and do a simple string similarity check
        result = session.run("""
            MATCH (b:Brand)
            RETURN b.name as brand
        """)
        
        brands = [record["brand"] for record in result]
        
        # Simple string similarity - could be improved
        matches = []
        for brand in brands:
            similarity = self._calculate_similarity(brand_name.lower(), brand.lower())
            if similarity > 0.7:  # Threshold for similarity
                matches.append((brand, similarity))
        
        # Sort by similarity score
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Get full context for top matches
        result = []
        for brand, score in matches[:3]:  # Top 3 matches
            context = self._query_exact_brand(session, brand)
            if context:
                context["similarity_score"] = score
                result.append(context)
                
        return result
    
    def _query_brand_variations(self, session, potential_variation: str) -> List[Dict[str, Any]]:
        """Check if the name matches any known counterfeit variations."""
        result = session.run("""
            MATCH (b:Brand)-[:HAS_VARIATION]->(v:Variation {name: $variation})
            OPTIONAL MATCH (b)-[:HAS_ATTRIBUTE]->(a:Attribute)-[:HAS_VALUE]->(val:Value)
            WITH b, 
                collect(distinct {name: a.name, value: val.name}) as attr_values
            RETURN b.name as original_brand, 
                   attr_values
        """, variation=potential_variation)
        
        records = []
        for record in result:
            # Convert attribute values to dictionary
            attributes = {}
            for attr in record["attr_values"]:
                name = attr["name"]
                value = attr["value"]
                if name not in attributes:
                    attributes[name] = []
                attributes[name].append(value)
                
            records.append({
                "original_brand": record["original_brand"],
                "attributes": attributes
            })
            
        return records
    
    def _check_counterfeit_indicators(
        self, 
        item: Dict[str, str], 
        brand_name: str, 
        brand_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Check for counterfeit indicators in the listing.
        
        Compare item against brand context from database.
        Returns list of indicator objects with type and confidence.
        """
        combined_text = f"{item.get('title', '')} {item.get('short_description', '')} {item.get('long_description', '')}"
        
        # Create context string for the LLM
        brand_attributes = ""
        if brand_context.get("attributes"):
            for attr_name, values in brand_context.get("attributes", {}).items():
                brand_attributes += f"- {attr_name}: {', '.join(values)}\n"
        
        known_counterfeits = "\n".join(brand_context.get("counterfeit_variations", []))
        
        # Use LLM to analyze for counterfeit indicators
        prompt = f"""
        You are a counterfeit detection expert analyzing a product listing that mentions the brand "{brand_name}".
        
        Here is information about the legitimate brand from our database:
        Brand: {brand_context.get("brand", brand_name)}
        Exists in database: {brand_context.get("exists_in_graph", False)}
        Is a known counterfeit variation: {brand_context.get("is_variation", False)}
        
        Brand attributes:
        {brand_attributes if brand_attributes else "No attribute data available"}
        
        Known counterfeit variations:
        {known_counterfeits if known_counterfeits else "No known counterfeit variations"}
        
        Now analyze this product listing:
        Title: {item.get('title', '')}
        Short Description: {item.get('short_description', '')}
        Long Description: {item.get('long_description', '')}
        
        Identify SPECIFIC indicators that this listing might be for a counterfeit product. Include:
        1. Name variations: Does the brand name have subtle misspellings?
        2. Price indicators: Is the price suspiciously low (if mentioned)?
        3. Description red flags: Vague descriptions, poor grammar, etc.
        4. Attribute mismatches: Product attributes that don't match known brand attributes
        5. Known patterns: Matching known counterfeit patterns
        
        Return a JSON array of objects with 'indicator_type', 'description', and 'confidence' (0-1):
        [
          {{"indicator_type": "name_variation", "description": "Brand name 'Nikee' has extra 'e'", "confidence": 0.9}},
          {{"indicator_type": "attribute_mismatch", "description": "Claims 'leather upper' but Nike doesn't use leather for this model", "confidence": 0.75}}
        ]
        
        If no counterfeit indicators are found, return an empty array: []
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=800
            )
            
            result = response.choices[0].message.content.strip()
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # Extract JSON if surrounded by markdown or text
                if '[' in result and ']' in result:
                    json_part = result[result.find('['):result.rfind(']')+1]
                    try:
                        return json.loads(json_part)
                    except:
                        pass
                print(f"Error parsing counterfeit indicators: {result}")
                return []
        except Exception as e:
            print(f"Error checking counterfeit indicators: {str(e)}")
            return []
    
    def _calculate_counterfeit_confidence(
        self, 
        brand_confidence: float, 
        indicators: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall counterfeit confidence score."""
        if not indicators:
            return 0.0
            
        # Weighted average of indicator confidences
        total_weight = 0
        weighted_score = 0
        
        # Define weights for different indicator types
        weights = {
            "name_variation": 1.0,
            "attribute_mismatch": 0.8,
            "description_red_flag": 0.6,
            "price_indicator": 0.7,
            "known_pattern": 1.0
        }
        
        for indicator in indicators:
            indicator_type = indicator.get("indicator_type", "other")
            confidence = indicator.get("confidence", 0.5)
            weight = weights.get(indicator_type, 0.5)
            
            weighted_score += confidence * weight
            total_weight += weight
        
        # Average of indicators, weighted by indicator type
        indicator_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # Final score formula: combine brand confidence and indicator confidence
        # Brand confidence boosts the overall score
        return min(1.0, indicator_score * (0.5 + 0.5 * brand_confidence))
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity score between 0 and 1."""
        # Simple Levenshtein distance implementation
        if len(str1) == 0:
            return 0.0
        if len(str2) == 0:
            return 0.0
        
        # Create matrix
        matrix = [[0 for x in range(len(str2) + 1)] for x in range(len(str1) + 1)]
        
        # Initialize first row and column of matrix
        for i in range(len(str1) + 1):
            matrix[i][0] = i
        for j in range(len(str2) + 1):
            matrix[0][j] = j
        
        # Fill matrix
        for i in range(1, len(str1) + 1):
            for j in range(1, len(str2) + 1):
                if str1[i-1] == str2[j-1]:
                    matrix[i][j] = matrix[i-1][j-1]
                else:
                    matrix[i][j] = min(
                        matrix[i-1][j] + 1,    # deletion
                        matrix[i][j-1] + 1,    # insertion
                        matrix[i-1][j-1] + 1   # substitution
                    )
        
        # Max possible distance is the length of the longer string
        max_distance = max(len(str1), len(str2))
        actual_distance = matrix[len(str1)][len(str2)]
        
        # Convert to similarity (0-1)
        similarity = 1.0 - (actual_distance / max_distance)
        return similarity
    
    def _get_risk_level(self, score: float) -> str:
        """Convert numerical score to risk level."""
        if score >= 0.8:
            return "HIGH"
        elif score >= 0.5:
            return "MEDIUM"
        elif score > 0:
            return "LOW"
        else:
            return "NONE"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def close(self):
        """Close Neo4j connection."""
        self.neo4j_driver.close()

def analyze_catalog_items(items: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Analyze a batch of catalog items for counterfeits.
    
    Args:
        items: List of dictionaries with 'title', 'short_description', and 'long_description'
        
    Returns:
        List of analysis results
    """
    detector = CounterfeitDetector()
    results = []
    
    for item in items:
        try:
            result = detector.analyze_catalog_item(item)
            results.append(result)
        except Exception as e:
            print(f"Error analyzing item '{item.get('title')}': {str(e)}")
            results.append({
                "item": item,
                "error": str(e),
                "analysis_timestamp": detector._get_timestamp()
            })
    
    detector.close()
    return results

# Example usage
if __name__ == "__main__":
    # Example catalog items
    test_items = [
        {
            "title": "Nike Air Max Running Shoes",
            "short_description": "Premium athletic footwear with air cushioning technology",
            "long_description": "Authentic Nike Air Max shoes featuring revolutionary Air cushioning technology. Mesh upper provides breathability while the rubber outsole offers superior traction."
        },
        {
            "title": "Nikey AirMax Elite Sports Shoes",
            "short_description": "Quality sports shoes with air technology",
            "long_description": "Get the look and feel of premium shoes at a fraction of the cost. Our Nikey AirMax Elite shoes have all the features you'd expect from expensive brands. Comfortable air pockets in sole. Many colors available."
        },
        {
            "title": "Nik3 Airr Maks Running Trainers",
            "short_description": "Cheap running shoes for everyday use",
            "long_description": "Best and cheapest running shoes on the market. Similar to expensive brands but much better value. Our Nik3 Airr Maks trainers are perfect for any athlete or casual wearer. Free shipping on all orders."
        }
    ]
    
    # Analyze items
    results = analyze_catalog_items(test_items)
    
    # Print results
    for i, result in enumerate(results):
        print(f"\n--- Analysis for Item {i+1}: {result['item']['title']} ---")
        if "error" in result:
            print(f"Error: {result['error']}")
            continue
            
        print(f"Counterfeit Score: {result['counterfeit_score']:.2f}")
        print(f"Risk Level: {result['risk_level']}")
        print(f"Is Likely Counterfeit: {result['is_likely_counterfeit']}")
        print(f"Highest Risk Brand: {result['highest_risk_brand']}")
        
        print("\nDetected Brand Candidates:")
        for candidate in result['brand_candidates']:
            print(f"- {candidate['brand_name']} (confidence: {candidate['detection_confidence']:.2f})")
            
            if candidate['counterfeit_indicators']:
                print("  Counterfeit Indicators:")
                for indicator in candidate['counterfeit_indicators']:
                    print(f"  - {indicator['indicator_type']}: {indicator['description']} (confidence: {indicator['confidence']:.2f})")
        
        print("-" * 80)