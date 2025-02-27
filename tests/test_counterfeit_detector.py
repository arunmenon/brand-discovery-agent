"""
Tests for Counterfeit Detection System
"""

import unittest
import os
import json
import time
from counterfeit_detector.detector import CounterfeitDetector
from counterfeit_detector.batch_processor import BatchProcessor


class TestCounterfeitDetector(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Initialize components needed for all tests
        cls.detector = CounterfeitDetector()
        cls.batch_processor = BatchProcessor(batch_size=5, max_workers=3)
        
        # Set up test data directory
        cls.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        cls.test_images_dir = os.path.join(cls.test_data_dir, 'images')
        
        # Ensure test directories exist
        os.makedirs(cls.test_images_dir, exist_ok=True)
        
        # Create test listings
        cls.test_listings = cls._create_test_listings()
        
    @staticmethod
    def _create_test_listings():
        """Create a set of test listings with various counterfeit indicators"""
        return [
            # Likely authentic item
            {
                "id": "auth_1",
                "title": "Nike Air Max 270 - Original Box",
                "description": "Brand new Nike Air Max 270 shoes. Comes with original box and authentication card.",
                "price": 150.99,
                "seller": "official_nike_store",
                "seller_rating": 4.9,
                "images": ["nike_authentic_1.jpg", "nike_authentic_2.jpg"]
            },
            # Price too low - suspicious
            {
                "id": "fake_1",
                "title": "Nike Air Jordan - 80% Off Sale!!",
                "description": "Brand new Nike shoes at amazing discount prices. Limited time offer!",
                "price": 39.99,
                "seller": "discount_kicks",
                "seller_rating": 3.2,
                "images": ["fake_nike_1.jpg"]
            },
            # Misspelled brand name
            {
                "id": "fake_2",
                "title": "N1ke Air Jrdn Sneakers",
                "description": "Authentic sports shoes, newest design. Ships from overseas warehouse.",
                "price": 65.50,
                "seller": "best_shoes_discount",
                "seller_rating": 2.8,
                "images": ["fake_nike_2.jpg"]
            },
            # Rolex at suspicious price
            {
                "id": "fake_3",
                "title": "Rolex Datejust Automatic Watch",
                "description": "Luxury automatic watch, perfect replica of original design.",
                "price": 199.99,
                "seller": "luxury_watches_wholesale",
                "seller_rating": 3.1,
                "images": ["fake_rolex_1.jpg"]
            },
            # Likely authentic Rolex
            {
                "id": "auth_2",
                "title": "Rolex Submariner 116610LN",
                "description": "Authentic Rolex Submariner with box and papers. Purchased from authorized dealer.",
                "price": 12500.00,
                "seller": "certified_watch_dealer",
                "seller_rating": 4.8,
                "images": ["rolex_authentic_1.jpg", "rolex_authentic_2.jpg"]
            }
        ]
    
    def test_single_listing_analysis(self):
        """Test analyzing a single listing"""
        # Get a test listing (likely authentic)
        listing = next(l for l in self.test_listings if l["id"] == "auth_1")
        
        # Add full image paths
        listing["images"] = [os.path.join(self.test_images_dir, img) for img in listing["images"]]
        
        # Analyze listing
        result = self.detector.analyze_listing(listing)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertIn("score", result)
        self.assertIn("confidence", result)
        self.assertIn("indicators", result)
        
        # Authentic item should have low counterfeit score
        self.assertLess(result["score"], 30)
        
    def test_counterfeit_listing_analysis(self):
        """Test analyzing a likely counterfeit listing"""
        # Get a test listing (likely counterfeit)
        listing = next(l for l in self.test_listings if l["id"] == "fake_1")
        
        # Add full image paths
        listing["images"] = [os.path.join(self.test_images_dir, img) for img in listing["images"]]
        
        # Analyze listing
        result = self.detector.analyze_listing(listing)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertGreater(result["score"], 60)  # High counterfeit score
        self.assertGreater(len(result["indicators"]), 0)  # Should have indicators
        
    def test_batch_processing(self):
        """Test batch processing of multiple listings"""
        # Prepare test listings with full image paths
        test_batch = self.test_listings[:3]  # Use first 3 listings
        for listing in test_batch:
            listing["images"] = [os.path.join(self.test_images_dir, img) for img in listing["images"]]
        
        # Process batch
        start_time = time.time()
        batch_results = self.batch_processor.process_batch(test_batch)
        end_time = time.time()
        
        # Assertions
        self.assertEqual(len(batch_results), len(test_batch))
        self.assertIsInstance(batch_results, list)
        
        # All results should have required fields
        for result in batch_results:
            self.assertIn("score", result)
            self.assertIn("confidence", result)
            self.assertIn("indicators", result)
        
        # Check timing - batch should be faster than sequential
        batch_time = end_time - start_time
        
        # Process sequentially for comparison
        start_time = time.time()
        sequential_results = []
        for listing in test_batch:
            sequential_results.append(self.detector.analyze_listing(listing))
        end_time = time.time()
        sequential_time = end_time - start_time
        
        # Batch should be faster (allow some overhead for first run)
        if sequential_time > 1.0:  # Only compare if meaningful time elapsed
            self.assertLess(batch_time / sequential_time, 0.8)  # At least 20% faster
            
        print(f"Batch processing time: {batch_time:.2f}s, Sequential: {sequential_time:.2f}s")
    
    def test_large_dataset_processing(self):
        """Test processing a larger dataset in chunks"""
        # Create a larger dataset by duplicating test listings
        large_dataset = []
        for i in range(3):  # Create 15 listings (3 × 5)
            for listing in self.test_listings:
                # Create a copy with unique ID
                listing_copy = listing.copy()
                listing_copy["id"] = f"{listing['id']}_{i}"
                listing_copy["images"] = [os.path.join(self.test_images_dir, img) for img in listing["images"]]
                large_dataset.append(listing_copy)
        
        # Process large dataset
        results = self.batch_processor.process_large_dataset(large_dataset)
        
        # Assertions
        self.assertEqual(len(results), len(large_dataset))
        
        # Count high risk items
        high_risk = sum(1 for r in results if r["score"] > 60)
        
        # We should have identified the counterfeit items
        self.assertGreater(high_risk, 0)
        print(f"Processed {len(results)} listings, identified {high_risk} high-risk items")
    
    def test_image_processing(self):
        """Test image processing capabilities"""
        # Get a test listing with images
        listing = next(l for l in self.test_listings if l["id"] == "fake_2")
        listing["images"] = [os.path.join(self.test_images_dir, img) for img in listing["images"]]
        
        # Test image-based analysis
        result = self.detector.analyze_listing(listing)
        
        # Should include visual indicators
        visual_indicators = [i for i in result["indicators"] if "visual" in i.lower() or "logo" in i.lower() or "image" in i.lower()]
        self.assertGreater(len(visual_indicators), 0)


if __name__ == "__main__":
    unittest.main()