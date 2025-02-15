from crewai import Agent, LLM
from config.config import OPENAI_API_KEY  # example usage of API keys

# Initialize a shared LLM instance
llm_instance = LLM(model="openai/gpt-4", temperature=0.2, verbose=False)

def get_product_type_agent():
    return Agent(
        role="Product Type Discovery",
        goal=(
            "Given the category '{category}', provide a JSON array listing possible product types "
            "within that category. Return strictly JSON, e.g. [\"Running Shoes\", \"Sandals\"]. "
            "Do not include extra commentary."
        ),
        backstory="An expert at enumerating product types within a broader category.",
        llm=llm_instance,
        memory=False,
        verbose=True,
        cache=False
    )

def get_brand_discovery_agent():
    return Agent(
        role="Brand Discovery",
        goal=(
            "Given the category '{category}' and product type '{product_type}', "
            "search online for relevant brand names and list one brand per line. "
            "Return strictly a JSON array (no extra text)."
        ),
        backstory="An expert researcher in identifying brands from various online sources.",
        llm=llm_instance,
        memory=False,
        verbose=True,
        cache=False
    )

def get_attribute_extraction_agent():
    return Agent(
        role="Attribute Extractor",
        goal=(
            "For the brand '{brand}' and product type '{product_type}', extract product-specific attributes "
            "and possible values. Return strictly JSON in the format: "
            "{\"Color\": [\"Red\", \"Blue\"], \"Size\": [\"8\", \"9\", \"10\"]}."
        ),
        backstory="Skilled at scraping and summarizing product details from online sources.",
        llm=llm_instance,
        memory=False,
        verbose=True,
        cache=False
    )

def get_brand_variation_agent():
    return Agent(
        role="Brand Variation Generator",
        goal=(
            "Generate a list of alternative names, misspellings, or knock-off variations for the brand '{brand}'. "
            "Return strictly as a JSON array (e.g., [\"BrandX\", \"Br4ndX\"])."
        ),
        backstory="Expert at detecting subtle variations that might represent counterfeit or alias names.",
        llm=llm_instance,
        memory=False,
        verbose=True,
        cache=False
    )
