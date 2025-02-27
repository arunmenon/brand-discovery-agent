"""
Multi-Modal LLM Client for Counterfeit Detection
"""

import base64
import time
import json
from openai import OpenAI
from config.config import OPENAI_API_KEY


class MultiModalResponse:
    """Structured response from multi-modal LLM"""
    def __init__(self, 
                 brands=None, 
                 similarity_score=None,
                 visual_issues=None,
                 text_issues=None,
                 differences=None,
                 is_authentic=None,
                 confidence=None,
                 **kwargs):
        self.brands = brands or []
        self.similarity_score = similarity_score
        self.visual_issues = visual_issues or []
        self.text_issues = text_issues or []
        self.differences = differences or []
        self.is_authentic = is_authentic
        self.confidence = confidence or 0.0


class MultiModalLLM:
    def __init__(self, model="gpt-4o"):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model
        
    def encode_image(self, image_path):
        """Convert image to base64 encoding"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
            
    def generate(self, prompt):
        """Generate response from multi-modal prompt"""
        # Prepare message content
        content = []
        
        # Add text component
        if "text" in prompt:
            content.append({"type": "text", "text": prompt["text"]})
        
        # Add image components
        if "images" in prompt:
            for img_path in prompt["images"]:
                base64_image = self.encode_image(img_path)
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                })
        
        # Make API call
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You analyze product images and text to detect counterfeit indicators. Respond with structured JSON."},
                {"role": "user", "content": content}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse and return result
        return MultiModalResponse(**json.loads(response.choices[0].message.content))
    
    def batch_generate(self, prompts, max_batch_size=5):
        """Process multiple prompts in batches to optimize API calls"""
        results = []
        
        # Process in smaller batches to avoid token limits
        for i in range(0, len(prompts), max_batch_size):
            batch = prompts[i:i+max_batch_size]
            batch_results = []
            
            # Create message content for each prompt in batch
            messages = []
            for prompt in batch:
                content = []
                if "text" in prompt:
                    content.append({"type": "text", "text": prompt["text"]})
                
                if "images" in prompt:
                    for img_path in prompt["images"]:
                        base64_image = self.encode_image(img_path)
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        })
                
                messages.append({"role": "user", "content": content})
            
            # Make batch API call with all prompts
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You analyze product images and text to detect counterfeit indicators. Process each item separately and respond with a JSON array of results."}
                ] + messages,
                response_format={"type": "json_object"}
            )
            
            # Parse responses (assuming JSON array returned)
            response_data = json.loads(response.choices[0].message.content)
            
            # Convert each item to a MultiModalResponse
            for item in response_data.get("results", []):
                batch_results.append(MultiModalResponse(**item))
            
            # Add batch results to overall results
            results.extend(batch_results)
            
            # Rate limit protection between batches
            if i + max_batch_size < len(prompts):
                time.sleep(0.5)
        
        return results
    
    def extract_brands(self, text_prompt):
        """Text-only brand extraction for initial grouping"""
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use faster model for text-only
            messages=[
                {"role": "system", "content": "Extract brand names from product listings. Respond with JSON."},
                {"role": "user", "content": text_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content).get("listings", [])