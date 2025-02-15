from crewai import Task
from agents import get_brand_discovery_agent, get_attribute_extraction_agent, get_brand_variation_agent

def brand_discovery_task():
    description = r"""
Given:
  Category: {category}
  Product Type: {product_type}

**INSTRUCTIONS**:
Search online for brand names relevant to these inputs.
Return strictly a JSON array of brand names, for example:
["BrandA", "BrandB", "BrandC"]
Do not include any extra commentary.
"""
    return Task(
        description=description,
        expected_output='["BrandA", "BrandB"]',
        agent=get_brand_discovery_agent()
    )

def attribute_extraction_task():
    description = r"""
For the brand "{brand}" and product type "{product_type}", extract product-specific attributes.
Return strictly as JSON in the format:
{
  "Color": ["Red", "Blue"],
  "Size": ["8", "9", "10"]
}
If no attributes are found, return {}.
"""
    return Task(
        description=description,
        expected_output='{"Color": [], "Size": []}',
        agent=get_attribute_extraction_agent()
    )

def variation_generation_task():
    description = r"""
For the brand "{brand}", generate a list of name variations or misspellings.
Return strictly a JSON array, for example:
["Variation1", "Variation2"]
Do not include any extra commentary.
"""
    return Task(
        description=description,
        expected_output='["Variation1", "Variation2"]',
        agent=get_brand_variation_agent()
    )
