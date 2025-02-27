"""
Test script to simulate CrewAI agent outputs without dependencies
"""
import json
import os
from openai import OpenAI
from config.config import OPENAI_API_KEY

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def simulate_brand_discovery(category, product_type):
    """Simulate the brand discovery agent using OpenAI directly."""
    prompt = f"""
    You are a brand discovery agent. Your task is to identify the most well-known brands 
    for the category "{category}" and product type "{product_type}".
    
    Return a JSON array of 5-10 brand names only, focusing on the most recognizable brands.
    Include a mix of luxury, mid-range, and affordable brands.
    
    Format your response as a valid JSON array of strings, for example:
    ["Brand1", "Brand2", "Brand3"]
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=500
        )
        
        result = response.choices[0].message.content.strip()
        # Try to parse JSON from the response
        try:
            brands = json.loads(result)
            return brands
        except json.JSONDecodeError:
            # If not valid JSON, try to extract from text
            print(f"Could not parse JSON directly. Raw response: {result}")
            # Simple extraction if response contains brackets
            if '[' in result and ']' in result:
                json_part = result[result.find('['):result.rfind(']')+1]
                try:
                    return json.loads(json_part)
                except:
                    pass
            return ["Error: Could not parse brands from response"]
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        return ["Error: API call failed"]

def simulate_attribute_extraction(brand, product_type):
    """Simulate the attribute extraction agent using OpenAI directly."""
    prompt = f"""
    You are an attribute extraction agent. For the brand "{brand}" and product type "{product_type}",
    identify the key attributes and their possible values.
    
    Return the result as a JSON object where keys are attribute names and values are arrays of possible values.
    
    For example:
    {{
        "Color": ["Red", "Blue", "Black"],
        "Size": ["Small", "Medium", "Large"],
        "Material": ["Leather", "Canvas", "Synthetic"]
    }}
    
    Focus on 3-6 of the most important attributes for this brand and product type.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=800
        )
        
        result = response.choices[0].message.content.strip()
        # Try to parse JSON from the response
        try:
            attributes = json.loads(result)
            return attributes
        except json.JSONDecodeError:
            # If not valid JSON, try to extract from text
            print(f"Could not parse JSON directly. Raw response: {result}")
            # Simple extraction if response contains braces
            if '{' in result and '}' in result:
                json_part = result[result.find('{'):result.rfind('}')+1]
                try:
                    return json.loads(json_part)
                except:
                    pass
            return {"Error": ["Could not parse attributes from response"]}
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        return {"Error": ["API call failed"]}

def simulate_variation_generation(brand):
    """Simulate the brand variation agent using OpenAI directly."""
    prompt = f"""
    You are a brand variation generation agent. For the brand "{brand}", generate variations that
    might be used for counterfeit products or trademark infringement.
    
    These might include:
    - Misspellings (like "Nikee" for "Nike")
    - Similar sounding names (like "Adides" for "Adidas")
    - Character substitutions (like "G00gle" for "Google")
    - Similar visual appearance names
    
    Return a JSON array of 5-8 plausible variations.
    
    Format your response as a valid JSON array of strings, for example:
    ["Variation1", "Variation2", "Variation3"]
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        
        result = response.choices[0].message.content.strip()
        # Try to parse JSON from the response
        try:
            variations = json.loads(result)
            return variations
        except json.JSONDecodeError:
            # If not valid JSON, try to extract from text
            print(f"Could not parse JSON directly. Raw response: {result}")
            # Simple extraction if response contains brackets
            if '[' in result and ']' in result:
                json_part = result[result.find('['):result.rfind(']')+1]
                try:
                    return json.loads(json_part)
                except:
                    pass
            return ["Error: Could not parse variations from response"]
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        return ["Error: API call failed"]

def test_category_mode(category, product_type):
    """Test the full category mode workflow."""
    print(f"\n===== TESTING CATEGORY MODE: {category} - {product_type} =====\n")
    
    # Step 1: Brand Discovery
    print(f"Discovering brands for {category} - {product_type}...")
    brands = simulate_brand_discovery(category, product_type)
    print(f"Discovered {len(brands)} brands: {', '.join(brands)}\n")
    
    # Process sample of brands
    sample_brands = brands[:3]  # Process first 3 brands only
    
    # Step 2 & 3: Process each brand
    for brand in sample_brands:
        print(f"Processing brand: {brand}")
        
        # Step 2: Attribute Extraction
        print(f"Extracting attributes for {brand}...")
        attributes = simulate_attribute_extraction(brand, product_type)
        print("Attributes extracted:")
        for attr, values in attributes.items():
            print(f"  - {attr}: {', '.join(values)}")
        
        # Step 3: Variation Generation
        print(f"\nGenerating variations for {brand}...")
        variations = simulate_variation_generation(brand)
        print(f"Variations generated: {', '.join(variations)}\n")
        
        print("-" * 80)

def main():
    """Main test function."""
    # Test various fashion categories and product types
    test_category_mode("Footwear", "Athletic Shoes")
    test_category_mode("Apparel", "Jeans")
    test_category_mode("Accessories", "Luxury Watches")
    
if __name__ == "__main__":
    main()