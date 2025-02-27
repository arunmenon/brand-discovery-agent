"""
Counterfeit Detection System
"""

from .multi_modal import MultiModalLLM
from .graph_client import BrandGraphClient

class CounterfeitDetector:
    def __init__(self):
        self.multimodal_llm = MultiModalLLM()
        self.graph_client = BrandGraphClient()
        
    def analyze_listing(self, listing):
        """Analyze a product listing using multi-modal approach"""
        # Step 1: Multi-modal analysis of listing
        multimodal_analysis = self.analyze_listing_multimodal(listing)
        
        # Step 2: Query graph database for brand information
        brand_data = {}
        for brand in multimodal_analysis["detected_brands"]:
            brand_data[brand] = self.graph_client.get_brand_data(brand)
        
        # Step 3: Compare with reference images if available
        visual_comparison = {}
        if listing.get("images") and brand_data:
            primary_brand = multimodal_analysis["detected_brands"][0]
            if brand_data[primary_brand].get("reference_images"):
                visual_comparison = self.compare_with_reference(
                    listing["images"][0], 
                    brand_data[primary_brand]["reference_images"]
                )
        
        # Step 4: Calculate final score
        indicators = []
        indicators.extend(multimodal_analysis["visual_indicators"])
        indicators.extend(multimodal_analysis["text_indicators"])
        
        if visual_comparison.get("visual_differences"):
            indicators.extend(visual_comparison["visual_differences"])
        
        # Calculate weighted score
        score = self.calculate_score(indicators, multimodal_analysis["confidence"])
        
        return {
            "score": score,
            "confidence": multimodal_analysis["confidence"],
            "indicators": indicators,
            "authentication_result": visual_comparison.get("authentication_result", None)
        }
    
    def analyze_listing_multimodal(self, listing):
        """Analyze listing with multi-modal LLM"""
        prompt = {
            "text": f"Analyze this product listing for counterfeit indicators: {listing.get('title', '')} {listing.get('description', '')}",
            "images": listing.get("images", [])[:4]  # Limit to first 4 images
        }
        
        response = self.multimodal_llm.generate(prompt)
        
        return {
            "detected_brands": response.brands,
            "visual_indicators": response.visual_issues,
            "text_indicators": response.text_issues,
            "confidence": response.confidence
        }
    
    def compare_with_reference(self, listing_image, reference_images):
        """Compare listing image with reference images"""
        prompt = {
            "text": "Compare the product image with these authentic reference images. Identify any visual differences that suggest counterfeiting.",
            "images": [listing_image] + reference_images[:3]
        }
        
        analysis = self.multimodal_llm.generate(prompt)
        return {
            "match_score": analysis.similarity_score,
            "visual_differences": analysis.differences,
            "authentication_result": analysis.is_authentic
        }
    
    def calculate_score(self, indicators, confidence):
        """Calculate counterfeit risk score"""
        # Basic implementation - each indicator adds points
        # More sophisticated scoring would weight by indicator type
        base_score = len(indicators) * 10
        return min(100, base_score * confidence)
    
    def analyze_batch(self, listings):
        """Process multiple listings in batch"""
        results = []
        for listing in listings:
            results.append(self.analyze_listing(listing))
        return results
    
    def analyze_with_context(self, listing, brand_data):
        """Analyze listing with pre-fetched brand data"""
        # Skip brand detection since it was done in batch
        
        # Multi-modal analysis with brand context
        prompt = {
            "text": f"Analyze this product listing for counterfeit indicators of {listing['detected_brand']}: {listing.get('title', '')} {listing.get('description', '')}",
            "images": listing.get("images", [])[:4]
        }
        
        response = self.multimodal_llm.generate(prompt)
        
        # Visual comparison with prefetched reference images
        visual_comparison = {}
        if listing.get("images") and brand_data.get("reference_images"):
            visual_comparison = self.compare_with_reference(
                listing["images"][0], 
                brand_data["reference_images"]
            )
        
        # Calculate results using prefetched data
        indicators = []
        indicators.extend(response.visual_issues)
        indicators.extend(response.text_issues)
        
        if visual_comparison.get("visual_differences"):
            indicators.extend(visual_comparison["visual_differences"])
        
        score = self.calculate_score(indicators, response.confidence)
        
        return {
            "score": score,
            "confidence": response.confidence,
            "indicators": indicators,
            "authentication_result": visual_comparison.get("authentication_result", None)
        }