"""
Benchmark Performance of Counterfeit Detection System
"""

import time
import csv
import random
from counterfeit_detector.detector import CounterfeitDetector
from counterfeit_detector.batch_processor import BatchProcessor


def generate_sample_data(num_samples=100):
    """Generate sample data for benchmarking"""
    brands = ["Nike", "Adidas", "Rolex", "Louis Vuitton", "Gucci", "Prada"]
    product_types = ["Shoes", "Watches", "Bags", "Clothing", "Accessories"]
    
    listings = []
    for i in range(num_samples):
        # Randomly select brand and product
        brand = random.choice(brands)
        product = random.choice(product_types)
        
        # Create listing with varying characteristics
        price_multiplier = random.uniform(0.3, 1.5)  # Some will be suspiciously low
        
        # Occasionally misspell brand (for counterfeits)
        if random.random() < 0.3:
            brand_name = brand.replace('i', '1').replace('o', '0') if random.random() < 0.5 else brand
        else:
            brand_name = brand
            
        listing = {
            "id": f"test_{i}",
            "title": f"{brand_name} {product} - {'New' if random.random() < 0.7 else 'Used'}",
            "description": f"{'Authentic' if random.random() < 0.8 else 'High Quality'} {brand} {product}. "
                         f"{'Ships from official store' if random.random() < 0.7 else 'International shipping'}.",
            "price": round(100 * price_multiplier, 2),
            "seller": f"seller_{i % 20}",  # 20 different sellers
            "seller_rating": round(random.uniform(2.5, 5.0), 1),
            # In real scenario would include images
            "images": []
        }
        listings.append(listing)
        
    return listings


def run_benchmark(batch_sizes=[1, 5, 10, 25, 50]):
    """Run benchmark with different batch sizes"""
    # Generate test data
    test_data = generate_sample_data(100)
    
    # Results to record
    results = []
    
    # Initialize detector for single processing
    detector = CounterfeitDetector()
    
    # Benchmark single processing first
    start_time = time.time()
    single_results = []
    for listing in test_data[:10]:  # Use first 10 for single processing test
        single_results.append(detector.analyze_listing(listing))
    single_time = time.time() - start_time
    single_time_per_item = single_time / 10
    
    results.append({
        "method": "Single Processing",
        "batch_size": 1,
        "items_processed": 10,
        "total_time": single_time,
        "time_per_item": single_time_per_item,
        "speedup": 1.0  # baseline
    })
    
    # Benchmark batch processing with different batch sizes
    for batch_size in batch_sizes:
        if batch_size == 1:
            continue  # Skip, we already tested single processing
            
        processor = BatchProcessor(batch_size=batch_size, max_workers=min(batch_size, 10))
        
        # Measure time for processing
        start_time = time.time()
        batch_results = processor.process_large_dataset(test_data)
        batch_time = time.time() - start_time
        
        # Calculate metrics
        items_processed = len(test_data)
        time_per_item = batch_time / items_processed
        speedup = single_time_per_item / time_per_item
        
        results.append({
            "method": f"Batch Processing",
            "batch_size": batch_size,
            "items_processed": items_processed,
            "total_time": batch_time,
            "time_per_item": time_per_item,
            "speedup": speedup
        })
        
        print(f"Batch size {batch_size}: {batch_time:.2f}s total, {time_per_item:.4f}s per item, {speedup:.2f}x speedup")
    
    # Write results to CSV
    with open('benchmark_results.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    return results


if __name__ == "__main__":
    print("Running counterfeit detection benchmarks...")
    results = run_benchmark()
    
    # Print summary
    print("\nBenchmark Results:")
    print("-" * 80)
    print(f"{'Method':<20} {'Batch Size':<12} {'Items':<8} {'Total Time':<12} {'Per Item':<12} {'Speedup':<8}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['method']:<20} {r['batch_size']:<12} {r['items_processed']:<8} "
              f"{r['total_time']:.2f}s{'':<6} {r['time_per_item']:.4f}s{'':<4} {r['speedup']:.2f}x")