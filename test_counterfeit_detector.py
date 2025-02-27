"""
Test the counterfeit detector with various examples
"""
from counterfeit_detector import analyze_catalog_items

def main():
    """Run tests with various catalog items"""
    
    # Test examples - mix of legitimate and counterfeit items
    test_items = [
        # Legitimate items
        {
            "title": "Nike Air Max 270 Running Shoes",
            "short_description": "Premium Nike athletic footwear with Air cushioning technology",
            "long_description": "Authentic Nike Air Max 270 shoes featuring revolutionary Air Max cushioning. Mesh upper provides breathability while the rubber outsole offers superior traction. These shoes come with original Nike packaging and warranty."
        },
        {
            "title": "Rolex Submariner Date Watch 126610LN",
            "short_description": "Luxury Rolex diving watch with date function",
            "long_description": "The Rolex Submariner Date in Oystersteel with a black Cerachrom bezel and black dial. Water-resistant to 300 meters (1,000 feet), this professional diver's watch features a unidirectional rotatable bezel and solid-link Oyster bracelet with Oysterlock safety clasp."
        },
        
        # Counterfeit items - obvious name variations
        {
            "title": "Nikey Air Max Sport Shoes - Best Price!",
            "short_description": "Quality sports shoes with air cushion technology",
            "long_description": "Get the look and feel of premium shoes at a fraction of the cost. Our Nikey AirMax shoes have all the features you'd expect from expensive brands. Comfortable air pockets in sole. Many colors available. These shoes are inspired by the popular design but at a much more affordable price."
        },
        {
            "title": "R0lex Submarriner Luxury Watch - 75% OFF!",
            "short_description": "Luxury diving watch - looks just like the expensive brand",
            "long_description": "This premium R0lex Submarriner watch has all the features of watches costing thousands more. Water resistant design, rotating bezel, and stainless steel construction. Our watches use high-quality materials at a fraction of the cost. Makes a perfect gift!"
        },
        
        # Counterfeit items - subtle indicators
        {
            "title": "Nike Running Shoes - Factory Direct",
            "short_description": "Authentic style Nike athletic footwear at 80% off retail",
            "long_description": "These Nike running shoes come direct from the factory with no middleman markup. Features air technology and premium materials. Note: These are A-grade Nike style shoes that may not include original packaging or brand tags. All sales are final."
        },
        {
            "title": "Limited Edition Rolex Yacht-Master Blue Special",
            "short_description": "Exclusive blue dial Rolex Yacht-Master",
            "long_description": "This rare Rolex Yacht-Master features a special blue dial not commonly found. Unique opportunity to own this hard-to-find model at a special price. Watch comes with box only, no papers. Perfect replica of original Rolex quality. Ships from overseas warehouse."
        },
        
        # Non-counterfeit but similar to known brands
        {
            "title": "Athletic Pro Air Cushion Running Shoes",
            "short_description": "Professional running shoes with air cushion technology",
            "long_description": "Athletic Pro shoes feature our proprietary air cushion technology for maximum comfort during long runs. These high-performance athletic shoes include breathable mesh upper and durable rubber outsole. Not affiliated with any major brand."
        },
        
        # Completely unrelated to known brands
        {
            "title": "GardenMaster 5000 Hedge Trimmer",
            "short_description": "Electric hedge trimmer with extended reach",
            "long_description": "The GardenMaster 5000 hedge trimmer features a powerful motor and ergonomic design. Perfect for maintaining your garden with minimal effort. Includes safety lock and 2-year warranty."
        }
    ]
    
    # Run analysis
    print("Analyzing catalog items for counterfeit indicators...\n")
    results = analyze_catalog_items(test_items)
    
    # Print results summary
    print("\n===== SUMMARY OF RESULTS =====")
    print(f"Total items analyzed: {len(results)}")
    
    high_risk = sum(1 for r in results if "risk_level" in r and r["risk_level"] == "HIGH")
    medium_risk = sum(1 for r in results if "risk_level" in r and r["risk_level"] == "MEDIUM")
    low_risk = sum(1 for r in results if "risk_level" in r and r["risk_level"] == "LOW")
    no_risk = sum(1 for r in results if "risk_level" in r and r["risk_level"] == "NONE")
    errors = sum(1 for r in results if "error" in r)
    
    print(f"HIGH risk items: {high_risk}")
    print(f"MEDIUM risk items: {medium_risk}")
    print(f"LOW risk items: {low_risk}")
    print(f"NO risk items: {no_risk}")
    print(f"Errors: {errors}")
    
    # Print detailed results
    for i, result in enumerate(results):
        print(f"\n--- Analysis for Item {i+1}: {result['item']['title']} ---")
        if "error" in result:
            print(f"Error: {result['error']}")
            continue
            
        print(f"Counterfeit Score: {result.get('counterfeit_score', 0):.2f}")
        print(f"Risk Level: {result.get('risk_level', 'UNKNOWN')}")
        print(f"Is Likely Counterfeit: {result.get('is_likely_counterfeit', False)}")
        print(f"Highest Risk Brand: {result.get('highest_risk_brand', 'None')}")
        
        print("\nDetected Brand Candidates:")
        for candidate in result.get('brand_candidates', []):
            print(f"- {candidate['brand_name']} (confidence: {candidate['detection_confidence']:.2f})")
            
            if candidate.get('counterfeit_indicators', []):
                print("  Counterfeit Indicators:")
                for indicator in candidate['counterfeit_indicators']:
                    print(f"  - {indicator['indicator_type']}: {indicator['description']} (confidence: {indicator['confidence']:.2f})")
        
        print("-" * 80)

if __name__ == "__main__":
    main()