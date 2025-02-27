"""
Batch Processor for Counterfeit Detection
"""

from .detector import CounterfeitDetector
from .multi_modal import MultiModalLLM
from .graph_client import BrandGraphClient
from concurrent.futures import ThreadPoolExecutor
import time

class BatchProcessor:
    def __init__(self, batch_size=50, max_workers=10):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.detector = CounterfeitDetector()
        self.multimodal_llm = MultiModalLLM()
        self.graph_client = BrandGraphClient()
        
    def process_large_dataset(self, listings):
        """Process large dataset by splitting into batches"""
        results = []
        total = len(listings)
        
        # Split dataset into batches
        for i in range(0, total, self.batch_size):
            batch = listings[i:min(i+self.batch_size, total)]
            print(f"Processing batch {i//self.batch_size + 1}/{(total+self.batch_size-1)//self.batch_size}")
            
            # Process batch and extend results
            batch_results = self.process_batch(batch)
            results.extend(batch_results)
            
            # Add delay between batches to avoid rate limiting
            if i + self.batch_size < total:
                time.sleep(1)
                
        return results
    
    def process_batch(self, listings):
        """Process a batch of listings with optimized flows"""
        # Group listings by brand to reduce graph queries
        brand_groups = self._group_by_brand(listings)
        
        # Pre-fetch all brand data from graph in one operation
        brand_data = self._prefetch_brand_data(brand_groups.keys())
        
        # Process listings in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Map each listing to a future
            futures = []
            for brand, items in brand_groups.items():
                for listing in items:
                    # Pass pre-fetched brand data to avoid redundant queries
                    futures.append(
                        executor.submit(
                            self._process_single_listing, 
                            listing, 
                            brand_data.get(listing['detected_brand'], {})
                        )
                    )
            
            # Collect results as they complete
            results = []
            for future in futures:
                results.append(future.result())
                
        return results
    
    def _group_by_brand(self, listings):
        """Group listings by detected brand - requires initial brand detection"""
        # First, run initial brand detection on all listings
        brand_groups = {}
        
        # Optimize by batching the brand detection step
        brand_detection_results = self._batch_brand_detection(listings)
        
        # Group by detected brand
        for i, listing in enumerate(listings):
            # Add detected brand to listing
            listing['detected_brand'] = brand_detection_results[i]['primary_brand']
            listing['all_detected_brands'] = brand_detection_results[i]['all_brands']
            
            # Group by primary brand
            brand = listing['detected_brand']
            if brand not in brand_groups:
                brand_groups[brand] = []
            brand_groups[brand].append(listing)
            
        return brand_groups
    
    def _batch_brand_detection(self, listings):
        """Run brand detection on batches of listings"""
        # Optimize LLM calls by doing text-only brand detection first
        text_batches = []
        current_batch = ""
        batch_indices = []
        current_indices = []
        
        # Group listings into text batches
        for i, listing in enumerate(listings):
            text = f"Listing {i}: {listing.get('title', '')} {listing.get('description', '')}\n"
            if len(current_batch) + len(text) < 15000:  # Token limit safety
                current_batch += text
                current_indices.append(i)
            else:
                text_batches.append(current_batch)
                batch_indices.append(current_indices)
                current_batch = text
                current_indices = [i]
        
        # Add final batch
        if current_batch:
            text_batches.append(current_batch)
            batch_indices.append(current_indices)
        
        # Process text batches for brand detection
        brand_results = [None] * len(listings)
        for batch_text, indices in zip(text_batches, batch_indices):
            prompt = f"Extract brand names from each listing. Output JSON array with primary_brand and all_brands for each listing:\n{batch_text}"
            
            # Send to text-only LLM for brand extraction
            batch_brands = self.detector.multimodal_llm.extract_brands(prompt)
            
            # Assign results to correct indices
            for list_idx, result_idx in enumerate(indices):
                if list_idx < len(batch_brands):
                    brand_results[result_idx] = batch_brands[list_idx]
        
        return brand_results
    
    def _prefetch_brand_data(self, brands):
        """Prefetch data for all brands in one operation"""
        return self.graph_client.get_brands_data(list(brands))
    
    def _process_single_listing(self, listing, brand_data):
        """Process a single listing with prefetched brand data"""
        # Use detector but skip redundant operations
        result = self.detector.analyze_with_context(listing, brand_data)
        return result