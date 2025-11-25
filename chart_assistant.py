import asyncio
import os
import time
import base64
import io
from config import Config
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes

SYSTEM_PROMPT = """You are a chart analysis expert. 
    Analyze charts and provide:
    1. Chart type
    2. Key data points
    3. Trends and insights
    4. Concise summary"""
class ChartsAssistant: 
    def __init__(self):
        Config.validate_env_variables()
        self.openai_client = Config.get_openai_client()
        self.vision_client = Config.get_vision_client()

    
    async def analyze_chart(self, files):
        """Computer Vision OCR + GPT-4 Vision to analyze chart images and extract structured data."""
        """Computer Vision OCR + GPT-4 Vision to analyze chart images and extract structured data."""
        image_bytes_dict = {}
        base64_images_dict = {}
        all_text_results = []
        
        for filename, image_data in files:
            if isinstance(image_data, bytes):
                image_bytes_dict[filename] = image_data
                base64_images_dict[filename] = base64.b64encode(image_data).decode('utf-8')
            else:
                # Already base64
                image_bytes_dict[filename] = base64.b64decode(image_data)
                base64_images_dict[filename] = image_data
                

        # Read operation for OCR from file
        print("Extracting text with OCR...")

        async def process_single_file(filename, image_bytes):
                """Process a single file with OCR"""
                try:
                    print(f"Processing {filename}...")
                    image_stream = io.BytesIO(image_bytes)
                    image_stream.seek(0)
                    
                    read_result = self.vision_client.read_in_stream(image_stream, raw=True)
                    operation_id = read_result.headers["Operation-Location"].split("/")[-1]
                    
                    print(f"Operation ID for {filename}: {operation_id}")
                    
                    result = await self._poll_for_result(operation_id)
                    
                    if result is None:
                        print(f"Failed to get result for {filename}")
                        return (filename, "")
                    
                    extracted = extract_text(result)
                    print(f"Extracted text from {filename}: {len(extracted)} characters")
                    
                    return (filename, extracted)
                    
                except Exception as e:
                    print(f"Error processing {filename}")
                    return (filename, "")

        def extract_text(result):
            """Extract text from OCR result"""
            if result is None:
                return 
            analyze_result = result.get('analyze_result') if isinstance(result, dict) else result.analyze_result
            file_text_items = []
            if analyze_result and hasattr(analyze_result, 'read_results'):
                for page in analyze_result.read_results:
                    for line in page.lines:
                        file_text_items.append({
                            'text': line.text,
                            'bbox': line.bounding_box
                        })
            extracted_text = "\n".join([item['text'] for item in file_text_items])
            return extracted_text
        
        # Process in parallel
        tasks = [process_single_file(fn, data) for fn, data in files[:5]]
        all_text_results = await asyncio.gather(*tasks)

      
        print("Analyzing with GPT-4 Vision...")
        
        ocr_summary = "\n\n".join([f"**{filename}:**\n{text}" for filename, text in all_text_results])



        user_prompt = [
                {
                    "type": "text",
                    "text": f"""Analyze these charts:

            OCR Data:
            {ocr_summary[:500]}

            Return structured analysis."""
                }
            ]
        
        for filename in all_text_results:
            user_prompt.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_images_dict[filename[0]]}"
                }
            })
            
        response = self.openai_client.chat.completions.create(
            model=os.getenv("OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt      
                }
            ],
            max_tokens=2500,
            response_format={"type": "json_object"}, 
            temperature=0.3  
        )
        
        return response.choices[0].message.content

    async def _poll_for_result(self, operation_id, max_attempts=30, poll_interval=1):
        """Poll for Read operation result"""
        print("   Polling for results...", end="", flush=True)
        
        for attempt in range(max_attempts):
            try:
                # Use the vision client created in __init__ to get the read result
                result = self.vision_client.get_read_result(operation_id)

                if result.status == OperationStatusCodes.succeeded:
                    print(" ✓ Succeeded")
                    return result
                elif result.status == OperationStatusCodes.failed:
                    print(" ✗ Failed")
                    return None
                
                print(".", end="", flush=True)
                await asyncio.sleep(poll_interval)
            except Exception as e:
                print(f" ✗ Error polling")
                return None
        
        print(" ✗ Timeout")
        return None

    def followup_response(self, question, previous_analysis):
        """Generate follow-up response based on previous analysis."""
        response = self.openai_client.chat.completions.create(
            model=os.getenv("OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"""Based on the previous chart analysis below, answer the following question:

                    Previous Analysis:
                    {previous_analysis}

                    Question:
                    {question}"""
                }
            ],
            max_tokens=1500
        )
        
        return response.choices[0].message.content